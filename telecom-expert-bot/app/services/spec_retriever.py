import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class SpecRetriever:
    def __init__(self, persist_directory: str = "./chroma_data", collection_name: str = "3gpp_specs"):
        self._persist_directory = persist_directory
        self._collection_name = collection_name
        self._client = None
        self._collection = None
        self._available = False
        self._init_chroma()

    def _init_chroma(self):
        try:
            import chromadb
            self._client = chromadb.PersistentClient(path=self._persist_directory)
            self._collection = self._client.get_or_create_collection(
                name=self._collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self._available = True
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.warning(f"ChromaDB not available: {e}. Using fallback mode.")
            self._available = False

    def is_available(self) -> bool:
        return self._available

    async def add_document(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        doc_id: Optional[str] = None,
    ) -> bool:
        if not self._available:
            return False
        try:
            import uuid
            doc_id = doc_id or str(uuid.uuid4())
            self._collection.add(
                documents=[text],
                metadatas=[metadata or {}],
                ids=[doc_id],
            )
            return True
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False

    async def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self._available:
            return []
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=top_k,
            )
            formatted = []
            if results and results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    formatted.append({
                        "text": doc,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 0.0,
                    })
            return formatted
        except Exception as e:
            logger.error(f"Error searching: {e}")
            return []

    async def ingest_specs(self, documents: List[Dict[str, Any]]) -> int:
        if not self._available:
            return 0
        count = 0
        for doc in documents:
            success = await self.add_document(
                text=doc.get("text", ""),
                metadata=doc.get("metadata", {}),
                doc_id=doc.get("id"),
            )
            if success:
                count += 1
        return count

    async def get_context_for_query(self, query: str, top_k: int = 5) -> str:
        results = await self.search(query, top_k=top_k)
        if not results:
            return ""
        context_parts = []
        for r in results:
            meta = r.get("metadata", {})
            spec_ref = f"{meta.get('spec_number', 'Unknown')} Section {meta.get('section', 'N/A')}"
            context_parts.append(f"[{spec_ref}]\n{r['text']}")
        return "\n\n".join(context_parts)
