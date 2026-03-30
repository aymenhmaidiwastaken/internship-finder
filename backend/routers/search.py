import time

from fastapi import APIRouter, Query, Request

from models.response import SearchResponse, SuggestionResponse
from services.suggestions import get_suggestions
from services.scraper import scrape_all

router = APIRouter()


@router.get("/suggestions", response_model=SuggestionResponse)
async def suggestions(
    q: str = Query("", min_length=0),
    locale: str = Query("en"),
):
    return SuggestionResponse(suggestions=get_suggestions(q, locale=locale))


@router.get("/search", response_model=SearchResponse)
async def search(
    request: Request,
    query: str = Query(..., min_length=1),
    location: str | None = Query(None),
    remote_only: bool = Query(False),
    date_filter: str | None = Query(None),
    page: int = Query(1, ge=1),
):
    client = request.app.state.http_client
    start = time.perf_counter()

    results = await scrape_all(
        client=client,
        query=query,
        location=location,
        remote_only=remote_only,
        date_filter=date_filter,
    )

    duration_ms = (time.perf_counter() - start) * 1000

    # Paginate
    per_page = 50
    offset = (page - 1) * per_page
    page_results = results[offset : offset + per_page]

    return SearchResponse(
        results=page_results,
        total=len(results),
        query=query,
        duration_ms=round(duration_ms, 1),
    )
