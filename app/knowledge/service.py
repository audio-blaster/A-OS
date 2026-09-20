import hashlib
import json
import re
import sqlite3
from html.parser import HTMLParser
from pathlib import Path

import requests


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._parts = []

    def handle_data(self, data):
        if data:
            self._parts.append(data)

    def get_text(self):
        return " ".join(self._parts)


class KnowledgeService:
    def __init__(self, storage_path=None):
        self.storage_path = Path(storage_path or "data/knowledge.db")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(str(self.storage_path))
        self.connection.row_factory = sqlite3.Row
        self._initialize()

    def _initialize(self):
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_sources (
                source_key TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                type TEXT NOT NULL,
                name TEXT NOT NULL,
                value TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS knowledge_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_key TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                content TEXT NOT NULL,
                chunk_order INTEGER NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self.connection.execute(
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_chunks_fts USING fts5(
                chunk_id UNINDEXED,
                agent_id UNINDEXED,
                source_key UNINDEXED,
                source_name UNINDEXED,
                source_type UNINDEXED,
                content,
                tokenize='porter ascii'
            )
            """
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_agent ON knowledge_chunks(agent_id)"
        )
        self.connection.execute(
            "CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_source ON knowledge_chunks(source_key)"
        )
        self.connection.commit()

    @staticmethod
    def _hash_source_key(agent_id, source_type, name, value):
        payload = json.dumps(
            {
                "agent_id": str(agent_id),
                "type": str(source_type),
                "name": str(name or ""),
                "value": str(value or ""),
            },
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @staticmethod
    def _normalize_text(value):
        if value is None:
            return ""
        text = str(value)
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def _sanitize_query(value):
        query = KnowledgeService._normalize_text(value)
        return " ".join(re.findall(r"[A-Za-z0-9_\-/]+", query))

    @staticmethod
    def _chunk_text(value, max_chars=500, overlap=60):
        text = KnowledgeService._normalize_text(value)
        if not text:
            return []

        words = text.split()
        if len(words) <= max_chars // 3:
            return [text]

        chunks = []
        step = max_chars - overlap
        step = max(1, step)

        for start in range(0, len(words), step):
            slice_words = words[start:start + max_chars]
            if not slice_words:
                continue
            chunk = " ".join(slice_words)
            if chunk and chunk not in chunks:
                chunks.append(chunk)

        return chunks or [text]

    @staticmethod
    def _extract_url_text(url):
        response = requests.get(url, timeout=10, headers={"User-Agent": "A-OS-KB/1.0"})
        response.raise_for_status()
        html = response.text
        cleaned = re.sub(r"<script.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
        cleaned = re.sub(r"<style.*?</style>", " ", cleaned, flags=re.IGNORECASE | re.DOTALL)
        parser = _HTMLTextExtractor()
        parser.feed(cleaned)
        return KnowledgeService._normalize_text(parser.get_text())

    @staticmethod
    def _source_text(source):
        source_type = (source or {}).get("type", "document")
        name = (source or {}).get("name") or ""
        value = (source or {}).get("value") or ""

        if source_type == "faq":
            question = KnowledgeService._normalize_text(name)
            answer = KnowledgeService._normalize_text(value)
            parts = []
            if question:
                parts.append(f"Question: {question}")
            if answer:
                parts.append(f"Answer: {answer}")
            return "\n".join(parts)

        if source_type == "url":
            url = KnowledgeService._normalize_text(value)
            if not url:
                return ""
            return KnowledgeService._extract_url_text(url)

        document_text = KnowledgeService._normalize_text(value)
        if document_text:
            if name and name.lower().endswith((".txt", ".md")):
                return document_text
            if source_type == "document":
                return document_text
        if name:
            return KnowledgeService._normalize_text(name)
        return ""

    def _upsert_source(self, agent_id, source):
        if not isinstance(source, dict):
            return None

        source_type = str(source.get("type") or "document").strip().lower()
        name = str(source.get("name") or "").strip()
        value = source.get("value") or ""
        source_key = self._hash_source_key(agent_id, source_type, name, value)
        status = str(source.get("status") or "ready").strip().lower() or "ready"

        now = __import__("datetime").datetime.utcnow().isoformat()
        try:
            source_text = self._source_text(source)
            if not source_text:
                status = "error"
        except Exception:
            source_text = ""
            status = "error"

        self.connection.execute(
            """
            INSERT INTO knowledge_sources (source_key, agent_id, type, name, value, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_key) DO UPDATE SET
                agent_id=excluded.agent_id,
                type=excluded.type,
                name=excluded.name,
                value=excluded.value,
                status=excluded.status,
                updated_at=excluded.updated_at
            """,
            (
                source_key,
                agent_id,
                source_type,
                name or source_type,
                str(value),
                status,
                now,
                now,
            ),
        )
        self.connection.execute("DELETE FROM knowledge_chunks WHERE source_key = ?", (source_key,))
        self.connection.execute("DELETE FROM knowledge_chunks_fts WHERE source_key = ?", (source_key,))

        if status == "error" or not source_text:
            self.connection.commit()
            return source_key

        for order, chunk in enumerate(self._chunk_text(source_text)):
            cursor = self.connection.execute(
                """
                INSERT INTO knowledge_chunks (source_key, agent_id, content, chunk_order, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (source_key, agent_id, chunk, order, now),
            )
            chunk_id = cursor.lastrowid
            self.connection.execute(
                """
                INSERT INTO knowledge_chunks_fts (chunk_id, agent_id, source_key, source_name, source_type, content)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (chunk_id, agent_id, source_key, name or source_type, source_type, chunk),
            )

        self.connection.commit()
        return source_key

    def reindex_agent(self, agent_id, sources):
        if agent_id is None:
            return []

        self.connection.execute("DELETE FROM knowledge_chunks WHERE agent_id = ?", (agent_id,))
        self.connection.execute("DELETE FROM knowledge_chunks_fts WHERE agent_id = ?", (agent_id,))
        self.connection.execute("DELETE FROM knowledge_sources WHERE agent_id = ?", (agent_id,))

        if not isinstance(sources, list):
            sources = []

        indexed = []
        for source in sources:
            source_key = self._upsert_source(agent_id, source)
            if source_key:
                indexed.append(source_key)

        self.connection.commit()
        return indexed

    def retrieve(self, agent_id, query, limit=3):
        if not agent_id or not query:
            return []

        query_text = self._sanitize_query(query)
        if not query_text:
            return []

        rows = self.connection.execute(
            """
            SELECT
                kc.id,
                kc.source_key,
                kc.agent_id,
                kc.content,
                kc.chunk_order,
                ks.name AS source_name,
                ks.type AS source_type,
                bm25(knowledge_chunks_fts) AS score
            FROM knowledge_chunks_fts AS fts
            JOIN knowledge_chunks AS kc ON kc.id = fts.chunk_id
            JOIN knowledge_sources AS ks ON ks.source_key = kc.source_key
            WHERE kc.agent_id = ?
              AND knowledge_chunks_fts MATCH ?
            ORDER BY bm25(knowledge_chunks_fts)
            LIMIT ?
            """,
            (agent_id, query_text, int(limit)),
        ).fetchall()

        results = []
        for row in rows:
            results.append(
                {
                    "source_key": row["source_key"],
                    "agent_id": row["agent_id"],
                    "source_name": row["source_name"],
                    "source_type": row["source_type"],
                    "content": row["content"],
                    "chunk_order": row["chunk_order"],
                    "score": row["score"],
                }
            )

        return results

    def render_context_for_query(self, agent_id, query, limit=3):
        results = self.retrieve(agent_id, query, limit=limit)
        if not results:
            return ""

        lines = ["Relevant knowledge:"]
        for result in results:
            lines.append(f"Source: {result['source_name']} ({result['source_type']})")
            lines.append(result["content"])
        return "\n".join(lines)


knowledge_service = KnowledgeService()
