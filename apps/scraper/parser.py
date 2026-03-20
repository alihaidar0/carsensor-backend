import logging
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup
from .translator import (
    translate_fuel_type,
    translate_transmission,
    translate_body_type,
    translate_drive_type,
    translate_color,
    translate_location,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://carsensor.net"
SEARCH_URL = "https://carsensor.net/usedcar/search.fcgi?BTYPE=U&"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ja,en;q=0.9",
}


def fetch_page(url: str) -> BeautifulSoup | None:
    try:
        with httpx.Client(headers=HEADERS, timeout=30, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, "lxml")
    except Exception as e:
        logger.error(f"Failed to fetch {url}: {e}")
        return None


def parse_price(text: str) -> float:
    if not text:
        return 0.0
    cleaned = text.replace(",", "").replace("万円", "").replace("円", "").strip()
    try:
        value = float(cleaned)
        if "万" in text:
            value *= 10000
        return value
    except ValueError:
        return 0.0


def parse_mileage(text: str) -> int:
    if not text:
        return 0
    cleaned = text.replace(",", "").replace("km", "").replace("万km", "").strip()
    try:
        value = float(cleaned)
        if "万" in text:
            value *= 10000
        return int(value)
    except ValueError:
        return 0


def parse_year(text: str) -> int:
    if not text:
        return 0
    import re
    match = re.search(r"(\d{4})", text)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d{2})", text)
    if match:
        year = int(match.group(1))
        return 2000 + year if year < 50 else 1900 + year
    return 0


def parse_listing_page(soup: BeautifulSoup) -> list[dict]:
    cars = []
    car_cards = soup.select("div.cassetteMain") or soup.select("div[class*='cassette']")

    for card in car_cards:
        try:
            car = parse_car_card(card)
            if car:
                cars.append(car)
        except Exception as e:
            logger.warning(f"Failed to parse car card: {e}")
            continue

    return cars


def parse_car_card(card) -> dict | None:
    try:
        link_tag = card.select_one("a[href*='/usedcar/']")
        if not link_tag:
            return None

        href = link_tag.get("href", "")
        url = href if href.startswith("http") else BASE_URL + href

        external_id = ""
        import re
        id_match = re.search(r"CS(\w+)", url)
        if id_match:
            external_id = id_match.group(0)
        else:
            external_id = url.split("/")[-2] if "/" in url else url[-20:]

        brand_tag = card.select_one(".carName .maker") or card.select_one("[class*='maker']")
        model_tag = card.select_one(".carName .car") or card.select_one("[class*='carName']")
        brand = brand_tag.get_text(strip=True) if brand_tag else ""
        model = model_tag.get_text(strip=True) if model_tag else ""

        if not brand and not model:
            title_tag = card.select_one("h3") or card.select_one(".carName")
            if title_tag:
                parts = title_tag.get_text(strip=True).split()
                brand = parts[0] if parts else ""
                model = " ".join(parts[1:]) if len(parts) > 1 else ""

        price_tag = card.select_one(".price") or card.select_one("[class*='price']")
        price_text = price_tag.get_text(strip=True) if price_tag else "0"
        price = parse_price(price_text)

        mileage_tag = card.select_one(".mileage") or card.select_one("[class*='mileage']")
        mileage_text = mileage_tag.get_text(strip=True) if mileage_tag else "0"
        mileage = parse_mileage(mileage_text)

        year_tag = card.select_one(".year") or card.select_one("[class*='year']")
        year_text = year_tag.get_text(strip=True) if year_tag else ""
        year = parse_year(year_text)

        img_tag = card.select_one("img")
        image_url = img_tag.get("src", "") or img_tag.get("data-src", "") if img_tag else ""

        specs = {}
        spec_items = card.select("li") or card.select("span[class*='spec']")
        for item in spec_items:
            text = item.get_text(strip=True)
            specs[text] = text

        raw_data = {
            "price_text": price_text,
            "mileage_text": mileage_text,
            "year_text": year_text,
            "specs": list(specs.keys()),
        }

        return {
            "external_id": external_id,
            "url": url,
            "brand": brand,
            "model": model,
            "year": year or 2000,
            "mileage": mileage,
            "price": price,
            "image_url": image_url,
            "image_urls": [image_url] if image_url else [],
            "raw_data": raw_data,
            "scraped_at": datetime.now(timezone.utc),
        }
    except Exception as e:
        logger.warning(f"Error parsing card: {e}")
        return None


def get_next_page_url(soup: BeautifulSoup, current_url: str) -> str | None:
    next_link = soup.select_one("a[class*='next']") or soup.select_one(".pager .next a")
    if next_link:
        href = next_link.get("href", "")
        if href:
            return href if href.startswith("http") else BASE_URL + href
    return None


def scrape_all_cars(max_pages: int = 50) -> list[dict]:
    all_cars = []
    url = SEARCH_URL
    page = 1

    while url and page <= max_pages:
        logger.info(f"Scraping page {page}: {url}")
        soup = fetch_page(url)
        if not soup:
            break

        cars = parse_listing_page(soup)
        if not cars:
            logger.info(f"No cars found on page {page}, stopping.")
            break

        all_cars.extend(cars)
        logger.info(f"Page {page}: found {len(cars)} cars (total: {len(all_cars)})")

        url = get_next_page_url(soup, url)
        page += 1

    return all_cars
