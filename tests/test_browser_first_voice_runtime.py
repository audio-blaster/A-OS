import asyncio
import sys
import types


audioop = types.ModuleType("audioop")
audioop.rms = lambda data, width: 0
audioop.ratecv = lambda data, width, nchannels, inrate, outrate, state, weight_a=1.0, weight_b=0.0: (data, state)
sys.modules.setdefault("audioop", audioop)

pyaudio = types.ModuleType("pyaudio")

class DummyPyAudio:
    def __init__(self, *args, **kwargs):
        pass


pyaudio.PyAudio = DummyPyAudio
pyaudio.paInt16 = 8
sys.modules.setdefault("pyaudio", pyaudio)

module = types.ModuleType("aec_audio_processing")

class DummyAudioProcessor:
    def __init__(self, *args, **kwargs):
        pass

    def set_stream_format(self, *args, **kwargs):
        pass

    def set_reverse_stream_format(self, *args, **kwargs):
        pass

    def set_stream_delay(self, *args, **kwargs):
        pass

    def process_stream(self, chunk):
        return chunk

    def process_reverse_stream(self, chunk):
        return None


module.AudioProcessor = DummyAudioProcessor
sys.modules.setdefault("aec_audio_processing", module)

numpy = types.ModuleType("numpy")
class DummyNDArray:
    def __array__(self):
        return self

numpy.frombuffer = lambda data, dtype=None: data
numpy.int16 = int
numpy.float32 = float
sys.modules.setdefault("numpy", numpy)

torch = types.ModuleType("torch")
torch.from_numpy = lambda data: data
sys.modules.setdefault("torch", torch)

silero_vad = types.ModuleType("silero_vad")
silero_vad.load_silero_vad = lambda: object()
silero_vad.get_speech_timestamps = lambda *args, **kwargs: []
sys.modules.setdefault("silero_vad", silero_vad)

from app.audio.engine import AudioEngine


def test_audio_engine_disables_local_hardware_when_browser_first_mode_is_enabled():
    engine = AudioEngine(enable_local_audio=False)

    assert engine.microphone is None
    assert engine.speaker is None
    assert engine.enable_local_audio is False

    asyncio.run(engine.start_capture(lambda _: None))
    assert engine.capture_task is None


def test_browser_audio_callback_still_works_without_local_speaker():
    engine = AudioEngine(enable_local_audio=False)
    calls = []

    async def callback(audio_bytes):
        calls.append(len(audio_bytes))

    engine.set_browser_audio_callback(callback)

    asyncio.run(engine.play_frame(b"\x00\x00\x00\x00"))

    assert calls == [4]
