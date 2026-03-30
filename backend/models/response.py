from pydantic import BaseModel


class Internship(BaseModel):
    id: str
    title: str
    company: str
    location: str
    date_posted: str
    url: str
    source: str
    description: str
    salary: str | None = None
    duration: str | None = None
    remote: bool = False


class SearchResponse(BaseModel):
    results: list[Internship]
    total: int
    query: str
    duration_ms: float


class SuggestionResponse(BaseModel):
    suggestions: list[str]
