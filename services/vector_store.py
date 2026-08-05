"""Vector store abstraction and a simple in‑memory implementation.

The project will use a vector store to keep embeddings of domain
knowledge (e.g., rule libraries, past execution logs, product
catalogues).  The interface is intentionally minimal so that we can
swap out the backend (FAISS, Pinecone, Weaviate, etc.) without
touching the rest of the code base.

Only the methods required by the current RAG agent are exposed:

* :func:`add_documents` – add a batch of documents with their
  embeddings.
* :func:`query` – retrieve the top‑k most similar documents for a
  query vector.
* :func:`delete` – remove documents by id.

The in‑memory implementation keeps a list of tuples ``(id, vector,
metadata)`` and performs a linear scan for similarity.  It is
adequate for unit tests and small demo runs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple

import numpy as np

__all__ = ["VectorStore", "InMemoryVectorStore", "Document"]


@dataclass
class Document:
    """Simple container for a document embedding and optional metadata."""

    id: str
    vector: np.ndarray
    metadata: dict | None = None


class VectorStore:
    """Abstract base class for vector stores.

    Sub‑classes must implement :meth:`add_documents`, :meth:`query`, and
    :meth:`delete`.
    """

    def add_documents(self, docs: Iterable[Document]) -> None:  # pragma: no cover
        raise NotImplementedError

    def query(self, vector: np.ndarray, k: int = 5) -> List[Document]:  # pragma: no cover
        raise NotImplementedError

    def delete(self, ids: Iterable[str]) -> None:  # pragma: no cover
        raise NotImplementedError


class InMemoryVectorStore(VectorStore):
    """A naive in‑memory vector store.

    It stores documents in a list and performs a linear scan for
    similarity.  Cosine similarity is used as the distance metric.
    """

    def __init__(self) -> None:
        self._docs: List[Document] = []

    def add_documents(self, docs: Iterable[Document]) -> None:
        self._docs.extend(docs)

    def query(self, vector: np.ndarray, k: int = 5) -> List[Document]:
        if not self._docs:
            return []
        # Compute cosine similarity
        vec_norm = vector / np.linalg.norm(vector)
        sims = []
        for doc in self._docs:
            doc_norm = doc.vector / np.linalg.norm(doc.vector)
            sims.append((np.dot(vec_norm, doc_norm), doc))
        sims.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in sims[:k]]

    def delete(self, ids: Iterable[str]) -> None:
        id_set = set(ids)
        self._docs = [doc for doc in self._docs if doc.id not in id_set]
