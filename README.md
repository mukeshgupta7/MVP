Agri Advisor (Offline-first)

- API and CLI for agriculture Q&A with retrieval + simple rules
- Offline-first using local CSV datasets and TF-IDF retrieval

Quickstart

1) Install deps

```
make setup
```

2) Ingest sample data and build index

```
make ingest
```

3) Run API

```
make run-api
```

4) Ask via CLI

```
make ask q="When should I irrigate?" district="Pune" crop="Wheat" lang=en
```

Data sources (samples with attribution)
- IMD (weather), Agmarknet (market prices), ICAR (crop calendars), Soil Health Card, Govt schemes portals. See `data/sources.md`.