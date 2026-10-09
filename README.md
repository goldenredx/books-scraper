# Books Scraper: Data Collection, Cleaning and Validation

A small pipeline that scrapes book data from [books.toscrape.com](https://books.toscrape.com), a public sandbox website built for scraping practice. It cleans and validates the data, removes duplicates, and exports it to CSV.

## Output

`books.csv` with columns: `title`, `price`, `rating`, `availability`, `url`

## Setup

```bash
pip install requests beautifulsoup4 pandas
python scraper.py
```

## Approach

1. **Fetch:** `requests` with a browser User-Agent, a 10s timeout and error handling. A failed request returns `None` instead of crashing.
2. **Parse:** `BeautifulSoup` with CSS selectors extracts title, price, rating, availability and URL from each book card. Missing fields become `None`.
3. **Paginate:** follows the "next" button until the last page (50 pages, 1000 books).
4. **Be polite:** a 1-second delay between requests, and only a site that explicitly permits scraping.
5. **Clean:** trim whitespace, convert price to float, map rating words ("One" to "Five") to 1-5, build absolute URLs.
6. **Validate:** bad rows are dropped and the failure counts are printed.
7. **Deduplicate:** by product URL.
8. **Export:** `pandas.to_csv`.

## Validation Checks

| Check | Rule |
|---|---|
| Null values | No row may have a missing field |
| Price | Must be greater than 0 |
| Rating | Must be between 1 and 5 |
| URL | Must start with `http` |
| Title | Must not be empty |
| Duplicates | One row per unique product URL |

## Project Structure

```
scraper.py
books.csv
requirements.txt
README.md
```

## Dividing the Work Among Team Members

| Role | Responsibility |
|---|---|
| Member 1 | Scraping: `fetch_page`, `parse_books`, `get_next_page`, `scrape_all` |
| Member 2 | Cleaning: `clean_data` (price, rating, URL and text normalization) |
| Member 3 | Validation and deduplication: `validate_data`, `remove_duplicates` |
| Team Lead | Defines the data schema up front, reviews every pull request, integrates modules in `main()`, runs final QA on the CSV (row count, sample check) |

**Workflow:**
- Each member works on their own Git branch and opens a pull request.
- The lead reviews and merges.
- Agreed schema: `title`, `price`, `rating`, `availability`, `url`.
- Each function takes and returns plain lists or DataFrames, so modules can be built and tested independently.

## Possible Improvements

- Retry with backoff on failed requests
- Logging instead of print statements
- Unit tests for the cleaning and validation functions
- Scrape category and description from each book page