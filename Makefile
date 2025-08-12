PYTHON?=python3
PIP?=pip3

.PHONY: setup run-api ask ingest test clean

setup:
	$(PIP) install --user -r requirements.txt --no-warn-script-location || $(PIP) install -r requirements.txt --break-system-packages --no-warn-script-location

run-api:
	$(PYTHON) -m uvicorn agri_advisor.server:app --host 0.0.0.0 --port 8000 --reload

ask:
	$(PYTHON) -m agri_advisor.cli --q "$(q)" --district "$(district)" --crop "$(crop)" --lang "$(lang)"

ingest:
	$(PYTHON) -m agri_advisor.data_ingestion --data-dir data/samples --db-path data/knowledge.db --rebuild-index

test:
	$(PYTHON) -m agri_advisor.cli --q "When should I irrigate?" --district "Pune" --crop "Wheat" --lang en

clean:
	rm -rf data/index