from __future__ import annotations
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pathlib import Path
import csv
from datetime import datetime, timedelta

from .config import RAINFALL_WINDOW_DAYS, RAINFALL_THRESHOLD_MM, HIGH_TEMP_C

@dataclass
class RuleResult:
    messages: List[str]
    confidence: float


def parse_weather(path: Path, district: Optional[str]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    try:
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if district and r.get("district", "").lower() != district.lower():
                    continue
                try:
                    rows.append({
                        "date": datetime.fromisoformat(r.get("date", "1970-01-01")),
                        "rain_mm": float(r.get("rain_mm", 0) or 0),
                        "tmax_c": float(r.get("tmax_c", 0) or 0),
                    })
                except Exception:
                    continue
    except Exception:
        return []
    return rows


def parse_soil(path: Path, district: Optional[str]) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                if district and r.get("district", "").lower() != district.lower():
                    continue
                whc = None
                try:
                    whc = float(r.get("whc_mm", "") or "")
                except Exception:
                    pass
                return {"whc_mm": whc, "soil_texture": r.get("soil_texture", "")}
    except Exception:
        return None
    return None


def when_to_irrigate(weather_rows: List[Dict[str, Any]], soil_row: Optional[Dict[str, Any]] = None) -> RuleResult:
    if not weather_rows:
        return RuleResult(["Insufficient recent weather data; default to field inspection for soil moisture."], 0.3)
    latest_date = max(r["date"] for r in weather_rows)
    window_start = latest_date - timedelta(days=RAINFALL_WINDOW_DAYS)
    recent = [r for r in weather_rows if r["date"] >= window_start]
    rain = sum(r["rain_mm"] for r in recent)
    tmax_vals = [r["tmax_c"] for r in recent if r.get("tmax_c") is not None]
    tmax = sum(tmax_vals) / len(tmax_vals) if tmax_vals else None

    msgs: List[str] = []
    conf = 0.5

    if rain >= RAINFALL_THRESHOLD_MM:
        msgs.append(f"Recent {RAINFALL_WINDOW_DAYS}-day rainfall {rain:.1f} mm >= {RAINFALL_THRESHOLD_MM} mm; irrigation can be deferred.")
        conf = 0.7
    else:
        if tmax is not None and tmax >= HIGH_TEMP_C:
            msgs.append(f"High temperatures (~{tmax:.0f}°C) with limited rain ({rain:.1f} mm): irrigate within 1-2 days if soil is dry.")
            conf = 0.65
        else:
            msgs.append(f"Limited rain ({rain:.1f} mm) recently; check soil moisture at root zone. If dry, irrigate in 2-3 days.")
            conf = 0.6

    if soil_row is not None:
        whc = soil_row.get("whc_mm")
        if isinstance(whc, (int, float)):
            if whc >= 160:
                msgs.append("Soil WHC is high; longer intervals between irrigations are acceptable.")
                conf += 0.05
            elif whc <= 100:
                msgs.append("Soil WHC is low; consider lighter but more frequent irrigations.")
                conf += 0.05

    return RuleResult(msgs, min(conf, 0.9))