
import io
import wave
import audioop
import asyncio
import time


from app.audio.microphone import Microphone
from app.audio.speaker import Speaker
from app.audio.processor import AudioProcessorService
from app.vad.service import VADService
from app.debug.audio_debugger import AudioDebugger
from app.audio.frame_buffer import FrameBuffer
from app.conversation.utterance_detector import UtteranceDetector


class AudioEngine:

    def __init__(self, enable_local_audio: bool = False):

        self.enable_local_audio = enable_local_audio
        self.processor = AudioProcessorService()
        self.microphone = Microphone() if enable_local_audio else None
        self.speaker = Speaker() if enable_local_audio else None
        self.vad = VADService()
        self.debugger = AudioDebugger()

        if self.microphone is not None:
            self.microphone.start()

        self.frame_buffer = FrameBuffer()
        self.utterance_detector = UtteranceDetector()
        self.capture_task = None
        self.capture_callback = None
        self.capture_running = False

        self.sample_rate = 16000
        self.channels = 1
        self.sample_width = 2

        # -----------------------------------------
        # Playback state
        # -----------------------------------------

        self.is_playing = False
        self.stop_requested = False

        # Every TTS response gets a generation.
        # When playback is interrupted, generation increases.
        # Old chunks are then rejected.
        self.playback_generation = 0

        self.play_queue = asyncio.Queue()

        self.playback_buffer = bytearray()

        self.playback_task = None
        self.browser_audio_callback = None
        
        # -----------------------------------------
        # Latency timing (set by agent runtime)
        # -----------------------------------------
        
        self.turn_timing = None

    def set_browser_audio_callback(self, callback):
        self.browser_audio_callback = callback

    # -----------------------------------------
    # START
    # -----------------------------------------

    async def start(self):

        if self.playback_task is None:

            self.playback_task = asyncio.create_task(
                self.playback_worker()
            )

    # -----------------------------------------
    # PLAYBACK WORKER
    # -----------------------------------------

    async def playback_worker(self):

        print("🎵 Playback worker running")

        while True:

            frame = await self.play_queue.get()

            try:

                # None is ONLY shutdown.
                if frame is None:

                    print("🛑 Playback worker stopping")
                    return

                # Playback was interrupted.
                if self.stop_requested:

                    continue

                if self.speaker is None or self.speaker.stopped:

                    continue

                self.is_playing = True

                # Give exact frame to AEC reverse stream
                self.processor.process_speaker(frame)

                await asyncio.to_thread(
                    self.speaker.play,
                    frame
                )

            finally:

                self.play_queue.task_done()

                if self.play_queue.empty():

                    self.is_playing = False

    # -----------------------------------------
    # BEGIN NEW TTS RESPONSE
    # -----------------------------------------

    def begin_playback(self):
        speaker_state = "disabled" if self.speaker is None else self.speaker.stopped
        print(
            f"[AUDIO] begin_playback ENTER "
            f"stop_requested={self.stop_requested} "
            f"speaker.stopped={speaker_state}"
        )

        self.playback_generation += 1

        self.stop_requested = False
        self.is_playing = False

        self.playback_buffer.clear()

        if self.speaker is not None:
            self.speaker.resume()

        return self.playback_generation

    # -----------------------------------------
    # STREAMING TTS
    # -----------------------------------------

    async def play_frame(
        self,
        chunk,
        generation=None,
    ):

        # Record first playback frame time for latency
        if (self.turn_timing and 
            self.turn_timing.playback_first_frame is None):
            self.turn_timing.playback_first_frame = time.perf_counter()

        speaker_state = "disabled" if self.speaker is None else self.speaker.stopped
        print(f"[AUDIO] play_frame ENTER bytes={len(chunk)}")
        print(
            f"[AUDIO] play_frame STATE "
            f"stop_requested={self.stop_requested} "
            f"speaker.stopped={speaker_state} "
            f"browser_callback={'present' if self.browser_audio_callback else 'none'}"
        )

        # Reject chunks from an old TTS generation.
        if generation is not None:

            if generation != self.playback_generation:

                print("[AUDIO] play_frame RETURN reason=generation_mismatch")

                return

        # Never restart playback after interruption.
        if self.stop_requested:

            print("[AUDIO] play_frame RETURN reason=stop_requested")

            return

        if self.speaker is not None and self.speaker.stopped:

            print("[AUDIO] play_frame RETURN reason=speaker_stopped")

            return

        if self.browser_audio_callback:
            print(f"[AUDIO] browser callback START bytes={len(chunk)}")
            try:
                await self.browser_audio_callback(bytes(chunk))
            except Exception as exc:
                print(
                    f"[AUDIO] browser callback FAILED "
                    f"bytes={len(chunk)} error={exc}"
                )
                raise
            print(f"[AUDIO] browser callback COMPLETE bytes={len(chunk)}")
            return

        self.playback_buffer.extend(chunk)

        FRAME_BYTES = 320

        while len(self.playback_buffer) >= FRAME_BYTES:

            # Check again because stop() could have happened
            # while this coroutine was waiting.
            if self.stop_requested:

                self.playback_buffer.clear()

                return

            frame = bytes(
                self.playback_buffer[
                    :FRAME_BYTES
                ]
            )

            del self.playback_buffer[
                :FRAME_BYTES
            ]

            await self.play_queue.put(frame)

            if self.stop_requested:

                self.playback_buffer.clear()

                return

        self.is_playing = True

    async def start_capture(self, callback):
        if self.microphone is None:
            print("🎤 Local microphone capture disabled")
            return

        if self.capture_task is not None:
            return

        self.capture_callback = callback
        self.capture_running = True

        self.capture_task = asyncio.create_task(
            self._capture_loop()
        )

        print("🎤 Continuous microphone capture started")


    async def _capture_loop(self):
        try:
            while self.capture_running:
                raw_frame = await asyncio.to_thread(
                    self.microphone.read
                )

                if not raw_frame:
                    continue

                # IMPORTANT:
                # Always process microphone audio through AEC.
                clean_frame = (
                    self.processor.process_microphone(raw_frame)
                )

                if self.capture_callback:
                    result = self.capture_callback(
                        clean_frame
                    )

                    if asyncio.iscoroutine(result):
                        await result

                await asyncio.sleep(0)

        except asyncio.CancelledError:
            print("🛑 Microphone capture stopped")

            raise

        except Exception as e:
            print(
            f"❌ Microphone capture error: {e}"
        )


    async def stop_capture(self):
        self.capture_running = False

        if self.capture_task is not None:
            self.capture_task.cancel()

            try:
                await self.capture_task

            except asyncio.CancelledError:
                pass

        self.capture_task = None

        self.capture_callback = None




    # -----------------------------------------
    # IMMEDIATE BARGE-IN
    # -----------------------------------------

    def stop(self):
        self.is_playing = False
        self.stop_requested = True

        # Discard audio that has not reached the speaker.
        self.playback_buffer.clear()

        while True:
            try:
                frame = (
                    self.play_queue.get_nowait()
                )

                self.play_queue.task_done()

            except asyncio.QueueEmpty:
                break

        if self.speaker is not None:
            self.speaker.stop()

        print(
            "🔇 Local playback cleared"
        )




    # -----------------------------------------
    # SHUTDOWN
    # -----------------------------------------

    async def shutdown(self):

        self.stop()

        if self.playback_task is not None:

            await self.play_queue.put(None)

            await self.playback_task

            self.playback_task = None

        if self.microphone is not None:
            self.microphone.cleanup()
        if self.speaker is not None:
            self.speaker.cleanup()

    def cleanup(self):

        self.stop()

        if self.microphone is not None:
            self.microphone.cleanup()
        if self.speaker is not None:
            self.speaker.cleanup()

