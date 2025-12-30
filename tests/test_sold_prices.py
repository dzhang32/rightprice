from pathlib import Path

import pytest
import responses
from bs4 import BeautifulSoup
from polars import DataFrame

from rightprice.error import InvalidRadiusError, InvalidYearsError, PostCodeFormatError
from rightprice.sold_prices import House, SoldPriceRetriever


@responses.activate
def test_sold_price_retriver(fixture_dir: Path) -> None:
    """
    Test that the sold price retriever works correctly.
    """
    # Register mock HTTP response.
    responses.add(
        responses.GET,
        "https://www.rightmove.co.uk/house-prices/ha0-1aq.html?pageNumber=1",
        body=(fixture_dir / "postcode_page_1.html").read_text(),
        status=200,
    )

    retriever = SoldPriceRetriever("HA0 1AQ")

    # Check postcode is formatted and validated correctly.
    assert retriever.postcode == "ha0-1aq"

    with pytest.raises(PostCodeFormatError) as e:
        retriever._validate_postcode("BADPOSTCODE")
        assert "Postcode must contain a space separator" in str(e.value)

    # Check radius is validated correctly.
    with pytest.raises(InvalidRadiusError) as e:
        retriever._validate_radius(100)
        assert "radius must be one of" in str(e.value)

    # Check years is validated correctly.
    with pytest.raises(InvalidYearsError) as e:
        retriever._validate_years(100)
        assert "years must be one of" in str(e.value)

    # Check URLs can be correctly constructed.
    assert (
        retriever.get_url(5)
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
    properties = retriever.get_houses_info(soup)

    assert isinstance(properties, list)
    assert len(properties) > 0
    assert all(isinstance(prop, House) for prop in properties)


@responses.activate
def test_sold_price_retriver_integration(fixture_dir: Path) -> None:
    """
    Test that the sold price retriever works end-to-end on multiple pages.
    """
    # Register mock HTTP response.
    responses.add(
        responses.GET,
        "https://www.rightmove.co.uk/house-prices/ha0-1aq.html?pageNumber=1&radius=0.25&soldIn=3",
        body=(fixture_dir / "postcode_radius_year_page_1.html").read_text(),
        status=200,
    )
    responses.add(
        responses.GET,
        "https://www.rightmove.co.uk/house-prices/ha0-1aq.html?pageNumber=2&radius=0.25&soldIn=3",
        body=(fixture_dir / "postcode_radius_year_page_2.html").read_text(),
        status=200,
    )

    retriever = SoldPriceRetriever("HA0 1AQ", radius=0.25, years=3)
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
