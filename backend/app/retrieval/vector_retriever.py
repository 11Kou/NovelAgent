from app.services.model_clients import EmbeddingClient
from app.storage.vector_store import VectorStore


class VectorRetriever:
    def __init__(self, embedding_client: EmbeddingClient, vector_store: VectorStore):
        self.embedding_client = embedding_client
        self.vector_store = vector_store

    def retrieve(self, *, story_id: int, query: str, top_k: int = 5) -> list[str]:
        if not query.strip():
            return []
        embedding = self.embedding_client.embed(query)
        return self.vector_store.query(embedding=embedding, story_id=story_id, top_k=top_k)

