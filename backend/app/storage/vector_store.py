import chromadb

from app.config.settings import Settings


class VectorStore:
    def __init__(self, settings: Settings):
        self.client = chromadb.PersistentClient(path=settings.chroma_path)
        self.collection = self.client.get_or_create_collection("state_descriptions")

    def add_state_description(
        self,
        *,
        embedding_id: str,
        text: str,
        embedding: list[float],
        metadata: dict,
    ) -> None:
        self.collection.add(
            ids=[embedding_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata],
        )

    def query(
        self,
        *,
        embedding: list[float],
        story_id: int,
        top_k: int = 5,
    ) -> list[str]:
        result = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            where={"story_id": story_id},
        )
        documents = result.get("documents") or [[]]
        return [doc for doc in documents[0] if doc]

