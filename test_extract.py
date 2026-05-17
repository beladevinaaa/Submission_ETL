import pytest
import pandas as pd
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../utils")))
import extract  # type: ignore

# ── helpers ──────────────────────────────────────────────────────────

ONE_CARD_HTML = """<html><body>
<div class="collection-card">
    <h3>Mock Shirt</h3>
    <span class="price">$20.00</span>
    <p>Rating: ⭐ 4.0 / 5</p>
    <p>3 Colors</p>
    <p>Size: M</p>
    <p>Gender: Unisex</p>
</div>
</body></html>"""

TWO_CARDS_HTML = """<html><body>
<div class="collection-card"><h3>A</h3><span class="price">$1</span></div>
<div class="collection-card"><h3>B</h3><span class="price">$2</span></div>
</body></html>"""

def mock_response(status=200, html=""):
    r = MagicMock()
    r.status_code = status
    r.text = html
    return r

# ── constants ─────────────────────────────────────────────────────────

def test_base_url():
    assert extract.BASE_URL == "https://fashion-studio.dicoding.dev/"

def test_headers_has_user_agent():
    assert "User-Agent" in extract.headers

# ── card parsing ──────────────────────────────────────────────────────

def _parse(html_snippet):
    from bs4 import BeautifulSoup
    card = BeautifulSoup(html_snippet, "html.parser").find("div", class_="collection-card")
    title = card.find("h3")
    price = card.find("span", class_="price")
    info  = card.find_all("p")
    rating = colors = size = gender = None
    for p in info:
        t = p.text.strip()
        if "Rating" in t: rating = t
        elif "Colors" in t: colors = t
        elif "Size"   in t: size   = t
        elif "Gender" in t: gender = t
    return {
        "Title":  title.text.strip() if title else "Unknown Product",
        "Price":  price.text.strip() if price else "Price Unavailable",
        "Rating": rating or "Invalid Rating",
        "Colors": colors or "Unknown",
        "Size":   size   or "Unknown",
        "Gender": gender or "Unknown",
    }

def test_parse_full_card():
    r = _parse(ONE_CARD_HTML)
    assert r["Title"]  == "Mock Shirt"
    assert r["Price"]  == "$20.00"
    assert "4.0"       in r["Rating"]
    assert r["Colors"] == "3 Colors"
    assert r["Size"]   == "Size: M"
    assert r["Gender"] == "Gender: Unisex"

def test_parse_missing_title_fallback():
    r = _parse('<div class="collection-card"><span class="price">$1</span></div>')
    assert r["Title"] == "Unknown Product"

def test_parse_missing_price_fallback():
    r = _parse('<div class="collection-card"><h3>Shirt</h3></div>')
    assert r["Price"] == "Price Unavailable"

def test_parse_missing_info_fallback():
    r = _parse('<div class="collection-card"><h3>X</h3></div>')
    assert r["Rating"] == "Invalid Rating"
    assert r["Colors"] == "Unknown"
    assert r["Size"]   == "Unknown"
    assert r["Gender"] == "Unknown"

# ── extract_data ──────────────────────────────────────────────────────

@pytest.fixture
def mock_get():
    with patch("extract.time.sleep"), \
         patch("extract.requests.get", return_value=mock_response(html=ONE_CARD_HTML)) as m:
        yield m

def test_returns_dataframe(mock_get: MagicMock | AsyncMock):
    assert isinstance(extract.extract_data(), pd.DataFrame)

def test_required_columns(mock_get: MagicMock | AsyncMock):
    df = extract.extract_data()
    assert {"Title","Price","Rating","Colors","Size","Gender","timestamp"}.issubset(df.columns)

def test_data_scraped(mock_get: MagicMock | AsyncMock):
    assert len(extract.extract_data()) > 0

def test_title_value(mock_get: MagicMock | AsyncMock):
    assert (extract.extract_data()["Title"] == "Mock Shirt").any()

def test_failed_page_skipped():
    with patch("extract.time.sleep"), \
         patch("extract.requests.get", return_value=mock_response(status=500)):
        assert len(extract.extract_data()) == 0

def test_sleep_called_50_times():
    with patch("extract.time.sleep") as s, \
         patch("extract.requests.get", return_value=mock_response(html=ONE_CARD_HTML)):
        extract.extract_data()
    assert s.call_count == 50

def test_page1_uses_base_url(mock_get: MagicMock | AsyncMock):
    extract.extract_data()
    assert mock_get.call_args_list[0][0][0] == extract.BASE_URL

def test_page2_uses_page_url(mock_get: MagicMock | AsyncMock):
    extract.extract_data()
    assert "page2" in mock_get.call_args_list[1][0][0]

def test_timestamp_format(mock_get: MagicMock | AsyncMock):
    df = extract.extract_data()
    datetime.strptime(df["timestamp"].iloc[0], "%Y-%m-%d %H:%M:%S")

def test_multiple_cards_per_page():
    with patch("extract.time.sleep"), \
         patch("extract.requests.get", return_value=mock_response(html=TWO_CARDS_HTML)):
        assert len(extract.extract_data()) == 100  # 50 pages × 2 cards

def test_request_sends_headers(mock_get: MagicMock | AsyncMock):
    extract.extract_data()
    assert mock_get.call_args_list[0][1]["headers"] == extract.headers