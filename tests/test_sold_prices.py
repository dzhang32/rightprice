from pathlib import Path

import pytest
import responses
from bs4 import BeautifulSoup

from rightprice.sold_prices import House, SoldPriceRetriever


@pytest.fixture
def fixture_dir() -> Path:
    """
    Return path to test fixtures directory.
    """
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def test_html(fixture_dir: Path) -> str:
    """
    Load mock HTML page.
    """
    return (fixture_dir / "sold_prices_page_1.html").read_text()


# TODO - add integration test
@responses.activate
def test_sold_price_retriver(test_html: str) -> None:
    """
    Test that the sold price retriever works correctly.
    """
    # Register mock HTTP response.
    responses.add(
        responses.GET,
        "https://www.rightmove.co.uk/house-prices/ha0-1aq.html?pageNumber=1",
        body=test_html,
        status=200,
    )

    retriever = SoldPriceRetriever("HA0 1AQ", Path("data"))

    # Check postcode is formatted correctly.
    assert retriever.postcode == "ha0-1aq"

    # Check URLs can be correctly constructed.
    url_page_1 = retriever.get_url(1)
    assert (
        url_page_1
        == "https://www.rightmove.co.uk/house-prices/ha0-1aq.html?pageNumber=1"
    )

    url_page_5 = retriever.get_url(5)
    assert (
        url_page_5
        == "https://www.rightmove.co.uk/house-prices/ha0-1aq.html?pageNumber=5"
    )

    # Check that HTML is retrieved and parsed correctly.
    soup = retriever.get_page(retriever.get_url(1))

    assert isinstance(soup, BeautifulSoup)

    # Check page count is retrieved.
    page_count = retriever.get_page_count(soup)

    assert isinstance(page_count, int)
    assert page_count > 0

    # Check property info is correctly retrieved.
    properties = retriever.get_house_info(soup)

    assert isinstance(properties, list)
    assert len(properties) > 0
    assert all(isinstance(prop, House) for prop in properties)
