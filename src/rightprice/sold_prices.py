import logging
import re
import time

import polars as pl
import requests
from bs4 import BeautifulSoup, ResultSet, Tag

from rightprice.error import InvalidRadiusError, InvalidYearsError, PostCodeFormatError
from rightprice.house import House

logger = logging.getLogger(__name__)


class SoldPriceRetriever:
    """
    Retrieves sold property prices for a given postcode.
    """

    BASE_URL = "https://www.rightmove.co.uk/house-prices/"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        + "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    def __init__(
        self,
        postcode: str,
        radius: float | None = None,
        years: int | None = None,
    ):
        """
        Initialize the sold price retriever.

        Args:
            postcode: UK postcode with space separator (e.g. "SE3 0AA").
            radius: Number of miles from the postcode to search for properties. Valid values: 0.25, 0.5, 1, 3, 5, 10.
            years: Number of years back from the current date to search for sold properties. Valid values: 2, 3, 5, 10, 15, 20.
        """
        self.postcode = self._validate_postcode(postcode)
        self.radius = self._validate_radius(radius)
        self.years = self._validate_radius(years)

    def retrieve(self) -> pl.DataFrame:
        """
        Retrieve all sold property prices for the configured postcode.

        Returns:
            DataFrame with columns: address, property_type, n_bedrooms, date, price.
        """
        # Obtain the total number of pages of houses.
        url = self.get_url(1)
        soup = self.get_page(url)
        n_pages = self.get_page_count(soup)

        houses = []
        for i in range(n_pages):
            page_number = i + 1
            logger.info(f"Fetching sold prices from page {page_number}")

            # Fetch the current page.
            url = self.get_url(page_number)
            soup = self.get_page(url)

            # Extract the information for each house.
            houses_per_page = self.get_houses_info(soup)
            houses.extend(houses_per_page)

            time.sleep(1)

        rows = []
        for house in houses:
            base = house.model_dump(exclude={"dates", "prices"})
            # Ensure there is 1 row per date/price for each house.
            for date, price in zip(house.dates, house.prices):
                rows.append({**base, "date": date, "price": price})

        return pl.DataFrame(rows)

    def get_url(
        self,
        page_number: int,
    ) -> str:
        """
        Build the URL for a specific page number.

        Args:
            page_number: The page number to retrieve.

        Returns:
            The complete URL with query parameters.
        """
        url = f"{self.BASE_URL}{self.postcode}.html?"

        # Build the URL query.
        extra_params = [f"pageNumber={str(page_number)}"]
        if self.radius:
            extra_params.append(f"radius={str(self.radius)}")
        if self.years:
            extra_params.append(f"soldIn={str(self.years)}")
        extra_params_joined = "&".join(extra_params)

        return url + extra_params_joined

    def get_page(self, url: str) -> BeautifulSoup:
        """
        Fetch and parse an HTML page.

        Args:
            url: The URL to fetch.

        Returns:
            Parsed HTML as a BeautifulSoup object.
        """
        response = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        return soup

    def get_page_count(self, soup: BeautifulSoup) -> int:
        """
        Extract the total number of pages from the HTML.

        Args:
            soup: Parsed HTML page.

        Returns:
            Total number of pages available.
        """
        dropdown = soup.find_all("div", class_="dsrm_dropdown_section")[0]
        page_text = dropdown.find_all("span")[1].text

        return int(page_text.replace("of ", ""))

    def get_houses_info(self, soup: BeautifulSoup) -> list[House]:
        """
        Extract information for all properties on a page.

        Args:
            soup: Parsed HTML page.

        Returns:
            List of House objects containing property details.
        """
        property_cards = soup.find_all("a", attrs={"data-testid": "propertyCard"})
        properties_info = []

        for card in property_cards:
            dates, prices = self._get_dates_prices(card)

            property_info = House(
                address=self._get_address(card),
                property_type=self._get_property_type(card),
                n_bedrooms=self._get_bedrooms(card),
                dates=dates,
                prices=prices,
            )

            properties_info.append(property_info)

        return properties_info

    @staticmethod
    def _validate_postcode(postcode: str) -> str:
        """
        Validate and format postcode for URL usage.

        Args:
            postcode: UK postcode with space separator.

        Returns:
            Lowercase postcode with space replaced by hyphen.

        Raises:
            PostCodeFormatError: If postcode doesn't contain a space.
        """
        if " " not in postcode:
            raise PostCodeFormatError(
                "Postcode must contain a space separator e.g. SE3 0AA"
            )

        return postcode.lower().replace(" ", "-")

    @staticmethod
    def _validate_radius(
        radius: float | None, choices=[0.25, 0.5, 1, 3, 5, 10]
    ) -> float | None:
        """
        Validate that radius is one of the allowed values.

        Args:
            radius: Search radius in miles.
            choices: Valid radius values.

        Returns:
            The validated radius value.

        Raises:
            InvalidRadiusError: If radius is not in the allowed choices.
        """
        if radius is not None and radius not in choices:
            choices_joined = ", ".join([str(x) for x in choices])
            raise InvalidRadiusError(
                f"radius must be one of: {', '.join(choices_joined)}"
            )

        return radius

    @staticmethod
    def _validate_years(years: int | None, choices=[2, 3, 5, 10, 15, 20]) -> int | None:
        """
        Validate that years is one of the allowed values.

        Args:
            years: Number of years to search back.
            choices: Valid year values.

        Returns:
            The validated years value.

        Raises:
            InvalidYearsError: If years is not in the allowed choices.
        """
        if years is not None and years not in choices:
            choices_joined = ", ".join([str(x) for x in choices])
            raise InvalidYearsError(
                f"years must be one of: {', '.join(choices_joined)}"
            )

        return years

    @staticmethod
    def _get_dates_prices(
        property_card: BeautifulSoup,
    ) -> tuple[list[str], list[int | None]]:
        """
        Extract sale dates and prices from a property card.

        Args:
            property_card: Parsed property card HTML.

        Returns:
            Tuple of (dates, prices) where dates are strings and prices are integers or None.
        """
        # Extract table cells containing date/price pairs (skip first 2 cells).
        table_cells = property_card.find_all("td")[2:]

        dates: list[str] = []
        prices: list[int | None] = []

        # Process cells in pairs: (date, price).
        for i in range(0, len(table_cells), 2):
            # Stop if we've run out of pairs or encounter an empty date.
            if i + 1 >= len(table_cells) or not table_cells[i].text:
                break

            date_cell = table_cells[i]
            price_cell = table_cells[i + 1]

            # Extract date.
            dates.append(date_cell.text)

            # Extract and parse price.
            price_text = price_cell.text
            if price_text.startswith("£"):
                # Remove £ symbol and commas, then convert to integer.
                price = int(price_text[1:].replace(",", ""))
                prices.append(price)
            else:
                prices.append(None)

        return dates, prices

    @staticmethod
    def _get_houses(soup: BeautifulSoup) -> ResultSet[Tag]:
        """
        Extract all property card elements from the page.

        Args:
            soup: Parsed HTML page.

        Returns:
            Collection of property card HTML elements.
        """
        return soup.find_all("a", attrs={"data-testid": "propertyCard"})

    @staticmethod
    def _get_address(house: Tag) -> str:
        """
        Extract the property address from a property card.

        Args:
            house: Property card HTML element.

        Returns:
            The property address.
        """
        return house.find("h2").text

    @staticmethod
    def _get_property_type(house: Tag) -> str | None:
        """
        Extract the property type from a property card.

        Args:
            house: Property card HTML element.

        Returns:
            The property type, or None if not found.
        """
        property_type_div = house.find_all(
            "div",
            attrs={"aria-label": re.compile(r"property type:", re.IGNORECASE)},
        )
        property_type = (
            property_type_div[0].text.replace("Property Type: ", "")
            if property_type_div
            else None
        )

        return property_type

    @staticmethod
    def _get_bedrooms(house: Tag) -> int | None:
        """
        Extract the number of bedrooms from a property card.

        Args:
            house: Property card HTML element.

        Returns:
            The number of bedrooms, or None if not found.
        """
        n_bedrooms_div = house.find_all(
            "div", attrs={"aria-label": re.compile(r"bedrooms:", re.IGNORECASE)}
        )
        n_bedrooms = (
            int(n_bedrooms_div[0].text.replace("Bedrooms: ", ""))
            if n_bedrooms_div
            else None
        )

        return n_bedrooms
