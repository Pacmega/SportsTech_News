# Implementation Plan: Website Scraping Support

Goal: extend the bot to fetch articles from sites that have no RSS feed, using HTML scraping. The output must be the same `NewsArticle` dataclass so the rest of the pipeline (formatting, Telegram) is unaffected.

---

## Architecture

Introduce `src/web_scraper.py` alongside the existing `src/scraper.py`.

```
src/
  scraper.py         ← existing RSS scraper (unchanged)
  web_scraper.py     ← NEW: base class + per-site scrapers + orchestrator
  main.py            ← merge RSS + web results here
```

### Key design decisions

- **Abstract base class** `BaseSiteScraper`: each supported site gets its own subclass. Enforces a single method `fetch() -> list[NewsArticle]` so every scraper is plug-and-play.
- **`WebScraper` orchestrator**: mirrors `NewsScraper` — holds a registry of active scrapers, exposes `get_all_news()`, uses a shared `httpx.Client`.
- **Date handling**: many sites don't expose dates cleanly in HTML. Each site scraper is responsible for its own date parsing. If a date cannot be extracted, `published_at` is `None` and `_is_recent()` returns `False`, so the article is dropped — same behaviour as RSS.
- **Deduplication in `main.py`**: after merging RSS + web results, deduplicate on URL before sending.
- **`pages_to_parse.md`**: fill this file with the target sites (name + URL + notes on structure) as you add them, so the list of intended sources is tracked.

---

## Step-by-step plan

### Step 1 — Add dependencies

In `pyproject.toml`, add to `[project.dependencies]`:
```
"beautifulsoup4>=4.12.0",
"lxml>=5.0.0",
```

Run `uv sync` to update the lockfile.

---

### Step 2 — Create `src/web_scraper.py` with base class and orchestrator

Create `src/web_scraper.py` containing:

**`BaseSiteScraper` (abstract base class)**
```python
from abc import ABC, abstractmethod

class BaseSiteScraper(ABC):
    def __init__(self, client: httpx.Client, hours_lookback: int) -> None:
        self.client = client
        self.hours_lookback = hours_lookback

    @abstractmethod
    def fetch(self) -> list[NewsArticle]:
        """Fetch and return recent articles from the site."""
        ...

    def _is_recent(self, published_datetime: Optional[datetime]) -> bool:
        # same logic as NewsScraper._is_recent
        ...
```

**`WebScraper` orchestrator**
```python
class WebScraper:
    HOURS_LOOKBACK = 25

    def __init__(self, timeout: float = 10.0) -> None:
        self.client = httpx.Client(timeout=timeout)
        self._scrapers: list[BaseSiteScraper] = self._build_scrapers()

    def _build_scrapers(self) -> list[BaseSiteScraper]:
        # Instantiate all active site scrapers here
        return []

    def get_all_news(self) -> list[NewsArticle]:
        all_articles = []
        for scraper in self._scrapers:
            try:
                all_articles.extend(scraper.fetch())
            except Exception as e:
                logger.error(f"Error in {scraper.__class__.__name__}: {e}")
        all_articles.sort(key=lambda x: x.published_at or "", reverse=True)
        return all_articles

    def __enter__(self): return self
    def __exit__(self, *args): self.client.close()
```

---

### Step 3 — Implement the first site scraper

Pick a target site (fill `pages_to_parse.md` first). For each site:

1. Inspect the site's HTML in a browser (DevTools → Elements) and identify:
   - The container element that wraps each article listing
   - The tag/class holding the article title
   - The tag/class holding the article URL (`<a href>`)
   - Where/whether a date is exposed (a `<time datetime="">` attribute is easiest)
2. Write a subclass of `BaseSiteScraper` in `src/web_scraper.py`:

```python
class ExampleSiteScraper(BaseSiteScraper):
    URL = "https://example.com/news"
    SOURCE_NAME = "Example Site"

    def fetch(self) -> list[NewsArticle]:
        articles = []
        try:
            response = self.client.get(self.URL)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")

            for item in soup.select("article.post"):   # adjust selector
                title = item.select_one("h2.title").get_text(strip=True)
                url = item.select_one("a")["href"]
                time_el = item.select_one("time")
                published_dt = self._parse_date(time_el)

                if not self._is_recent(published_dt):
                    continue

                articles.append(NewsArticle(
                    title=title,
                    url=url,
                    source=self.SOURCE_NAME,
                    published_at=published_dt.isoformat() if published_dt else None,
                ))
        except httpx.RequestError as e:
            logger.error(f"Error fetching {self.SOURCE_NAME}: {e}")
        return articles

    def _parse_date(self, time_el) -> Optional[datetime]:
        if time_el and time_el.get("datetime"):
            try:
                return datetime.fromisoformat(time_el["datetime"]).astimezone(timezone.utc)
            except ValueError:
                pass
        return None
```

3. Register it in `WebScraper._build_scrapers()`.

Repeat for each new site.

---

### Step 4 — Wire into `main.py`

Update `main.py` to run both scrapers and deduplicate:

```python
from src.web_scraper import WebScraper

with NewsScraper() as rss_scraper:
    rss_articles = rss_scraper.get_all_news()

with WebScraper() as web_scraper:
    web_articles = web_scraper.get_all_news()

# Merge + deduplicate on URL
seen_urls: set[str] = set()
articles: list[NewsArticle] = []
for article in rss_articles + web_articles:
    if article.url not in seen_urls:
        seen_urls.add(article.url)
        articles.append(article)

# Re-sort after merge
articles.sort(key=lambda x: x.published_at or "", reverse=True)
```

---

### Step 5 — Add tests

Create `tests/test_web_scraper.py` covering:

- `WebScraper` initialises with an empty scraper list by default
- `WebScraper.get_all_news()` returns a list (smoke test)
- Per site scraper: mock `httpx.Client.get` to return a fixture HTML string, assert correct `NewsArticle` fields are extracted
- Per site scraper: articles older than `HOURS_LOOKBACK` are filtered out
- Per site scraper: graceful handling when HTTP request fails (returns empty list, no exception raised)
- Deduplication in `main.py`: duplicate URLs appear only once in merged output

Use `unittest.mock.patch` or `pytest-mock` for HTTP mocking. Keep fixture HTML minimal — only the tags the scraper actually reads.

---

### Step 6 — Update `pages_to_parse.md`

Document each configured site:
```
| Site | URL | Date selector | Notes |
|------|-----|---------------|-------|
| Example | https://... | time[datetime] | ISO 8601 in datetime attr |
```

This file is the source of truth for which sites are configured and how their HTML was structured at the time of writing (useful when a site redesigns).

---

## Checklist (tick off per session)

- [ ] Step 1: dependencies added and `uv.lock` updated
- [ ] Step 2: `src/web_scraper.py` created with base class + orchestrator
- [ ] Step 3: first site scraper implemented and registered
- [ ] Step 4: `main.py` updated with merged + deduplicated pipeline
- [ ] Step 5: tests written and passing
- [ ] Step 6: `pages_to_parse.md` filled in
- [ ] Each additional site: subclass added, registered, tested, documented in `pages_to_parse.md`

---

## Notes and gotchas

- **No date in HTML**: if a site doesn't expose a date at all, consider including the article unconditionally (set `published_at=None` and skip the recency filter for that scraper). Document this exception in `pages_to_parse.md`.
- **Relative URLs**: some sites use `/path` links — prepend the base domain.
- **JavaScript-rendered content**: `httpx` + BeautifulSoup only works for server-rendered HTML. If a site requires JS execution, a headless browser (Playwright) would be needed — treat that as a separate, later step.
- **Rate limiting / bot detection**: add a `User-Agent` header to the shared `httpx.Client` to reduce the chance of being blocked.
- **CSS selector maintenance**: site HTML changes break scrapers silently. If a scraper returns 0 articles consistently, check whether the selectors are still valid.
