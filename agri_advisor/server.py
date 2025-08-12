from __future__ import annotations
from fastapi import FastAPI
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.staticfiles import StaticFiles
from pathlib import Path

from .data_models import AskRequest, Answer
from .advice_engine import AgriAdvisor
from .config import SAMPLES_DIR

app = FastAPI(title="Agri Advisor", version="0.2.0")

advisor = AgriAdvisor(SAMPLES_DIR)

@app.post("/ask", response_model=Answer)
async def ask(req: AskRequest):
    res = advisor.ask(req.question, district=req.district, crop=req.crop, lang=req.lang or "en")
    return JSONResponse(
        content={
            "answer": res.answer,
            "confidence": res.confidence,
            "reasons": res.reasons,
            "citations": res.citations,
            "followups": res.followups,
            "debug": res.debug,
        }
    )

@app.get("/")
async def root():
    return RedirectResponse(url="/ui/")

# Mount static UI
static_dir = Path(__file__).resolve().parent / "static"
app.mount("/ui", StaticFiles(directory=static_dir, html=True), name="ui")