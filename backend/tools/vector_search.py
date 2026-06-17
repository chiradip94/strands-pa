from strands import tool
from vector_store.base import VectorStore


def make_memory_tools(vector_store: VectorStore):
    @tool
    def add_memory(text: str, metadata: dict) -> dict:
        """Store a new memory with text content and associated metadata.

        Args:
            text: The text content to remember, this is used for vector search and should be concise but descriptive.
            metadata: Dictionary of metadata to associate with this memory

        Returns:
            A dict with status and message confirming the memory was stored
        """
        vector_store.add_vector(text, metadata)
        return {"status": "success", "message": "Memory stored successfully"}

    @tool
    def update_memory(text: str, metadata: dict, point_id: str | None = None) -> dict:
        """Update an existing memory. Pass point_id to update a specific memory by its ID (returned by search_memory). Without point_id, updates the first memory matching the text, or creates a new one if none exists.

        Args:
            text: The text content to update, this is used for vector search and should be concise but descriptive.
            metadata: Dictionary of metadata to associate with this memory
            point_id: Optional unique ID of the specific memory to update (obtained from search_memory results)

        Returns:
            A dict with status and message confirming the memory was updated or stored
        """
        vector_store.update(text, metadata, point_id)
        return {"status": "success", "message": "Memory updated successfully"}

    @tool
    def search_memory(query_text: str, top_k: int = 5) -> list[dict]:
        """Search stored memories by semantic similarity to the query text.

        Args:
            query_text: The text to search for in memories
            top_k: Maximum number of results to return (default 5)

        Returns:
            List of matching memories with id, score, and metadata
        """
        return vector_store.search(query_text, top_k)

    return [add_memory, update_memory, search_memory]
