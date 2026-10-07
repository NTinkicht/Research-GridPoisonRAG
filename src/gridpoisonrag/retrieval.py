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
    def __init__(self, documents: list[dict[str, Any]], model_name: str):
        self.documents = documents
        self.model = SentenceTransformer(model_name)
        texts = [d["text"] for d in documents]
        self.embeddings = self.model.encode(
            texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

    def search(self, query: str, k: int) -> list[Hit]:
        q = self.model.encode(
            [query], normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False
        )[0]
        scores = np.dot(self.embeddings, q)
        order = np.argsort(-scores)[:k]
        return [
            Hit(rank=i + 1, score=float(scores[idx]), document=self.documents[int(idx)])
            for i, idx in enumerate(order)
        ]
