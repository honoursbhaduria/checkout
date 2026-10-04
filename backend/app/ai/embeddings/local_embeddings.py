import math
import hashlib
import logging
from typing import List

logger = logging.getLogger(__name__)


class LocalEmbeddings:
    """
    Local sentence embedding generator.
    Uses sentence-transformers (e.g. all-MiniLM-L6-v2, 384 dimensions) when installed,
    with a deterministic normalized hashing vector fallback for zero-dependency offline environments.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dimension: int = 384):
        self.model_name = model_name
        self.dimension = dimension
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except ImportError:
                logger.info("sentence-transformers not installed. Using deterministic vector generation.")
                self._model = False
        return self._model

    def embed_text(self, text: str) -> List[float]:
        model = self._get_model()
        if model and model is not False:
            try:
                vector = model.encode(text).tolist()
                return vector
            except Exception as e:
                logger.warning(f"SentenceTransformer encoding failed: {e}")

        # Deterministic 384-dimensional vector fallback
        vec = []
        for i in range(self.dimension):
            h = hashlib.sha256(f"{text}_{i}".encode()).hexdigest()
            val = (int(h[:8], 16) / 0xFFFFFFFF) * 2 - 1
            vec.append(val)
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


local_embeddings = LocalEmbeddings()
