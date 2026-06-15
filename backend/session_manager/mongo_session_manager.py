from datetime import datetime

from pymongo import MongoClient
from pymongo.collection import Collection


class ConversationHistoryManager:

    def __init__(self, uri: str, db_name: str, collection_name: str = "conversations"):
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
