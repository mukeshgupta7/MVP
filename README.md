Agri Advisor (Offline-first + Public API support)

- API, CLI and Browser UI for agriculture Q&A with retrieval + simple rules
- Offline-first using local CSV datasets and pure-Python TF-IDF retrieval
- Optional public APIs for weather (Open-Meteo) and geocoding (Nominatim)

Quickstart

1) Install deps (or rely on break-system-packages)
```
make setup
```

2) Ingest sample data and build index
```
make ingest
```

3) Run API + UI
```
make run-api
# open http://localhost:8000/ui/
```

4) CLI
```
make ask q="When should I irrigate?" district="Pune" crop="Wheat" lang=en
```

Public APIs used
- Weather: Open-Meteo (`https://api.open-meteo.com/`) – terms: `https://open-meteo.com/en/features#terms`
- Geocoding: Nominatim OpenStreetMap (`https://nominatim.org/`) – usage policy: `https://operations.osmfoundation.org/policies/nominatim/`

Data sources (samples with attribution)
- IMD (weather), Agmarknet (market prices), ICAR (crop calendars), Soil Health Card, Govt schemes portals. See `data/sources.md`.

Notes
- If public APIs are unavailable, the engine falls back to the included CSV samples for irrigation heuristics.
- Be mindful of API usage policies and rate limits. Configure a custom User-Agent if deploying.