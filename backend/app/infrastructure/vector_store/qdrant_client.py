import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.core.config import settings

logger = logging.getLogger(__name__)


import os

class QdrantVectorStore:
    """
    Qdrant Vector Store wrapper.
    Supports Qdrant Cloud with API Key, localhost:6333, or in-memory fallback.
    """

    def __init__(self, url: Optional[str] = None, api_key: Optional[str] = None, host: str = "localhost", port: int = 6333):
        self.url = url or os.environ.get("QDRANT_URL")
        self.api_key = api_key or os.environ.get("QDRANT_API_KEY")
        self.host = host
        self.port = port
        self._client: Optional[QdrantClient] = None
        self._init_client()

    def _init_client(self):
        if self.url:
            try:
                self._client = QdrantClient(url=self.url, api_key=self.api_key, timeout=5.0)
                self._client.get_collections()
                logger.info(f"Connected to Qdrant Cloud at {self.url}")
                return
            except Exception as e:
                logger.warning(f"Failed to connect to Qdrant Cloud: {e}")

        try:
            self._client = QdrantClient(host=self.host, port=self.port, timeout=2.0)
            self._client.get_collections()
            logger.info(f"Connected to self-hosted Qdrant at {self.host}:{self.port}")
        except Exception:
            logger.info("Self-hosted Qdrant server not reached. Initializing fast in-memory Qdrant instance.")
            self._client = QdrantClient(":memory:")

    def ensure_collection(self, collection_name: str, vector_size: int = 384):
        try:
            collections = [c.name for c in self._client.get_collections().collections]
            if collection_name not in collections:
                self._client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
        except Exception as e:
            logger.error(f"Error ensuring collection {collection_name}: {e}")

    def upsert_vectors(self, collection_name: str, points: List[Dict[str, Any]]):
        self.ensure_collection(collection_name)
        qdrant_points = [
            PointStruct(
                id=p["id"],
                vector=p["vector"],
                payload=p.get("payload", {})
            )
            for p in points
        ]
        self._client.upsert(collection_name=collection_name, points=qdrant_points)

    def search(self, collection_name: str, query_vector: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        self.ensure_collection(collection_name)
        results = self._client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=limit
        ).points
        return [
            {
                "id": r.id,
                "score": r.score,
                "payload": r.payload
            }
            for r in results
        ]


qdrant_store = QdrantVectorStore()
