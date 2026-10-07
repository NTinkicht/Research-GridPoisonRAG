from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class Hit:
    rank: int
    score: float
    document: dict[str, Any]


class DenseRetriever:
    """Dense index with reusable clean-corpus embeddings and optional per-query extra documents."""

    def __init__(self, documents: list[dict[str, Any]], model_name: str):
        self.documents = list(documents)
        self.model = SentenceTransformer(model_name)
        self.embeddings = self._encode([d["text"] for d in self.documents])

    def _encode(self, texts: list[str]) -> np.ndarray:
        return self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

    def search(
        self,
        query: str,
        k: int,
        extra_documents: list[dict[str, Any]] | None = None,
    ) -> list[Hit]:
        extra_documents = extra_documents or []
        q = self._encode([query])[0]
        documents = self.documents
        embeddings = self.embeddings
        if extra_documents:
            extra_embeddings = self._encode([d["text"] for d in extra_documents])
            documents = self.documents + extra_documents
            embeddings = np.concatenate([self.embeddings, extra_embeddings], axis=0)
        scores = np.dot(embeddings, q)
        order = np.argsort(-scores)[:k]
        return [
            Hit(rank=i + 1, score=float(scores[idx]), document=documents[int(idx)])
            for i, idx in enumerate(order)
        ]
