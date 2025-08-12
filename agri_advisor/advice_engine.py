from __future__ import annotations
from typing import Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
import langid

from .retriever import LocalRetriever
from .rules import when_to_irrigate, parse_weather, parse_soil
from .config import INDEX_DIR

@dataclass
class AdvisorResult:
    answer: str
    confidence: float
    reasons: List[str]
    citations: List[Dict[str, Any]]
    followups: List[str]
    debug: Dict[str, Any]


class AgriAdvisor:
    def __init__(self, data_dir: Path):
        self.retriever = LocalRetriever(INDEX_DIR)
        self.data_dir = Path(data_dir)

    def ask(self, question: str, district: str | None = None, crop: str | None = None, lang: str = "en") -> AdvisorResult:
        lang_detected, _ = langid.classify(question)
        lang = lang or lang_detected
        query = self._augment_query(question, district, crop)
        docs = self.retriever.retrieve(query)

        reasons: List[str] = []
        citations: List[Dict[str, Any]] = []
        for d in docs:
            citations.append({"source": d.get("__source"), "dataset": d.get("__dataset")})

        lower_q = question.lower()
        if "irrigate" in lower_q or "सिंचाई" in lower_q:
            w = parse_weather(self.data_dir / "weather_sample.csv", district)
            s = parse_soil(self.data_dir / "soil_types.csv", district)
            rule = when_to_irrigate(w, s)
            answer = reasons_to_answer(rule.messages)
            conf = rule.confidence
            reasons.extend(rule.messages)
            return AdvisorResult(answer, conf, reasons, citations, self._followups(), {"hits": docs[:3]})

        top_texts = [d["__text"] for d in docs[:3]]
        answer = summarize_bullets(top_texts)
        reasons.extend(["Synthesized from local datasets via TF-IDF retrieval."])
        return AdvisorResult(answer, 0.55, reasons, citations, self._followups(), {"hits": docs[:3]})

    def _augment_query(self, question: str, district: str | None, crop: str | None) -> str:
        parts = [question]
        if district:
            parts.append(f"district: {district}")
        if crop:
            parts.append(f"crop: {crop}")
        return " | ".join(parts)

    def _followups(self) -> List[str]:
        return [
            "Do you want advice tailored to your field's soil type and irrigation method?",
            "Should I consider expected market price trends before harvest?",
            "Would you like pesticide advice aligned with IPM guidelines?",
        ]


def summarize_bullets(texts: List[str]) -> str:
    bullets = []
    for t in texts:
        bullets.append(f"- {t[:200]}...")
    if not bullets:
        return "I need more local data to answer reliably."
    return "\n".join(bullets)


def reasons_to_answer(messages: List[str]) -> str:
    if not messages:
        return "No specific rule-based insight found."
    return " ".join(messages)