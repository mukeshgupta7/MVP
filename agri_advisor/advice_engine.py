from __future__ import annotations
from typing import Dict, Any, List
from dataclasses import dataclass
from pathlib import Path
import langid

from .retriever import LocalRetriever
from .rules import when_to_irrigate, parse_weather, parse_soil
from .config import INDEX_DIR
from . import external

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
            # Try public APIs first
            weather_rows = None
            if district:
                try:
                    # geocode and fetch open-meteo daily forecast
                    # We run async functions via httpx.run wrappers
                    loc = external.geocode_district(district)
                    if loc:
                        lat, lon = loc
                        daily = external.fetch_open_meteo(lat, lon)
                        if daily:
                            # Convert to rules-compatible rows using most recent 3 days (or next 3 days?)
                            # For irrigation, use past days would be ideal, but Open-Meteo daily returns forecast.
                            # We will use first 3 entries as near-term outlook.
                            from datetime import datetime
                            parsed = []
                            for row in daily[:3]:
                                parsed.append({
                                    "date": datetime.fromisoformat(row["date"]),
                                    "rain_mm": row.get("rain_mm", 0.0) or 0.0,
                                    "tmax_c": row.get("tmax_c"),
                                })
                            weather_rows = parsed
                            citations.append({"source": "Open-Meteo", "dataset": "weather_forecast", "url": "https://api.open-meteo.com/"})
                            citations.append({"source": "Nominatim OSM", "dataset": "geocoding", "url": "https://nominatim.org/"})
                except Exception:
                    weather_rows = None
            if not weather_rows:
                weather_rows = parse_weather(self.data_dir / "weather_sample.csv", district)
            s = parse_soil(self.data_dir / "soil_types.csv", district)
            rule = when_to_irrigate(weather_rows or [], s)
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