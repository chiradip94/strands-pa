
class VectorStore:
    def add_vector(self, text: str, metadata: dict):
        raise NotImplementedError

    def search(self, query_text: str, top_k: int = 5) -> list[dict]:
        raise NotImplementedError