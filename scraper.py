"""Ekantipur scraper: entertainment listing extraction."""

import json
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import Locator, Page, sync_playwright

# Target site and output file (relative to current working directory when run).
EKANTIPUR_URL = "https://ekantipur.com"
OUTPUT_PATH = Path("output.json")

# Fixed Nepali label for this section (site UI may vary; we normalize here).
ENTERTAINMENT_CATEGORY = "मनोरञ्जन"

# How many article cards to read from the entertainment listing.
ARTICLE_LIMIT = 5


def _text_or_none(loc: Locator) -> str | None:
    """Return stripped inner text, or None if the locator matches nothing."""
    if loc.count() == 0:
        return None
    text = loc.first.inner_text().strip()
    return text or None


def _image_url_from_card(card: Locator, page_url: str) -> str | None:
    """
    Resolve hero image URL from `.category-image a`.

    Prefer `img[src]` inside the anchor; otherwise use the anchor `href`
    (some cards link the image area directly).
    """
    anchor = card.locator(".category-image a")
    if anchor.count() == 0:
        return None

    img = anchor.locator("img")
    raw = None
    if img.count() > 0:
        raw = img.first.get_attribute("src")
    if not raw:
        raw = anchor.first.get_attribute("href")
    if not raw:
        return None
    return urljoin(page_url, raw.strip())


def extract_entertainment_articles(page: Page) -> list[dict]:
    """
    Walk the first `.category-inner-wrapper` cards and build article dicts.

    Each card is expected to contain title (`h2 a`), image (`.category-image a`),
    and optionally author (`.author-name`). Category is always the entertainment label.
    """
    # One locator for all cards; scope child queries with `.nth(i)` so each field
    # selector runs inside a single article only.
    cards = page.locator(".category-inner-wrapper")
    # Wait until at least one listing card is on screen (dynamic section).
    cards.first.wait_for(state="visible")

    articles: list[dict] = []
    n = min(ARTICLE_LIMIT, cards.count())
    for i in range(n):
        card = cards.nth(i)

        # Headline link text; empty string if the card markup differs.
        title_loc = card.locator("h2 a")
        title = (
            title_loc.first.inner_text().strip()
            if title_loc.count() > 0
            else ""
        )
        # Thumbnail: nested img preferred, else fall back to the anchor href.
        image_url = _image_url_from_card(card, page.url)
        # Byline is optional on some promos; locator count 0 → None.
        author = _text_or_none(card.locator(".author-name"))

        articles.append(
            {
                "title": title,
                "image_url": image_url,
                "category": ENTERTAINMENT_CATEGORY,
                "author": author,
            }
        )
    return articles


def main() -> None:
    entertainment_news: list = []
    cartoon_of_the_day: dict = {}

    playwright = sync_playwright().start()
    browser = None
    try:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()

        # --- Bootstrap: open homepage (networkidle gives a stable first paint) ---
        page.goto(EKANTIPUR_URL, wait_until="networkidle")

        page.goto(
        EKANTIPUR_URL + "/entertainment",
            wait_until="networkidle"
        )

        page.wait_for_timeout(2000)
        entertainment_news = extract_entertainment_articles(page)

        # --- Other sections (not built yet) ---
        cartoon_of_the_day = {}

    finally:
        if browser is not None:
            browser.close()
        playwright.stop()

    payload = {
        "entertainment_news": entertainment_news,
        "cartoon_of_the_day": cartoon_of_the_day,
    }
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
