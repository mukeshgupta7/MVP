from __future__ import annotations
import typer
from rich.console import Console
from pathlib import Path

from .advice_engine import AgriAdvisor
from .config import SAMPLES_DIR

app = typer.Typer(add_completion=False)
console = Console()

advisor = AgriAdvisor(SAMPLES_DIR)

@app.command()
def ask(q: str = typer.Option(..., "--q", help="Your question"),
        district: str = typer.Option("", "--district"),
        crop: str = typer.Option("", "--crop"),
        lang: str = typer.Option("en", "--lang")):
    res = advisor.ask(q, district=district or None, crop=crop or None, lang=lang)
    console.rule("Answer")
    console.print(res.answer)
    console.rule("Confidence")
    console.print(f"{res.confidence:.2f}")
    console.rule("Reasons")
    for r in res.reasons:
        console.print(f"- {r}")
    console.rule("Citations")
    for c in res.citations:
        console.print(f"- {c.get('dataset')} ({c.get('source')})")

if __name__ == "__main__":
    app()