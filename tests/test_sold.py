from pathlib import Path

import pytest
import responses
from bs4 import BeautifulSoup

from rightprice.sold import House, SoldPriceRetriever


@pytest.fixture
def fixture_dir() -> Path:
    """Return path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_html(fixture_dir: Path) -> str:
    """Load sample RightMove HTML page."""
    return (fixture_dir / "sold_prices_page_1.html").read_text()


@pytest.fixture
def sample_soup(sample_html: str) -> BeautifulSoup:
    """Parse sample HTML into BeautifulSoup object."""
    return BeautifulSoup(sample_html, "html.parser")


def test_init_formats_postcode() -> None:
    """Test that postcode is formatted correctly on initialization."""
    retriever = SoldPriceRetriever("W14 0DB", Path("data"))
    assert retriever.postcode == "w14-0db"


def test_get_url_constructs_correct_url() -> None:
    """Test URL construction for different page numbers."""
    retriever = SoldPriceRetriever("w14-0db", Path("data"))

    url_page_1 = retriever._get_url(1)
    assert url_page_1 == "https://www.rightmove.co.uk/house-prices/w14-0db.html?pageNumber=1"

    url_page_5 = retriever._get_url(5)
    assert url_page_5 == "https://www.rightmove.co.uk/house-prices/w14-0db.html?pageNumber=5"


@responses.activate
def test_get_page_returns_soup(sample_html: str) -> None:
    """Test that _get_page fetches and parses HTML correctly.

    This demonstrates how responses works:
    1. @responses.activate decorator intercepts all HTTP requests
    2. responses.add() registers a mock response for a specific URL
    3. When requests.get() is called, responses returns our mock HTML
    4. No actual HTTP request is made to RightMove
    """
    # Register a mock HTTP response
    responses.add(
        responses.GET,
        "https://www.rightmove.co.uk/house-prices/w14-0db.html?pageNumber=1",
        body=sample_html,
        status=200
    )

    retriever = SoldPriceRetriever("w14-0db", Path("data"))
    soup = retriever._get_page(retriever._get_url(1))

    assert isinstance(soup, BeautifulSoup)
    assert soup.find("h2") is not None  # Should have property addresses


def test_extract_page_count(sample_soup: BeautifulSoup) -> None:
    """Test extraction of total page count from HTML."""
    retriever = SoldPriceRetriever("w14-0db", Path("data"))
    page_count = retriever._extract_page_count(sample_soup)

    assert isinstance(page_count, int)
    assert page_count > 0


def test_extract_property_info(sample_soup: BeautifulSoup) -> None:
    """Test extraction of property information from HTML page."""
    retriever = SoldPriceRetriever("w14-0db", Path("data"))
    properties = retriever._extract_property_info(sample_soup)

    assert isinstance(properties, list)
    assert len(properties) > 0
    assert all(isinstance(prop, House) for prop in properties)

    # Check first property has expected fields
    first_property = properties[0]
    assert first_property.address
    assert isinstance(first_property.dates, list)
    assert isinstance(first_property.prices, list)
    assert len(first_property.dates) == len(first_property.prices)


def test_get_address(sample_soup: BeautifulSoup) -> None:
    """Test address extraction from property card."""
    property_cards = sample_soup.find_all("a", attrs={"data-testid": "propertyCard"})

    if property_cards:
        address = SoldPriceRetriever._get_address(property_cards[0])
        assert isinstance(address, str)
        assert len(address) > 0


def test_get_property_type(sample_soup: BeautifulSoup) -> None:
    """Test property type extraction from property card."""
    property_cards = sample_soup.find_all("a", attrs={"data-testid": "propertyCard"})

    if property_cards:
        property_type = SoldPriceRetriever._get_property_type(property_cards[0])
        # Property type can be None if not available
        assert property_type is None or isinstance(property_type, str)


def test_get_bedrooms(sample_soup: BeautifulSoup) -> None:
    """Test bedroom count extraction from property card."""
    property_cards = sample_soup.find_all("a", attrs={"data-testid": "propertyCard"})

    if property_cards:
        bedrooms = SoldPriceRetriever._get_bedrooms(property_cards[0])
        # Bedrooms can be None if not available
        assert bedrooms is None or isinstance(bedrooms, int)


def test_extract_dates_prices(sample_soup: BeautifulSoup) -> None:
    """Test extraction of date/price pairs from property card."""
    property_cards = sample_soup.find_all("a", attrs={"data-testid": "propertyCard"})

    if property_cards:
        dates, prices = SoldPriceRetriever._extract_dates_prices(property_cards[0])

        assert isinstance(dates, list)
        assert isinstance(prices, list)
        assert len(dates) == len(prices)

        # All dates should be strings
        assert all(isinstance(date, str) for date in dates)

        # Prices can be int or None (if "Price not disclosed")
        assert all(price is None or isinstance(price, int) for price in prices)


@responses.activate
def test_retrieve_makes_multiple_requests(sample_html: str) -> None:
    """Test that retrieve method fetches multiple pages.

    This demonstrates mocking multiple HTTP requests:
    - Each responses.add() call registers a different URL
    - responses automatically matches the URL when requests.get() is called
    """
    # Mock responses for pages 1 and 2
    responses.add(
        responses.GET,
        "https://www.rightmove.co.uk/house-prices/w14-0db.html?pageNumber=1",
        body=sample_html,
        status=200
    )
    responses.add(
        responses.GET,
        "https://www.rightmove.co.uk/house-prices/w14-0db.html?pageNumber=2",
        body=sample_html,
        status=200
    )

    retriever = SoldPriceRetriever("w14-0db", Path("data"))
    retriever.retrieve()

    # Verify that both URLs were called
    assert len(responses.calls) == 2
    assert "pageNumber=1" in responses.calls[0].request.url
    assert "pageNumber=2" in responses.calls[1].request.url


def test_house_creation_with_all_fields() -> None:
    """Test creating a House with all fields populated."""
    house = House(
        address="123 Main St",
        property_type="Flat",
        n_bedrooms=2,
        dates=["01 Jan 2024", "15 Jun 2020"],
        prices=[450000, 380000]
    )

    assert house.address == "123 Main St"
    assert house.property_type == "Flat"
    assert house.n_bedrooms == 2
    assert len(house.dates) == 2
    assert len(house.prices) == 2


def test_house_creation_with_optional_none() -> None:
    """Test creating a House with optional fields as None."""
    house = House(
        address="456 Oak Ave",
        property_type=None,
        n_bedrooms=None,
        dates=["20 Mar 2023"],
        prices=[675000]
    )

    assert house.address == "456 Oak Ave"
    assert house.property_type is None
    assert house.n_bedrooms is None


def test_house_with_undisclosed_prices() -> None:
    """Test creating a House with some undisclosed prices."""
    house = House(
        address="789 Elm Rd",
        property_type="Detached",
        n_bedrooms=4,
        dates=["12 Sep 2022", "05 May 2019"],
        prices=[None, 550000]
    )

    assert house.prices[0] is None
    assert house.prices[1] == 550000
