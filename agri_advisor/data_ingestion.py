from __future__ import annotations
import argparse
from pathlib import Path
import csv
import json
import math
from collections import Counter, defaultdict
from typing import List, Dict, Any

from .config import INDEX_DIR

DATASETS = {
    "weather": {
        "file": "weather_sample.csv",
        "key": "weather_id",
        "text_fields": ["district", "date", "tmax_c", "tmin_c", "rain_mm", "humidity_pct"],
        "source": "IMD sample",
    },
    "crop_calendar": {
        "file": "crop_calendar.csv",
        "key": "crop",
        "text_fields": ["crop", "season", "sowing_start", "sowing_end", "duration_days"],
        "source": "ICAR sample",
    },
    "pest_alerts": {
        "file": "pest_alerts.csv",
        "key": "id",
        "text_fields": ["crop", "pest", "conditions", "advice"],
        "source": "ICAR/PPVFRA sample",
    },
    "mandi_prices": {
        "file": "mandi_prices.csv",
        "key": "id",
        "text_fields": ["commodity", "district", "date", "modal_price", "unit"],
        "source": "Agmarknet sample",
    },
    "soil": {
        "file": "soil_types.csv",
        "key": "district",
        "text_fields": ["district", "soil_texture", "whc_mm", "drainage"],
        "source": "Soil Health Card sample",
    },
    "policies": {
        "file": "policies.csv",
        "key": "scheme",
        "text_fields": ["scheme", "name", "eligibility", "benefit"],
        "source": "Govt schemes sample",
    },
}


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append({k: (v if v is not None else "") for k, v in row.items()})
    return rows


def build_corpus(data_dir: Path) -> List[Dict[str, Any]]:
    corpus: List[Dict[str, Any]] = []
    for name, meta in DATASETS.items():
        fpath = data_dir / meta["file"]
        if not fpath.exists():
            continue
        rows = read_csv_rows(fpath)
        for i, row in enumerate(rows):
            text = " | ".join(str(row.get(field, "")) for field in meta["text_fields"])  # type: ignore
            corpus.append({
                "__dataset": name,
                "__source": meta["source"],
                "__id": str(i),
                "__text": text,
            })
    return corpus


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


def build_index(corpus: List[Dict[str, Any]], index_dir: Path) -> None:
    index_dir.mkdir(parents=True, exist_ok=True)
    if not corpus:
        raise RuntimeError("Empty corpus; place CSVs in data/samples")

    # Document frequencies
    df_counter: Counter[str] = Counter()
    docs_tokens: List[List[str]] = []
    for doc in corpus:
        toks = tokenize(doc["__text"])
        docs_tokens.append(toks)
        df_counter.update(set(toks))

    num_docs = len(corpus)
    idf: Dict[str, float] = {term: math.log((1 + num_docs) / (1 + df)) + 1.0 for term, df in df_counter.items()}

    # Build vectors as term->weight dictionaries
    vectors: List[Dict[str, float]] = []
    for toks in docs_tokens:
        tf = Counter(toks)
        vec: Dict[str, float] = {}
        max_tf = max(tf.values()) if tf else 1
        for term, cnt in tf.items():
            tf_weight = 0.5 + 0.5 * (cnt / max_tf)
            vec[term] = tf_weight * idf.get(term, 0.0)
        vectors.append(vec)

    # Save index
    (index_dir / "corpus.json").write_text(json.dumps(corpus), encoding="utf-8")
    (index_dir / "idf.json").write_text(json.dumps(idf), encoding="utf-8")
    (index_dir / "vectors.json").write_text(json.dumps(vectors), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=str, required=True)
    parser.add_argument("--db-path", type=str, required=False)
    parser.add_argument("--rebuild-index", action="store_true")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    index_dir = INDEX_DIR

    corpus = build_corpus(data_dir)
    if args.rebuild_index:
        build_index(corpus, index_dir)
    print(json.dumps({"docs": len(corpus)}))

if __name__ == "__main__":
    main()