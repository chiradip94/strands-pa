
class VectorStore:
    def add_vector(self, text: str, metadata: dict):
        raise NotImplementedError

    def search(self, query_text: str, top_k: int = 5) -> list[dict]:
        raise NotImplementedError
    
    def update(self, text: str, metadata: dict, point_id: str | None = None):
        raise NotImplementedError

    def delete(self, point_id: str):
        raise NotImplementedError