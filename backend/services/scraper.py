"""Scrape internships from multiple job sites concurrently."""

import asyncio
import hashlib
import json
import re
from datetime import datetime, timedelta
from urllib.parse import quote_plus, urlencode

import httpx
from bs4 import BeautifulSoup

from models.response import Internship


async def scrape_all(
    client: httpx.AsyncClient,
    query: str,
    location: str | None = None,
    remote_only: bool = False,
    date_filter: str | None = None,
) -> list[Internship]:
    """Run all scrapers concurrently and merge results."""
    tasks = [
        _scrape_linkedin(client, query, location),
        _scrape_linkedin_alt_queries(client, query, location),
        _scrape_themuse(client, query, location, page=0),
        _scrape_themuse(client, query, location, page=1),
        _scrape_themuse(client, query, location, page=2),
        _scrape_themuse(client, query, location, page=3),
        _scrape_themuse(client, query, location, page=4),
        _scrape_remoteok(client, query),
        _scrape_adzuna(client, query, location),
        _scrape_arbeitnow(client, query),
    ]
    gathered = await asyncio.gather(*tasks, return_exceptions=True)

    results: list[Internship] = []
    seen: set[str] = set()

    for result in gathered:
        if isinstance(result, list):
            for job in result:
                # Deduplicate by normalized title+company
                dedup_key = (job.title.lower().strip() + "|" + job.company.lower().strip())
                if dedup_key not in seen:
                    seen.add(dedup_key)
                    results.append(job)

    # Apply filters
    if remote_only:
        results = [r for r in results if r.remote]

    if date_filter and date_filter != "all":
        cutoff = _get_date_cutoff(date_filter)
        if cutoff:
            results = [r for r in results if _parse_date(r.date_posted) >= cutoff]

    if location:
        loc_lower = location.lower()
        results = [
            r for r in results
            if loc_lower in r.location.lower() or r.remote
        ]

    # Sort by date (newest first)
    results.sort(key=lambda r: _parse_date(r.date_posted), reverse=True)
    return results


def _make_id(val: str) -> str:
    return hashlib.md5(val.encode()).hexdigest()[:12]


def _get_date_cutoff(date_filter: str) -> datetime | None:
    now = datetime.now()
    if date_filter == "24h":
        return now - timedelta(days=1)
    elif date_filter == "7d":
        return now - timedelta(days=7)
    elif date_filter == "30d":
        return now - timedelta(days=30)
    return None


def _parse_date(date_str: str) -> datetime:
    """Parse date string to a naive datetime (no timezone) for consistent sorting."""
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        # Strip timezone info for consistent comparison
        return dt.replace(tzinfo=None)
    except (ValueError, TypeError):
        for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%b %d, %Y"]:
            try:
                return datetime.strptime(date_str, fmt)
            except (ValueError, TypeError):
                continue
        return datetime.min


def _relative_date_to_iso(text: str) -> str:
    """Convert relative dates like '3 days ago' to ISO format."""
    text = text.lower().strip()
    now = datetime.now()

    if not text:
        return now.isoformat()
    if "just" in text or "now" in text or "today" in text:
        return now.isoformat()
    if "yesterday" in text:
        return (now - timedelta(days=1)).isoformat()

    match = re.search(r"(\d+)\s*(minute|hour|day|week|month)", text)
    if match:
        num = int(match.group(1))
        unit = match.group(2)
        if "minute" in unit:
            return (now - timedelta(minutes=num)).isoformat()
        elif "hour" in unit:
            return (now - timedelta(hours=num)).isoformat()
        elif "day" in unit:
            return (now - timedelta(days=num)).isoformat()
        elif "week" in unit:
            return (now - timedelta(weeks=num)).isoformat()
        elif "month" in unit:
            return (now - timedelta(days=num * 30)).isoformat()

    return now.isoformat()


def _detect_remote(text: str) -> bool:
    return any(kw in text.lower() for kw in ["remote", "work from home", "wfh", "hybrid", "anywhere"])


# ---------------------------------------------------------------------------
# LinkedIn (public search — takes ALL cards from a single page, ~60)
# ---------------------------------------------------------------------------

async def _scrape_linkedin(
    client: httpx.AsyncClient,
    query: str,
    location: str | None,
) -> list[Internship]:
    results: list[Internship] = []
    search_query = f"{query} intern"
    url = f"https://www.linkedin.com/jobs/search?keywords={quote_plus(search_query)}&f_E=1"
    if location:
        url += f"&location={quote_plus(location)}"

    try:
        resp = await client.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        job_cards = soup.select("div.base-card, li.result-card, div.job-search-card")

        for card in job_cards:
            title_el = card.select_one("h3.base-search-card__title, h3")
            company_el = card.select_one("h4.base-search-card__subtitle, h4, a.hidden-nested-link")
            location_el = card.select_one("span.job-search-card__location, span.base-search-card__metadata")
            date_el = card.select_one("time")
            link_el = card.select_one("a.base-card__full-link, a[href*='/jobs/']")

            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            company = company_el.get_text(strip=True) if company_el else "Unknown"
            loc_text = location_el.get_text(strip=True) if location_el else ""
            date_posted = date_el.get("datetime", "") if date_el else ""
            if not date_posted and date_el:
                date_posted = _relative_date_to_iso(date_el.get_text(strip=True))
            href = link_el.get("href", "") if link_el else ""

            results.append(Internship(
                id=_make_id(href or title + company),
                title=title,
                company=company,
                location=loc_text or "Not specified",
                date_posted=date_posted or datetime.now().isoformat(),
                url=href or url,
                source="LinkedIn",
                description=f"{title} position at {company}",
                remote=_detect_remote(title + loc_text),
            ))
    except Exception:
        pass

    return results


# ---------------------------------------------------------------------------
# LinkedIn alt queries — broaden the search with related terms
# ---------------------------------------------------------------------------

async def _scrape_linkedin_alt_queries(
    client: httpx.AsyncClient,
    query: str,
    location: str | None,
) -> list[Internship]:
    """Search LinkedIn with broader/related query terms to get more results."""
    results: list[Internship] = []

    # Generate related queries
    q_lower = query.lower()
    alt_queries = []

    if "full stack" in q_lower or "fullstack" in q_lower:
        alt_queries = ["frontend developer intern", "backend developer intern", "web developer intern"]
    elif "software" in q_lower:
        alt_queries = ["developer intern", "programming intern", "engineering intern"]
    elif "data science" in q_lower or "data analyst" in q_lower:
        alt_queries = ["machine learning intern", "analytics intern", "business intelligence intern"]
    elif "marketing" in q_lower:
        alt_queries = ["digital marketing intern", "growth intern", "content intern"]
    elif "design" in q_lower:
        alt_queries = ["UX intern", "UI intern", "product design intern"]
    else:
        # Generic broadening: just add "internship" variant
        alt_queries = [f"{query} internship", f"{query} entry level"]

    async def _fetch_one(alt_q: str) -> list[Internship]:
        inner: list[Internship] = []
        url = f"https://www.linkedin.com/jobs/search?keywords={quote_plus(alt_q)}&f_E=1"
        if location:
            url += f"&location={quote_plus(location)}"
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")
            cards = soup.select("div.base-card, li.result-card, div.job-search-card")
            for card in cards:
                title_el = card.select_one("h3.base-search-card__title, h3")
                company_el = card.select_one("h4.base-search-card__subtitle, h4, a.hidden-nested-link")
                location_el = card.select_one("span.job-search-card__location, span.base-search-card__metadata")
                date_el = card.select_one("time")
                link_el = card.select_one("a.base-card__full-link, a[href*='/jobs/']")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                loc_text = location_el.get_text(strip=True) if location_el else ""
                date_posted = date_el.get("datetime", "") if date_el else ""
                if not date_posted and date_el:
                    date_posted = _relative_date_to_iso(date_el.get_text(strip=True))
                href = link_el.get("href", "") if link_el else ""
                inner.append(Internship(
                    id=_make_id(href or title + company),
                    title=title,
                    company=company,
                    location=loc_text or "Not specified",
                    date_posted=date_posted or datetime.now().isoformat(),
                    url=href or url,
                    source="LinkedIn",
                    description=f"{title} position at {company}",
                    remote=_detect_remote(title + loc_text),
                ))
        except Exception:
            pass
        return inner

    sub_tasks = [_fetch_one(q) for q in alt_queries[:3]]
    gathered = await asyncio.gather(*sub_tasks, return_exceptions=True)
    for res in gathered:
        if isinstance(res, list):
            results.extend(res)

    return results


# ---------------------------------------------------------------------------
# RemoteOK (JSON API — remote-first jobs)
# ---------------------------------------------------------------------------

async def _scrape_remoteok(
    client: httpx.AsyncClient,
    query: str,
) -> list[Internship]:
    results: list[Internship] = []

    # Try multiple tag variations
    tag_variants = [
        query.lower().replace(" ", "-"),
        query.lower().split()[0] if query.split() else query.lower(),
    ]

    for tags in tag_variants:
        url = f"https://remoteok.com/api?tags={tags}&api=1"
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()
            jobs = data[1:] if isinstance(data, list) and len(data) > 1 else []

            for job in jobs[:50]:
                title = job.get("position", "")
                company = job.get("company", "Unknown")
                loc_text = job.get("location", "Remote")
                date_posted = job.get("date", "")
                job_url = job.get("url", "")
                description = job.get("description", "")
                salary_min = job.get("salary_min")
                salary_max = job.get("salary_max")

                if job_url and not job_url.startswith("http"):
                    job_url = f"https://remoteok.com{job_url}"

                salary = None
                if salary_min and salary_max:
                    salary = f"${int(salary_min):,} - ${int(salary_max):,}"

                if description:
                    desc_soup = BeautifulSoup(description, "lxml")
                    description = desc_soup.get_text(" ", strip=True)[:200]

                if title:
                    results.append(Internship(
                        id=_make_id(job_url or title + company),
                        title=title,
                        company=company,
                        location=loc_text if loc_text else "Remote",
                        date_posted=date_posted or datetime.now().isoformat(),
                        url=job_url or "https://remoteok.com",
                        source="RemoteOK",
                        description=description or f"{title} at {company}",
                        salary=salary,
                        remote=True,
                    ))
        except Exception:
            pass

    return results


# ---------------------------------------------------------------------------
# Adzuna (free public API — no key needed for basic search)
# ---------------------------------------------------------------------------

async def _scrape_adzuna(
    client: httpx.AsyncClient,
    query: str,
    location: str | None,
) -> list[Internship]:
    """Scrape Adzuna job search results page."""
    results: list[Internship] = []
    search_query = f"{query} intern"
    country = "us"

    for page in range(1, 4):  # 3 pages
        url = f"https://www.adzuna.com/search?q={quote_plus(search_query)}&p={page}"
        if location:
            url += f"&w={quote_plus(location)}"

        try:
            resp = await client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "lxml")

            job_cards = soup.select("div.ui-job-card, article[data-aid], div[class*='ResultCard']")

            for card in job_cards:
                title_el = card.select_one("h2 a, a[data-aid='jobTitle'], h2[data-aid='jobTitle'] a")
                company_el = card.select_one("div[data-aid='companyName'], span.ui-job-card__company, p.ui-job-card__company")
                location_el = card.select_one("span[data-aid='jobLocation'], span.ui-job-card__location")
                date_el = card.select_one("time, span[data-aid='date'], span.ui-job-card__date")
                snippet_el = card.select_one("p.ui-job-card__description, span[data-aid='jobDescription']")

                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                company = company_el.get_text(strip=True) if company_el else "Unknown"
                loc_text = location_el.get_text(strip=True) if location_el else ""
                date_text = date_el.get_text(strip=True) if date_el else ""
                description = snippet_el.get_text(strip=True)[:200] if snippet_el else ""
                href = title_el.get("href", "")

                if href and not href.startswith("http"):
                    href = f"https://www.adzuna.com{href}"

                results.append(Internship(
                    id=_make_id(href or title + company),
                    title=title,
                    company=company,
                    location=loc_text or "Not specified",
                    date_posted=_relative_date_to_iso(date_text),
                    url=href or url,
                    source="Adzuna",
                    description=description or f"{title} at {company}",
                    remote=_detect_remote(title + loc_text + description),
                ))
        except Exception:
            pass

    return results


# ---------------------------------------------------------------------------
# Arbeitnow (free JSON API — tech/remote jobs)
# ---------------------------------------------------------------------------

async def _scrape_arbeitnow(
    client: httpx.AsyncClient,
    query: str,
) -> list[Internship]:
    """Arbeitnow has a free JSON API."""
    results: list[Internship] = []
    url = f"https://www.arbeitnow.com/api/job-board-api"

    try:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
        jobs = data.get("data", [])
        q_words = query.lower().split()

        for job in jobs:
            title = job.get("title", "")
            title_lower = title.lower()
            # Filter: must contain "intern" OR match query words
            if not ("intern" in title_lower or any(w in title_lower for w in q_words)):
                continue

            company = job.get("company_name", "Unknown")
            loc_text = job.get("location", "")
            date_posted = job.get("created_at", "")
            job_url = job.get("url", "")
            description = job.get("description", "")
            is_remote = job.get("remote", False)
            tags = job.get("tags", [])

            if description:
                desc_soup = BeautifulSoup(description, "lxml")
                description = desc_soup.get_text(" ", strip=True)[:200]

            results.append(Internship(
                id=_make_id(job_url or title + company),
                title=title,
                company=company,
                location=loc_text if loc_text else ("Remote" if is_remote else "Not specified"),
                date_posted=date_posted or datetime.now().isoformat(),
                url=job_url or "https://www.arbeitnow.com",
                source="Arbeitnow",
                description=description or f"{title} at {company}",
                remote=is_remote or _detect_remote(title + loc_text),
            ))
    except Exception:
        pass

    return results


# ---------------------------------------------------------------------------
# TheMuse (free JSON API — thousands of internships)
# ---------------------------------------------------------------------------

async def _scrape_themuse(
    client: httpx.AsyncClient,
    query: str,
    location: str | None,
    page: int = 0,
) -> list[Internship]:
    """TheMuse has a free public API with internship-level filtering."""
    results: list[Internship] = []
    url = f"https://www.themuse.com/api/public/jobs?level=Internship&page={page}&descending=true"

    try:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
        jobs = data.get("results", [])
        q_words = query.lower().split()

        for job in jobs:
            title = job.get("name", "")
            company_data = job.get("company", {})
            company = company_data.get("name", "Unknown")
            locations = job.get("locations", [])
            loc_names = [loc.get("name", "") for loc in locations]
            loc_text = ", ".join(loc_names) if loc_names else ""
            pub_date = job.get("publication_date", "")
            description_html = job.get("contents", "")
            job_url = f"https://www.themuse.com/jobs/{job.get('id', '')}" if job.get("id") else ""
            categories = [c.get("name", "").lower() for c in job.get("categories", [])]
            job_levels = [l.get("name", "").lower() for l in job.get("levels", [])]

            # Filter for relevance: title or category must match query words
            title_lower = title.lower()
            combined = title_lower + " " + " ".join(categories)
            if not any(w in combined for w in q_words):
                continue

            if description_html:
                desc_soup = BeautifulSoup(description_html, "lxml")
                description = desc_soup.get_text(" ", strip=True)[:200]
            else:
                description = f"{title} at {company}"

            is_remote = _detect_remote(title + loc_text) or "flexible / remote" in loc_text.lower()

            # Parse date
            date_posted = ""
            if pub_date:
                try:
                    dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                    date_posted = dt.isoformat()
                except ValueError:
                    date_posted = pub_date

            results.append(Internship(
                id=_make_id(job_url or title + company),
                title=title,
                company=company,
                location=loc_text or "Not specified",
                date_posted=date_posted or datetime.now().isoformat(),
                url=job_url or "https://www.themuse.com",
                source="TheMuse",
                description=description,
                remote=is_remote,
            ))
    except Exception:
        pass

    return results
