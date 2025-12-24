"""FastAPI backend for serving Wikipedia category word frequencies."""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


def _ensure_repo_root_on_syspath() -> None:
    """Ensure the repository root is importable.

    This allows importing `category_wordfreq.py` when running the app via Uvicorn
    from within the `backend/` directory.
    """

    repo_root = Path(__file__).resolve().parents[1]
    repo_root_str = str(repo_root)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


_ensure_repo_root_on_syspath()

from category_wordfreq import get_category_counts


FrontendMetric = Literal["count", "freq"]

DEFAULT_TOP_N = 200
DEFAULT_MIN_COUNT = 1
DEFAULT_SLEEP_SECONDS = 0.0

DEFAULT_ALLOWED_ORIGINS = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


class WordItem(BaseModel):
    """A single word item displayed in the word cloud."""

    text: str
    value: float


class WordFreqResponse(BaseModel):
    """Response payload for `/api/wordfreq`."""

    category: str
    metric: FrontendMetric
    total_words: int
    items: list[WordItem]


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(title="wikipedia_analysis")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(DEFAULT_ALLOWED_ORIGINS),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


app = create_app()


def _sorted_rows(counts: Counter[str], *, min_count: int, top_n: int) -> list[tuple[str, int]]:
    rows = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    if min_count > 1:
        rows = [(word, count) for (word, count) in rows if count >= min_count]
    if top_n > 0:
        rows = rows[:top_n]
    return rows


def _build_items(
    rows: list[tuple[str, int]],
    *,
    metric: FrontendMetric,
    total_words: int,
) -> list[WordItem]:
    if metric == "freq":
        denom = float(total_words) if total_words else 1.0
        return [WordItem(text=word, value=float(count) / denom) for (word, count) in rows]
    return [WordItem(text=word, value=float(count)) for (word, count) in rows]


@app.get("/api/wordfreq", response_model=WordFreqResponse)
def api_wordfreq(
    category: str = Query(..., min_length=1),
    refresh: bool = False,
    sleep: float = Query(DEFAULT_SLEEP_SECONDS, ge=0.0),
    top: int = Query(DEFAULT_TOP_N, ge=0),
    metric: FrontendMetric = "count",
    min_count: int = Query(DEFAULT_MIN_COUNT, ge=1),
) -> WordFreqResponse:
    category = category.strip()
    if not category:
        raise HTTPException(status_code=400, detail="category is required")

    counts = get_category_counts(category, refresh=refresh, sleep=sleep)
    if not counts:
        raise HTTPException(status_code=404, detail="no pages or no words found for category")

    total_words = int(sum(counts.values()))
    rows = _sorted_rows(counts, min_count=min_count, top_n=top)
    items = _build_items(rows, metric=metric, total_words=total_words)

    return WordFreqResponse(
        category=category,
        metric=metric,
        total_words=total_words,
        items=items,
    )
