from datetime import datetime

from pymongo import MongoClient
from pymongo.collection import Collection

from utils.llm import respond


class ConversationHistoryManager:

    def __init__(self, model, uri: str, db_name: str, collection_name: str = "conversations"):
        self._model = model
        self._collection: Collection = MongoClient(uri)[db_name][collection_name]
        self._ensure_indexes()

    def _ensure_indexes(self):
        self._collection.create_index(
            [("session_id", 1), ("created_at", 1)]
        )

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        agent_name: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        self._collection.insert_one({
            "session_id": session_id,
            "role": role,
            "content": content,
            "agent_name": agent_name,
            "created_at": datetime.utcnow(),
            "metadata": metadata or {},
        })

    def get_conversation(
        self, session_id: str, limit: int | None = None, offset: int = 0
    ) -> list[dict]:
        cursor = self._collection.find(
            {"session_id": session_id},
            sort=[("created_at", 1)],
        )
        if offset:
            cursor = cursor.skip(offset)
        if limit is not None:
            cursor = cursor.limit(limit)
        return list(cursor)

    def count_by_session_id(self, session_id: str) -> int:
        return self._collection.count_documents({"session_id": session_id})

    def delete_by_session_id(self, session_id: str) -> int:
        result = self._collection.delete_many({"session_id": session_id})
        return result.deleted_count

    async def summarise_conversation(self, session_id: str, messages: list[dict] | None = None) -> str:
        if messages is None:
            messages = list(self._collection.find(
                {"session_id": session_id},
                sort=[("created_at", 1)],
            ))
        lines = []
        for m in messages:
            tag = f"{m['role']} ({m['agent_name']})" if m.get("agent_name") else m["role"]
            lines.append(f"{tag}: {m['content']}")
        conversation_text = "\n".join(lines)

        summary = await respond(
            self._model,
            system_prompt="Summarize the following conversation concisely. Preserve user info, preferences, and ongoing context. Exclude ALL temporal data — no relative terms (today/tomorrow/yesterday/now/this week), no absolute dates (Oct 13, 2025, etc.), no day names (Monday, Tuesday), and no times. These go stale instantly. Calendar event details belong in the calendar, not in summaries.\n\nThe messages are ordered from oldest to newest. Weight more recent messages more heavily — they better reflect the user's current intent, preferences, and context. Older messages contribute less to the summary. Preserve specific facts, names, preferences, and action items.",
            user_message=conversation_text,
        )
        return summary

    async def update_conversation_with_summary(self, session_id: str) -> bool:
        count = self.count_by_session_id(session_id)
        if count <= 15:
            return False
        messages = list(self._collection.find(
            {"session_id": session_id},
            sort=[("created_at", 1)],
        ))
        keep_count = 5
        to_summarize = messages[:-keep_count]
        to_keep_ids = [m["_id"] for m in messages[-keep_count:]]
        summary = await self.summarise_conversation(session_id, to_summarize)
        self._collection.delete_many({
            "session_id": session_id,
            "_id": {"$nin": to_keep_ids},
        })
        self.add_message(
            session_id, "system", summary, agent_name="summary",
            metadata={"type": "conversation_summary"},
        )
        return True