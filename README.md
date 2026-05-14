# Ekantipur Scraper

A Playwright-based Python web scraper that extracts:

- Top 5 Entertainment news articles from Ekantipur
- Cartoon of the Day section

The scraper stores the extracted data in structured JSON format.

---

# Features

- Dynamic website scraping using Playwright
- Scoped CSS locator extraction
- Handles lazy-loaded images
- Safe fallback handling for missing fields
- UTF-8 JSON output for Nepali text support
- Modular and beginner-friendly code structure

---

# Tech Stack

- Python 3.12+
- Playwright
- uv (package/dependency management)

---

# Project Structure

```text
ekantipur-scraper/
│
├── scraper.py          # Main scraping logic
├── output.json         # Generated scraper output
├── prompts.txt         # AI prompts used during development
├── pyproject.toml      # Project dependencies
├── uv.lock             # Locked dependency versions
└── README.md
```

---

# Setup Instructions

## 1. Clone the Repository

```bash
git clone <your-repo-url>
cd ekantipur-scraper
```

---

## 2. Install uv

### Windows (PowerShell)

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify installation:

```bash
uv --version
```

---

## 3. Create Virtual Environment

```bash
uv venv
```

Activate it:

### Windows

```powershell
.venv\Scripts\activate
```

---

## 4. Install Dependencies

```bash
uv sync
```

---

## 5. Install Playwright Browser

```bash
playwright install chromium
```

---

# Running the Scraper

```bash
uv run python scraper.py
```

The scraper will:

1. Launch Chromium browser
2. Navigate to Ekantipur entertainment section
3. Extract top 5 entertainment articles
4. Navigate to cartoon section
5. Extract Cartoon of the Day data
6. Save everything into `output.json`

---

# Example Output

```json
{
  "entertainment_news": [
    {
      "title": "Sample title",
      "image_url": "https://example.com/image.jpg",
      "category": "मनोरञ्जन",
      "author": "Author Name"
    }
  ],
  "cartoon_of_the_day": {
    "title": "Sample cartoon title",
    "image_url": "https://example.com/cartoon.jpg",
    "author": null
  }
}
```

---

# Scraping Approach

## Entertainment Section

The scraper:

- Navigates directly to:
  `https://ekantipur.com/entertainment`
- Identifies repeating article containers
- Extracts:
  - title
  - image URL
  - category
  - author
- Handles lazy-loaded images using Playwright scrolling

---

## Cartoon of the Day

The scraper:

- Navigates directly to:
  `https://ekantipur.com/cartoon`
- Extracts:
  - cartoon caption/title
  - image URL
  - author (when available)
- Removes embedded date text from captions

---

# Notes

- The website contains dynamic and lazy-loaded content, which is why Playwright was used instead of static HTML scraping.
- Some fields may return `null` if the website does not expose the data consistently.
- The scraper uses only CSS locators (no XPath).

---

# Author

Navaras Shrestha