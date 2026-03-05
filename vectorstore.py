"""ChromaDB vector store with multilingual embeddings."""

from pathlib import Path

import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction


EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
COLLECTION_NAME = "pistrik_kb"


class VectorStore:
    def __init__(self, persist_dir: Path | str = "chroma_db"):
        self._persist_dir = str(persist_dir)
        self._embedding_fn = SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        self._client = chromadb.PersistentClient(path=self._persist_dir)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: list[dict]) -> None:
        if not chunks:
            return
        ids = [f"chunk_{i}_{hash(c['text'][:50])}" for i, c in enumerate(chunks)]
        documents = [c["text"] for c in chunks]
        metadatas = [
            {k: str(v) for k, v in c.get("metadata", {}).items()}
            for c in chunks
        ]
        self._collection.add(documents=documents, metadatas=metadatas, ids=ids)

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        if self._collection.count() == 0:
            return []
        results = self._collection.query(query_texts=[query], n_results=min(top_k, self._collection.count()))
        output = []
        for i in range(len(results["documents"][0])):
            output.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": round(1 - results["distances"][0][i], 4),  # cosine: 1 = identical
            })
        return output

    def count(self) -> int:
        return self._collection.count()

    def clear(self) -> None:
        self._client.delete_collection(COLLECTION_NAME)
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
