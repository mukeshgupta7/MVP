from __future__ import annotations
from typing import Optional, List, Dict, Any, Tuple
import httpx

DEFAULT_UA = "AgriAdvisor/0.1 (+https://example.invalid)"


def geocode_district(district: str, country: str = "India", timeout: float = 10.0) -> Optional[Tuple[float, float]]:
    query = f"{district}, {country}"
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"User-Agent": DEFAULT_UA}
    params = {"format": "json", "q": query, "limit": 1}
    try:
        with httpx.Client(timeout=timeout, headers=headers) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            data = r.json()
            if not data:
                return None
            lat = float(data[0]["lat"])  # type: ignore
            lon = float(data[0]["lon"])  # type: ignore
            return lat, lon
    except Exception:
        return None


def fetch_open_meteo(lat: float, lon: float, timeout: float = 10.0) -> Optional[List[Dict[str, Any]]]:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum,temperature_2m_max",
        "timezone": "auto",
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.get(url, params=params)
            r.raise_for_status()
            js = r.json()
            daily = js.get("daily", {})
            dates = daily.get("time", [])
            precip = daily.get("precipitation_sum", [])
            tmax = daily.get("temperature_2m_max", [])
            out: List[Dict[str, Any]] = []
            for i in range(min(len(dates), len(precip), len(tmax))):
                out.append({
                    "date": dates[i],
                    "rain_mm": float(precip[i]) if precip[i] is not None else 0.0,
                    "tmax_c": float(tmax[i]) if tmax[i] is not None else None,
                })
            return out
    except Exception:
        return None