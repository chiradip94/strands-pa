from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection

from strands.session.session_repository import SessionRepository
from strands.types.session import Session, SessionAgent, SessionMessage, SessionType


class MongoSessionRepository(SessionRepository):

    def __init__(self, uri: str, db_name: str):
        self._db = MongoClient(uri)[db_name]
        self._sessions: Collection = self._db["sessions"]
        self._agents: Collection = self._db["agents"]
        self._messages: Collection = self._db["messages"]
        self._ensure_indexes()

    def _ensure_indexes(self):
        self._sessions.create_index("session_id", unique=True)
        self._agents.create_index(["session_id", "agent_id"], unique=True)
        self._messages.create_index(["session_id", "agent_id", "message_id"])

    # --- Session ---

    def create_session(self, session: Session, **kwargs: Any) -> Session:
        self._sessions.insert_one(session.to_dict())
        return session

    def read_session(self, session_id: str, **kwargs: Any) -> Session | None:
        doc = self._sessions.find_one({"session_id": session_id})
        if doc is None:
            return None
        doc.pop("_id", None)
        return Session.from_dict(doc)

    # --- Agent ---

    def create_agent(self, session_id: str, session_agent: SessionAgent, **kwargs: Any) -> None:
        doc = session_agent.to_dict()
        doc["session_id"] = session_id
        self._agents.insert_one(doc)

    def read_agent(self, session_id: str, agent_id: str, **kwargs: Any) -> SessionAgent | None:
        doc = self._agents.find_one({"session_id": session_id, "agent_id": agent_id})
        if doc is None:
            return None
        doc.pop("_id", None)
        doc.pop("session_id", None)
        return SessionAgent.from_dict(doc)

    def update_agent(self, session_id: str, session_agent: SessionAgent, **kwargs: Any) -> None:
        doc = session_agent.to_dict()
        doc["session_id"] = session_id
        self._agents.replace_one(
            {"session_id": session_id, "agent_id": session_agent.agent_id},
            doc,
        )

    # --- Message ---

    def create_message(self, session_id: str, agent_id: str, session_message: SessionMessage, **kwargs: Any) -> None:
        doc = session_message.to_dict()
        doc["session_id"] = session_id
        doc["agent_id"] = agent_id
        self._messages.insert_one(doc)

    def read_message(self, session_id: str, agent_id: str, message_id: int, **kwargs: Any) -> SessionMessage | None:
        doc = self._messages.find_one({"session_id": session_id, "agent_id": agent_id, "message_id": message_id})
        if doc is None:
            return None
        doc.pop("_id", None)
        doc.pop("session_id", None)
        doc.pop("agent_id", None)
        return SessionMessage.from_dict(doc)

    def update_message(self, session_id: str, agent_id: str, session_message: SessionMessage, **kwargs: Any) -> None:
        doc = session_message.to_dict()
        doc["session_id"] = session_id
        doc["agent_id"] = agent_id
        self._messages.replace_one(
            {"session_id": session_id, "agent_id": agent_id, "message_id": session_message.message_id},
            doc,
        )

    def list_messages(
        self, session_id: str, agent_id: str, limit: int | None = None, offset: int = 0, **kwargs: Any
    ) -> list[SessionMessage]:
        cursor = self._messages.find(
            {"session_id": session_id, "agent_id": agent_id},
            sort=[("message_id", 1)],
        )
        if offset:
            cursor = cursor.skip(offset)
        if limit is not None:
            cursor = cursor.limit(limit)
        result = []
        for doc in cursor:
            doc.pop("_id", None)
            doc.pop("session_id", None)
            doc.pop("agent_id", None)
            result.append(SessionMessage.from_dict(doc))
        return result

    # --- Delete ---

    def delete_session(self, session_id: str) -> None:
        self._sessions.delete_one({"session_id": session_id})
        self._agents.delete_many({"session_id": session_id})
        self._messages.delete_many({"session_id": session_id})

    # --- Session listing ---

    def list_sessions(self) -> list[dict]:
        pipeline = [
            {"$group": {
                "_id": "$session_id",
                "last_updated": {"$max": "$updated_at"},
            }},
            {"$sort": {"last_updated": -1}},
        ]
        docs = list(self._messages.aggregate(pipeline))
        result = []
        for doc in docs:
            session_id = doc["_id"]
            first = self._messages.find_one(
                {"session_id": session_id, "message.role": {"$in": ["user", "assistant"]}},
                sort=[("message_id", 1)],
            )
            title = ""
            if first:
                blocks = first.get("message", {}).get("content", [])
                texts = [b.get("text", "") for b in blocks if isinstance(b, dict) and "text" in b]
                title = " ".join(texts)[:80]
            result.append({
                "id": session_id,
                "title": title or "New chat",
                "last_updated": doc.get("last_updated", ""),
            })
        return result

    # --- Multi-agent (not used) ---

    def create_multi_agent(self, session_id: str, multi_agent: Any, **kwargs: Any) -> None:
        raise NotImplementedError("Multi-agent not implemented")

    def read_multi_agent(self, session_id: str, multi_agent_id: str, **kwargs: Any) -> dict[str, Any] | None:
        raise NotImplementedError("Multi-agent not implemented")

    def update_multi_agent(self, session_id: str, multi_agent: Any, **kwargs: Any) -> None:
        raise NotImplementedError("Multi-agent not implemented")
