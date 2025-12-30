from pathlib import Path

import pytest
import responses
from bs4 import BeautifulSoup
from polars import DataFrame

from rightprice.error import PostCodeFormatError
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

    retriever = SoldPriceRetriever("HA0 1AQ")

    # Check postcode is formatted correctly.
    assert retriever.postcode == "ha0-1aq"
    # And postcode validator catches user input errors.
    with pytest.raises(PostCodeFormatError) as e:
        retriever._format_postcode("BADPOSTCODE")
        assert "Postcode must contain a space separator" in str(e.value)

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
    n_pages = retriever.get_page_count(soup)

    assert isinstance(n_pages, int)
    assert n_pages > 0

    # Check property info is correctly retrieved.
    properties = retriever.get_house_info(soup)

    assert isinstance(properties, list)
    assert len(properties) > 0
    assert all(isinstance(prop, House) for prop in properties)


@responses.activate
def test_sold_price_retriver_integration(test_html: str) -> None:
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

    retriever = SoldPriceRetriever("HA0 1AQ")
    sold_prices = retriever.retrieve()

    assert isinstance(sold_prices, DataFrame)
    assert sold_prices.columns == [
        "address",
        "property_type",
        "n_bedrooms",
        "date",
        "price",
    ]
    assert sold_prices.shape[0] > 0
