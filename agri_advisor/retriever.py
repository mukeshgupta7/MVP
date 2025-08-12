from __future__ import annotations
from pathlib import Path
import json
from typing import List, Dict, Any
import math

from .config import INDEX_DIR, MAX_DOCS


def tokenize(text: str) -> List[str]:
    buf = []
    word = []
    for ch in text.lower():
        if ch.isalnum():
            word.append(ch)
        else:
            if word:
                buf.append("".join(word))
                word = []
    if word:
        buf.append("".join(word))
    return [w for w in buf if w]


class LocalRetriever:
    def __init__(self, index_dir: Path = INDEX_DIR):
        self.index_dir = Path(index_dir)
        self.corpus = json.loads((self.index_dir / "corpus.json").read_text(encoding="utf-8"))
        self.idf: Dict[str, float] = json.loads((self.index_dir / "idf.json").read_text(encoding="utf-8"))
        self.vectors: List[Dict[str, float]] = json.loads((self.index_dir / "vectors.json").read_text(encoding="utf-8"))

    def _vectorize_query(self, query: str) -> Dict[str, float]:
        toks = tokenize(query)
        tf: Dict[str, int] = {}
        for t in toks:
            tf[t] = tf.get(t, 0) + 1
        max_tf = max(tf.values()) if tf else 1
        vec: Dict[str, float] = {}
        for term, cnt in tf.items():
            tf_weight = 0.5 + 0.5 * (cnt / max_tf)
            vec[term] = tf_weight * self.idf.get(term, 0.0)
        return vec

    def _cosine(self, q: Dict[str, float], d: Dict[str, float]) -> float:
        # dot
        dot = 0.0
        for term, qv in q.items():
            dv = d.get(term)
            if dv is not None:
                dot += qv * dv
        # norms
        nq = math.sqrt(sum(v * v for v in q.values())) or 1.0
        nd = math.sqrt(sum(v * v for v in d.values())) or 1.0
        return dot / (nq * nd)

    def retrieve(self, query: str, k: int = MAX_DOCS) -> List[Dict[str, Any]]:
        qvec = self._vectorize_query(query)
        scores: List[float] = []
        for dvec in self.vectors:
            scores.append(self._cosine(qvec, dvec))
        ranked = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
        results: List[Dict[str, Any]] = []
        for idx in ranked:
            doc = self.corpus[idx].copy()
            doc["score"] = float(scores[idx])
            results.append(doc)
        return results