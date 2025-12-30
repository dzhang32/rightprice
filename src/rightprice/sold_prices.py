import re

import polars as pl
import requests
from bs4 import BeautifulSoup, ResultSet, Tag

from rightprice.error import InvalidRadiusError, InvalidYearsError, PostCodeFormatError
from rightprice.house import House


class SoldPriceRetriever:
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
        self.postcode = self._validate_postcode(postcode)
        self.radius = self._validate_radius(radius)
        self.years = self._validate_radius(years)

    def retrieve(self) -> pl.DataFrame:
        url = self.get_url(1)
        soup = self.get_page(url)
        n_pages = self.get_page_count(soup)

        houses = []
        for i in range(n_pages):
            url = self.get_url(i + 1)
            soup = self.get_page(url)
            house_list = self.get_house_info(soup)
            houses.extend(house_list)

        # Flatten list[House] to rows where each date/price is a row
        rows = []
        for house in houses:
            base = house.model_dump(exclude={"dates", "prices"})
            for date, price in zip(house.dates, house.prices):
                rows.append({**base, "date": date, "price": price})

        return pl.DataFrame(rows)

    def get_url(
        self,
        page_number: int,
    ) -> str:
        url = f"{self.BASE_URL}{self.postcode}.html?"

        extra_params = [f"pageNumber={str(page_number)}"]
        if self.radius:
            extra_params.append(f"radius={str(self.radius)}")
        if self.years:
            extra_params.append(f"soldIn={str(self.years)}")
        extra_params = "&".join(extra_params)

        return url + extra_params

    def get_page(self, url: str) -> BeautifulSoup:
        response = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        return soup

    def get_page_count(self, soup: BeautifulSoup) -> int:
        dropdown = soup.find_all("div", class_="dsrm_dropdown_section")[0]
        page_text = dropdown.find_all("span")[1].text
        return int(page_text.replace("of ", ""))

    def get_house_info(self, soup: BeautifulSoup) -> list[House]:
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
        if " " not in postcode:
            raise PostCodeFormatError(
                "Postcode must contain a space separator e.g. SE3 0AA"
            )

        return postcode.lower().replace(" ", "-")

    @staticmethod
    def _validate_radius(
        radius: float | None, choices=[0.25, 0.5, 1, 3, 5, 10]
    ) -> float:
        if radius is not None and radius not in choices:
            choices_joined = ", ".join([str(x) for x in choices])
            raise InvalidRadiusError(
                f"radius must be one of: {', '.join(choices_joined)}"
            )

        return radius

    @staticmethod
    def _validate_years(years: int | None, choices=[2, 3, 5, 10, 15, 20]) -> int:
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
        prices_dates = property_card.find_all("td")[2:]

        dates = []
        prices = []

        for i, td in enumerate(prices_dates):
            if td.text == "":
                break

            if i % 2 == 0:
                dates.append(td.text)
            else:
                if td.text[0] == "£":
                    prices.append(int(td.text[1:].replace(",", "")))
                else:
                    prices.append(None)

        return dates, prices

    @staticmethod
    def _get_houses(soup: BeautifulSoup) -> ResultSet[Tag]:
        return soup.find_all("a", attrs={"data-testid": "propertyCard"})

    @staticmethod
    def _get_address(house: Tag) -> str:
        return house.find("h2").text

    @staticmethod
    def _get_property_type(house: Tag) -> str | None:
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
        n_bedrooms_div = house.find_all(
            "div", attrs={"aria-label": re.compile(r"bedrooms:", re.IGNORECASE)}
        )
        n_bedrooms = (
            int(n_bedrooms_div[0].text.replace("Bedrooms: ", ""))
            if n_bedrooms_div
            else None
        )

        return n_bedrooms
