import logging
import re
import time
import random
from datetime import datetime, timezone
from typing import Optional

from bs4 import BeautifulSoup, Tag
from curl_cffi import requests as cffi_requests

from .translator import (
    translate_body_type,
    translate_color,
    translate_drive_type,
    translate_fuel_type,
    translate_location,
    translate_transmission,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://www.carsensor.net"
SEARCH_URL = "https://www.carsensor.net/usedcar/search.php?AR=0&SKIND=1"

_CHROME_HEADERS: dict[str, str] = {
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;"
        "q=0.8,application/signed-exchange;v=b3;q=0.7"
    ),
    "Accept-Language": "ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "sec-ch-ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "Cache-Control": "max-age=0",
}

_MIN_DELAY_SECONDS: float = 2.0
_MAX_DELAY_SECONDS: float = 5.0


def _build_session() -> cffi_requests.Session:
    """
    Build a curl_cffi Session impersonating Chrome 124 at the TLS layer.

    curl_cffi replicates Chrome's exact TLS ClientHello — cipher suite order,
    elliptic curves, ALPN extensions, and GREASE values — defeating JA3/JA4
    fingerprinting which is the primary bot-detection mechanism on Japanese
    automotive sites.
    """
    session = cffi_requests.Session(impersonate="chrome124")
    session.headers.update(_CHROME_HEADERS)
    return session


def _warm_up_session(session: cffi_requests.Session) -> bool:
    """
    Visit the homepage before scraping search results.

    Real users land on the homepage first. Cold direct requests to search
    endpoints are a strong bot signal. This warm-up establishes a valid
    session cookie and populates the Referer chain.
    """
    try:
        resp = session.get(BASE_URL, timeout=20, allow_redirects=True)
        resp.raise_for_status()
        logger.info("Session warm-up successful.")
        time.sleep(random.uniform(1.5, 3.0))
        return True
    except Exception as exc:
        logger.warning(f"Session warm-up failed (non-fatal): {exc}")
        return False


def fetch_page(
    url: str,
    session: cffi_requests.Session,
    retries: int = 3,
) -> Optional[BeautifulSoup]:
    """
    Fetch a single page with exponential backoff retry logic.

    Args:
        url:     The absolute URL to fetch.
        session: A warm curl_cffi Session shared across all pages so
                 cookies persist and Referer headers are consistent.
        retries: Number of attempts before giving up.

    Returns:
        Parsed BeautifulSoup tree, or None if all retries failed.
    """
    for attempt in range(1, retries + 1):
        try:
            session.headers.update({"Referer": SEARCH_URL})
            response = session.get(url, timeout=30, allow_redirects=True)
            response.raise_for_status()
            logger.debug(f"Fetched {url} [HTTP {response.status_code}] (attempt {attempt})")
            return BeautifulSoup(response.content, "lxml")
        except cffi_requests.RequestsError as exc:
            logger.warning(f"Network error fetching {url} (attempt {attempt}/{retries}): {exc}")
        except Exception as exc:
            status = getattr(getattr(exc, "response", None), "status_code", "?")
            logger.warning(f"HTTP {status} fetching {url} (attempt {attempt}/{retries}): {exc}")

        if attempt < retries:
            backoff = (2 ** (attempt + 1)) + random.uniform(-1.0, 1.0)
            logger.info(f"Retrying in {backoff:.1f}s...")
            time.sleep(backoff)

    logger.error(f"Failed to fetch {url} after {retries} attempts.")
    return None


# ---------------------------------------------------------------------------
# Value parsers
# ---------------------------------------------------------------------------

def parse_price(main: str, sub: str) -> float:
    """
    Parse split price spans into a float JPY value.

    The real HTML splits price into two spans:
        <span class="totalPrice__mainPriceNum">125</span>
        <span class="totalPrice__subPriceNum">.9</span>
    Combined: "125.9" → 125.9 × 10,000 = 1,259,000 JPY
    """
    try:
        combined = (main.strip() + sub.strip()).replace(",", "")
        return float(combined) * 10_000
    except ValueError:
        return 0.0


def parse_mileage(text: str) -> int:
    """
    Parse mileage from specList__data text.

    Examples:
        "9 km"    → 9
        "3.2万km"  → 32000
        "10万km"   → 100000
    """
    if not text:
        return 0
    cleaned = text.replace(",", "").replace("km", "").replace("Km", "").strip()
    try:
        value = float(cleaned)
        if "万" in text:
            value *= 10_000
        return int(value)
    except ValueError:
        return 0


def parse_year(text: str) -> int:
    """
    Extract 4-digit year from specList__data text.

    Examples:
        "2026 (R08)" → 2026
        "2019(H31)"  → 2019
    """
    if not text:
        return 0
    match = re.search(r"(\d{4})", text)
    return int(match.group(1)) if match else 0


def _get_text(tag: Optional[Tag]) -> str:
    """Safe get_text that returns empty string for None tags."""
    return tag.get_text(strip=True) if tag else ""


def _extract_image_url(card: Tag) -> str:
    """
    Extract the car image URL from the lazy-load <script> block.

    The real HTML injects images via document.write() with a
    data-original attribute containing the actual CDN URL:
        data-original="//ccsrpcma.carsensor.net/CSphoto/..."

    Falls back to <noscript> > <img src> if script block is absent.
    """
    script_tag = card.select_one("div.cassetteMain__mainImg script")
    if script_tag and script_tag.string:
        match = re.search(r'data-original="([^"]+)"', script_tag.string)
        if match:
            url = match.group(1)
            return url if url.startswith("http") else "https:" + url

    noscript = card.select_one("div.cassetteMain__mainImg noscript")
    if noscript:
        img = BeautifulSoup(noscript.string or "", "lxml").find("img")
        if img:
            src = img.get("src", "")
            return src if src.startswith("http") else "https:" + src

    return ""


def _extract_specs(card: Tag) -> dict[str, str]:
    """
    Extract all spec key→value pairs from dl.specList.

    Real HTML structure (confirmed via DevTools, March 2026):
        <div class="specList__detailBox">
            <dt class="specList__title">年式</dt>
            <dd class="specList__data">
                <span class="specList__emphasisData">2026</span>
                <span class="specList__jpYear">(R08)</span>
            </dd>
        </div>

    All classes use BEM double-underscore (__), not single underscore.
    """
    specs: dict[str, str] = {}
    for box in card.select("div.specList__detailBox"):
        dt = box.select_one("dt.specList__title")
        dd = box.select_one("dd.specList__data")
        if dt and dd:
            key = dt.get_text(strip=True)
            val = dd.get_text(separator=" ", strip=True)
            specs[key] = val
    return specs


def parse_car_card(card: Tag) -> Optional[dict]:
    """
    Parse a single cassetteWrap card into a structured dict.

    DOM structure confirmed via DevTools inspection, March 2026:

    div.cassetteWrap.js-mainCassette
      └─ div.cassette.js_listTableCassette  [id="AU6767037010_cas"]
           └─ div.cassetteMain
                ├─ div.cassetteMain__carImgContainer
                │    ├─ div.cassetteMain__mainImg > a > script  (lazy image)
                │    └─ ul.carBodyInfoList > li.carBodyInfoList__item (body/color)
                └─ div.cassetteMain__carInfoContainer
                     ├─ div.cassetteMain__label  (badge icons)
                     ├─ p  (brand: "日産" — plain <p>, no class)
                     ├─ h3.cassetteMain__title > a  (model title + URL)
                     └─ div.cassetteMain__detailInfoBlock
                          ├─ div.cassetteMain__priceInfo
                          │    └─ div.totalPrice
                          │         ├─ span.totalPrice__mainPriceNum ("125")
                          │         └─ span.totalPrice__subPriceNum  (".9")
                          └─ div.cassetteMain__specInfo
                               └─ dl.specList
                                    └─ div.specList__detailBox (×N)
                                         ├─ dt.specList__title
                                         └─ dd.specList__data
    """
    try:
        # ── External ID ────────────────────────────────────────────────────
        cassette_div = card.select_one("div.cassette")
        external_id: str = ""
        if cassette_div:
            raw_id: str = cassette_div.get("id", "")
            external_id = raw_id.replace("_cas", "").strip()
        if not external_id and cassette_div:
            external_id = cassette_div.get("data-bknnum", "")

        # ── URL ────────────────────────────────────────────────────────────
        link_tag = card.select_one("h3.cassetteMain__title a")
        if not link_tag:
            return None
        href: str = link_tag.get("href", "")
        url: str = href if href.startswith("http") else BASE_URL + href

        if not external_id:
            id_match = re.search(r"/detail/([^/]+)/", url)
            external_id = id_match.group(1) if id_match else url.split("/")[-2]

        # ── Brand ──────────────────────────────────────────────────────────
        # Plain <p> tag directly inside cassetteMain__carInfoContainer,
        # between the label div and the h3. No class. Short text (e.g. "日産").
        info_container = card.select_one("div.cassetteMain__carInfoContainer")
        brand: str = ""
        if info_container:
            for p in info_container.find_all("p", recursive=False):
                text = p.get_text(strip=True)
                if text and len(text) <= 20 and "保証" not in text:
                    brand = text
                    break

        # ── Model ──────────────────────────────────────────────────────────
        model: str = _get_text(link_tag)

        if not brand and not model:
            return None

        # ── Price ──────────────────────────────────────────────────────────
        main_num: str = _get_text(card.select_one("span.totalPrice__mainPriceNum"))
        sub_num: str = _get_text(card.select_one("span.totalPrice__subPriceNum"))
        price: float = parse_price(main_num, sub_num)
        price_text: str = f"{main_num}{sub_num}万円"

        # ── Specs ──────────────────────────────────────────────────────────
        specs = _extract_specs(card)

        year_text: str = specs.get("年式", "")
        year: int = parse_year(year_text)

        mileage_text: str = specs.get("走行距離", "")
        mileage: int = parse_mileage(mileage_text)

        engine_size: str = specs.get("排気量", "")
        inspection_date: str = specs.get("車検", "")

        # ── Transmission ───────────────────────────────────────────────────
        transmission_raw: str = specs.get("ミッション", "")
        if "CVT" in transmission_raw:
            transmission: str = "CVT"
        elif "AT" in transmission_raw:
            transmission = "AT"
        elif "MT" in transmission_raw:
            transmission = "MT"
        else:
            transmission = translate_transmission(transmission_raw)

        fuel_type: str = translate_fuel_type(specs.get("燃料", ""))
        drive_type: str = translate_drive_type(specs.get("駆動", ""))

        # ── Body type & Color ──────────────────────────────────────────────
        body_items = card.select("li.carBodyInfoList__item")
        body_type_raw: str = body_items[0].get_text(strip=True) if len(body_items) > 0 else ""
        color_raw: str = body_items[1].get_text(strip=True) if len(body_items) > 1 else ""
        body_type: str = translate_body_type(body_type_raw)
        color: str = translate_color(color_raw)

        # ── Location ───────────────────────────────────────────────────────
        location_tag = (
            card.select_one("p.shopCassette__address")
            or card.select_one("[class*='shopAddress']")
            or card.select_one("[class*='address']")
        )
        location_raw: str = _get_text(location_tag)
        location: str = translate_location(location_raw)

        # ── Image ──────────────────────────────────────────────────────────
        image_url: str = _extract_image_url(card)

        # ── Truncation guards ──────────────────────────────────────────────
        brand           = brand[:100]
        model           = model[:500]
        color           = color[:50]
        fuel_type       = fuel_type[:50]
        transmission    = transmission[:50]
        body_type       = body_type[:50]
        drive_type      = drive_type[:20]
        engine_size     = engine_size[:20]
        inspection_date = inspection_date[:50]
        location        = location[:100]

        return {
            "external_id": external_id,
            "url": url,
            "brand": brand,
            "model": model,
            "year": year or 2000,
            "mileage": mileage,
            "price": price,
            "color": color,
            "fuel_type": fuel_type,
            "transmission": transmission,
            "body_type": body_type,
            "drive_type": drive_type,
            "engine_size": engine_size,
            "inspection_date": inspection_date,
            "location": location,
            "image_url": image_url,
            "image_urls": [image_url] if image_url else [],
            "raw_data": {
                "price_text": price_text,
                "mileage_text": mileage_text,
                "year_text": year_text,
                "specs": specs,
                "body_type_raw": body_type_raw,
                "color_raw": color_raw,
            },
            "scraped_at": datetime.now(timezone.utc),
        }

    except Exception as exc:
        logger.warning(f"Error parsing card: {exc}", exc_info=True)
        return None


def parse_listing_page(soup: BeautifulSoup) -> list[dict]:
    """
    Extract all car listing cards from a parsed search results page.

    Primary selector confirmed from DevTools: div.cassetteWrap.js-mainCassette
    Two fallbacks provided for resilience against minor HTML changes.
    """
    cars: list[dict] = []

    car_cards = soup.select("div.cassetteWrap.js-mainCassette")
    if not car_cards:
        car_cards = soup.select("div.cassetteWrap")
    if not car_cards:
        car_cards = soup.select("div.cassetteMain")

    logger.debug(f"Found {len(car_cards)} card elements on page.")

    for card in car_cards:
        try:
            car = parse_car_card(card)
            if car:
                cars.append(car)
        except Exception as exc:
            logger.warning(f"Failed to parse car card: {exc}")

    return cars


def get_next_page_url(current_page: int) -> str:
    """
    Construct the next page URL directly from the current page number.

    carsensor.net pagination URLs:
        Page 1 → https://www.carsensor.net/usedcar/search.php?AR=0&SKIND=1  (SEARCH_URL)
        Page 2 → https://www.carsensor.net/usedcar/index2.html
        Page 3 → https://www.carsensor.net/usedcar/index3.html
        Page N → https://www.carsensor.net/usedcar/indexN.html

    We construct the URL directly — no HTML parsing needed, no looping risk.
    """
    next_page = current_page + 1
    return f"{BASE_URL}/usedcar/index{next_page}.html"


def scrape_all_cars(max_pages: int = 10) -> list[dict]:
    """
    Main scrape loop.

    Design decisions:
    - Single shared Session across all pages — preserves cookies and
      makes Referer headers consistent, both critical for avoiding
      mid-session bans.
    - Homepage warm-up before first search request.
    - Page URLs constructed directly from page number — avoids the
      index2/index3 infinite loop caused by HTML pagination parsing.
    - Randomized 2–5s inter-page delay mimics human browsing cadence.
    - max_pages is a safety circuit-breaker (default: 10 = 300 cars).
    """
    all_cars: list[dict] = []
    session = _build_session()
    _warm_up_session(session)

    page: int = 1
    url: str = SEARCH_URL  # Page 1 uses the search URL directly

    while page <= max_pages:
        logger.info(f"Scraping page {page}: {url}")
        soup = fetch_page(url, session)

        if not soup:
            logger.error(f"Aborting scrape at page {page} — fetch returned None.")
            break

        cars = parse_listing_page(soup)
        if not cars:
            logger.info(f"No cars found on page {page}. Scrape complete.")
            break

        all_cars.extend(cars)
        logger.info(f"Page {page}: +{len(cars)} cars (running total: {len(all_cars)})")

        page += 1

        if page <= max_pages:
            url = get_next_page_url(page - 1)
            delay = random.uniform(_MIN_DELAY_SECONDS, _MAX_DELAY_SECONDS)
            logger.debug(f"Waiting {delay:.1f}s before next page...")
            time.sleep(delay)
        else:
            break

    logger.info(f"Scrape finished. Total cars collected: {len(all_cars)}")
    return all_cars
