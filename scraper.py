import time
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

START_URL = "https://books.toscrape.com/catalogue/page-1.html"
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
OUTPUT_PATH = "books.csv"


def fetch_page(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()  # Throws error for 404, 500, etc.
        response.encoding = "utf-8"  # Avoids the "Â£" glitch
        return response.text
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return None


def parse_books(html, page_url):
    """Parse one listing page. page_url is used to build absolute book URLs."""
    soup = BeautifulSoup(html, "html.parser")
    books = []

    for card in soup.select("article.product_pod"):
        title_tag = card.select_one("h3 a")
        price_tag = card.select_one("p.price_color")
        rating_tag = card.select_one("p.star-rating")
        availability_tag = card.select_one("p.availability")

        title = title_tag.get("title") if title_tag else None
        href = title_tag.get("href") if title_tag else None
        full_url = urljoin(page_url, href) if href else None
        price = price_tag.text.strip() if price_tag else None

        rating = None
        if rating_tag and len(rating_tag.get("class", [])) > 1:
            rating = rating_tag["class"][1]

        availability = availability_tag.text.strip() if availability_tag else None

        books.append({
            "title": title,
            "price": price,
            "rating": rating,
            "availability": availability,
            "url": full_url,
        })

    return books


def get_next_page(html):
    soup = BeautifulSoup(html, "html.parser")
    next_btn = soup.select_one("li.next a")
    return next_btn["href"] if next_btn else None


def scrape_all():
    all_books = []
    url = START_URL
    page = 1
    while url:
        html = fetch_page(url)
        if html is None:
            break
        books = parse_books(html, url)
        all_books.extend(books)
        print(f"Page {page}: {len(books)} books")
        next_href = get_next_page(html)
        url = urljoin(url, next_href) if next_href else None
        page += 1
        time.sleep(1) # to avoid rate limiting or being blocked by the server
    return all_books


def clean_data(df):
    df = df.copy()
    df["title"] = df["title"].str.strip()
    df["availability"] = df["availability"].str.strip()
    # Invalid prices become NaN so validate_data can catch them
    df["price"] = pd.to_numeric(df["price"].str.replace(r"[^\d.]", "", regex=True), errors="coerce")
    df["rating"] = df["rating"].map(RATING_MAP)
    return df


def validate_data(df):
    checks = {
        "null values": df.isnull().any(axis=1),
        "price <= 0": df["price"] <= 0,
        "rating not in 1-5": ~df["rating"].between(1, 5),
        "invalid url": ~df["url"].fillna("").str.startswith("http"),
        "empty title": df["title"].fillna("").str.len() == 0,
    }
    for name, mask in checks.items():
        print(f"{name}: {mask.sum()} failed")
    bad_rows = pd.concat(checks.values(), axis=1).any(axis=1)
    return df[~bad_rows]


def remove_duplicates(df):
    before = len(df)
    df = df.drop_duplicates(subset="url")
    print(f"Duplicates removed: {before - len(df)}")
    return df


def export_csv(df, path=OUTPUT_PATH):
    df.to_csv(path, index=False)
    print(f"Saved {len(df)} rows to {path}")


def main():
    raw = scrape_all()
    if not raw:
        print("No data scraped. Exiting.")
        return

    df = pd.DataFrame(raw)
    print(f"Scraped rows: {len(df)}")

    df = clean_data(df)
    df = validate_data(df)
    df = remove_duplicates(df)
    export_csv(df)


if __name__ == "__main__":
    main()