"""Ekantipur scraper: entertainment listing and cartoon-of-the-day extraction."""

import json
import re
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import Locator, Page, TimeoutError as PlaywrightTimeoutError, sync_playwright

# Target site and output file (relative to current working directory when run).
EKANTIPUR_URL = "https://ekantipur.com"
CARTOON_URL = "https://ekantipur.com/cartoon"
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


def _normalize_whitespace(text: str) -> str:
    """Turn runs of whitespace/newlines into a single space for clean JSON titles."""
    return re.sub(r"\s+", " ", text).strip()


def _image_url_from_card(card: Locator, page_url: str) -> str | None:
    """
    Resolve the listing thumbnail from `div.category-image` inside the card.

    Prefer `img.loaded` (the site adds this class when the real asset is ready).
    If that node is not there yet, fall back to any `img` in the same container.
    Only `src` is read so we never surface article page URLs from surrounding anchors.
    """
    loaded = card.locator("div.category-image img.loaded")
    if loaded.count() > 0:
        target = loaded.first
    else:
        plain = card.locator("div.category-image img")
        if plain.count() == 0:
            return None
        target = plain.first

    raw = target.get_attribute("src")
    if not raw or not raw.strip():
        return None
    return urljoin(page_url, raw.strip())


def extract_entertainment_articles(page: Page) -> list[dict]:
    """
    Walk the first `.category-inner-wrapper` cards and build article dicts.

    Each card is expected to contain title (`h2 a`), image (`div.category-image img`),
    and optionally author (`.author-name`). Category is always the entertainment label.
    """
    # One locator for all cards; scope child queries with `.nth(i)` so each field
    # selector runs inside a single article only.
    cards = page.locator(".category-inner-wrapper")
    # Wait until at least one listing card is on screen (dynamic section).
    cards.first.wait_for(state="visible")

    # Thumbnails below the fold often lazy-load: scroll each card we will read into
    # view first, then pause briefly so `img.loaded` / `src` can populate.
    n_scroll = min(ARTICLE_LIMIT, cards.count())
    for i in range(n_scroll):
        cards.nth(i).scroll_into_view_if_needed()
    page.wait_for_timeout(800)

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
        # Thumbnail: real file from `img.loaded`, else any `img` under `div.category-image`.
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


def extract_cartoon_of_the_day(page: Page) -> dict:
    """
    Read the Cartoon of the Day block on `/cartoon`.

    Everything is scoped under `div.cartoon-wrapper` so we only touch the
    cartoon feature, not unrelated images elsewhere on the page.

    Returns a small dict suitable for `output.json` under `cartoon_of_the_day`.
    Missing fields use None so downstream code can branch safely.
    """
    # Start with a predictable shape for beginners consuming the JSON file.
    result: dict = {"title": None, "image_url": None, "author": None}

    # --- Wait for the section shell (layout exists before inner bits fill in) ---
    section = page.locator("div.cartoon-wrapper").first
    section.wait_for(state="visible")

    # --- Image: prefer the lazy-loaded node (`img.loaded`), fall back to any image ---
    # The site adds `.loaded` after the file is ready; if that never appears in time,
    # we still try a plain `img` so we do not return empty-handed on slow networks.
    img_loc = section.locator(".cartoon-image img.loaded")
    try:
        img_loc.first.wait_for(state="visible", timeout=20_000)
    except PlaywrightTimeoutError:
        img_loc = section.locator(".cartoon-image img")
        if img_loc.count() == 0:
            img_loc = None
        else:
            try:
                img_loc.first.wait_for(state="visible", timeout=10_000)
            except PlaywrightTimeoutError:
                img_loc = None

    if img_loc is not None and img_loc.count() > 0:
        raw_src = img_loc.first.get_attribute("src")
        if raw_src:
            result["image_url"] = urljoin(page.url, raw_src.strip())

    # --- Caption lives in `.cartoon-description`; the date is a child `div.date` ---
    desc = section.locator("div.cartoon-description")
    if desc.count() == 0:
        return result

    # `inner_text()` mirrors what a reader sees, including the date line.
    full_caption = desc.first.inner_text().strip()
    date_loc = desc.locator("div.date")
    date_text = (_text_or_none(date_loc) or "").strip()

    # Strip the date string once so the title is only the editorial caption.
    caption = full_caption
    if date_text:
        caption = caption.replace(date_text, "", 1).strip()
    caption = _normalize_whitespace(caption)

    # --- Author: try a byline node first (same pattern as other Kantipur pages) ---
    author = _text_or_none(section.locator(".author-name"))

    # If there is no `.author-name`, many strips encode "Title - Cartoonist" in text.
    title: str | None = caption or None
    if author is None and caption and " - " in caption:
        left, right = caption.rsplit(" - ", 1)
        left, right = left.strip(), right.strip()
        if left and right:
            title = left
            author = right

    result["title"] = title
    result["author"] = author
    return result


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

        # --- Entertainment listing (direct URL matches the live section) ---
        page.goto(EKANTIPUR_URL + "/entertainment", wait_until="networkidle")
        entertainment_news = extract_entertainment_articles(page)

        # --- Cartoon of the Day: dedicated page, separate extraction function ---
        page.goto(CARTOON_URL, wait_until="domcontentloaded")
        cartoon_of_the_day = extract_cartoon_of_the_day(page)

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
