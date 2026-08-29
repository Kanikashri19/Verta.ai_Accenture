from typing import List
from fastembed import TextEmbedding

class LocalEmbedder:
    """
    Local ONNX-based embedding engine using FastEmbed.
    Model: BAAI/bge-small-en-v1.5 (384-dimensional vectors).
    Zero cloud dependencies, 100% offline.
    """

    MODEL_NAME = "BAAI/bge-small-en-v1.5"

    def __init__(self, model_name: str = MODEL_NAME):
        self.model_name = model_name
        self._model = TextEmbedding(model_name=self.model_name)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generates dense vector embeddings for a list of text strings.
        """
        if not texts:
            return []
        embeddings = list(self._model.embed(texts))
        return [e.tolist() for e in embeddings]

    def embed_query(self, query: str) -> List[float]:
        """
        Generates embedding vector for a single query string.
        """
        res = self.embed_texts([query])
        return res[0] if res else [0.0] * 384

local_embedder = LocalEmbedder()
