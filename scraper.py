"""Ekantipur scraper entrypoint (skeleton — extraction not implemented yet)."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

# Target site and output file (relative to current working directory when run).
EKANTIPUR_URL = "https://ekantipur.com"
OUTPUT_PATH = Path("output.json")


def main() -> None:
    # --- Result containers (populate in a later extraction step) ---
    entertainment_news: list = []
    cartoon_of_the_day: dict = {}

    # --- Playwright lifecycle: start API, launch browser, always tear down ---
    playwright = sync_playwright().start()
    browser = None
    try:
        # --- Browser: visible Chromium window for local debugging ---
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()

        # --- Navigation: load homepage and settle background requests ---
        page.goto(EKANTIPUR_URL, wait_until="networkidle")

        # --- Extraction (TODO): parse DOM / API responses into the structures above ---
        # entertainment_news / cartoon_of_the_day intentionally left empty for now.

    finally:
        # --- Cleanup: close browser and stop Playwright even on errors ---
        if browser is not None:
            browser.close()
        playwright.stop()

    # --- Persist: write UTF-8 JSON with readable Unicode and indentation ---
    payload = {
        "entertainment_news": entertainment_news,
        "cartoon_of_the_day": cartoon_of_the_day,
    }
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
