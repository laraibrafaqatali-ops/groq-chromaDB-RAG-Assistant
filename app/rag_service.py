from typing import Any, Dict, List, Optional

from .embedding_service import EmbeddingService
from .groq_service import GroqService
from .vector_store import ChromaVectorStore


class RAGService:
    def __init__(self) -> None:
        self.embedder = EmbeddingService()
        self.store = ChromaVectorStore()
        self.groq = GroqService()

    def ask(
        self,
        question: str,
        top_k: Optional[int] = None,
        source: Optional[str] = None,
    ) -> Dict[str, Any]:

        question = question.strip()

        if not question:
            raise ValueError("Question cannot be empty.")

        if top_k is None:
            top_k = 5

        if self.store.count() == 0:
            raise RuntimeError(
                "No documents are indexed in ChromaDB. "
                "Please run the ingestion step first."
            )

        # Question ko embedding mein convert karo
        query_embedding = self.embedder.embed_one(question)

        # Optional source filter
        where = None

        if source:
            where = {"source": source}

        # ChromaDB se relevant chunks retrieve karo
        results = self.store.query(
            query_embedding=query_embedding,
            top_k=top_k,
            where=where,
        )

        if not results:
            return {
                "answer": "I could not find enough information in the supplied documents.",
                "sources": [],
            }

        # Retrieved chunks ko Groq ke context mein convert karo
        context_parts: List[str] = []

        sources: List[Dict[str, Any]] = []

        for result in results:
            metadata = result.get("metadata") or {}
            text = result.get("text") or ""

            source_name = metadata.get(
                "source",
                metadata.get("filename", "unknown"),
            )

            context_parts.append(
                f"Source: {source_name}\n"
                f"{text}"
            )

            sources.append(
                {
                    "id": result.get("id"),
                    "source": source_name,
                    "distance": result.get("distance"),
                    "metadata": metadata,
                }
            )

        context = "\n\n---\n\n".join(context_parts)

        # Groq final answer generate karega
        answer = self.groq.generate_answer(
            question=question,
            context=context,
        )

        return {
            "answer": answer,
            "sources": sources,
        }