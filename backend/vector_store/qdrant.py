import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, Document


class QdrantVectorStore:

    def __init__(
        self,
        url: str,
        api_key: str,
        collection_name: str,
        model: str,
        vector_size: int = 1536,
        cloud_inference: bool = True,
    ):
        self.client = QdrantClient(url=url, api_key=api_key, cloud_inference=cloud_inference)
        self.collection_name = collection_name
        self.model = model
        self.vector_size = vector_size
        self._ensure_collection()

    def _ensure_collection(self):
        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=self.vector_size, distance=Distance.COSINE),
            )

    def add_vector(self, text: str, metadata: dict):
        metadata["original_text"] = text  # Store original text in metadata for reference
        point = PointStruct(
            id=uuid.uuid4(),
            vector=Document(text=text, model=self.model),
            payload=metadata,
        )
        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

    def search(self, query_text: str, top_k: int = 5) -> list[dict]:
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=Document(text=query_text, model=self.model),
            limit=top_k,
            with_payload=True,
        )
        return [
            {
                "id": str(hit.id),
                "score": hit.score,
                "metadata": hit.payload,
            }
            for hit in results.points
        ]
