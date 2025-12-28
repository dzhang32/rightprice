import re
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


class SoldPriceRetriever:
    BASE_URL = "https://www.rightmove.co.uk/house-prices/"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        + "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    def __init__(self, postcode: str, output_dir: Path):
        # TODO: Validate postcode.
        self.postcode = postcode.lower().replace(" ", "-")
        # TODO: Build output path using input postcode.
        self.output_dir = output_dir

    def retrieve(self) -> None:
        url = self._get_url()
        soup = self._get_page(url) + "1"

        for page in range(self._extract_page_count(soup)):
            url = self._get_url() + str(page + 1)
            soup = self._get_page(url)
            properties_info = self._extract_property_info(soup)
            properties_info.append(properties_info)

        properties_info = pd.concat(properties_info, ignore_index=True)
        properties_info.to_csv(self.output_dir / f"{self.postcode}.csv", index=False)

    def _get_url(self) -> str:
        # TODO: Add more parameters.
        return f"{self.BASE_URL}{self.postcode}.html?pageNumber="

    def _get_page(self, url: str) -> BeautifulSoup:
        response = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(response.text, "html.parser")

        return soup

    def _extract_page_count(self, soup: BeautifulSoup) -> int:
        dropdown = soup.find_all("div", class_="dsrm_dropdown_section")[0]
        page_text = dropdown.find_all("span")[1].text
        return int(page_text.replace("of ", ""))

    def _extract_property_info(self, soup: BeautifulSoup) -> pd.DataFrame:
        property_cards = soup.find_all("a", attrs={"data-testid": "propertyCard"})
        properties_info = []

        for card in property_cards:
            address = card.find("h3").text

            property_type_div = card.find_all(
                "div",
                attrs={"aria-label": re.compile(r"property type:", re.IGNORECASE)},
            )
            property_type = (
                property_type_div[0].text.replace("Property Type: ", "")
                if property_type_div
                else ""
            )

            bedrooms_div = card.find_all(
                "div", attrs={"aria-label": re.compile(r"bedrooms", re.IGNORECASE)}
            )
            bedrooms = (
                int(bedrooms_div[0].text.replace("Bedrooms: ", ""))
                if bedrooms_div
                else pd.NA
            )

            dates, prices = self._extract_dates_prices(card)

            property_info = pd.DataFrame(
                {
                    "property_type": property_type,
                    "address": address,
                    "date": dates,
                    "price": prices,
                    "bedrooms": bedrooms,
                }
            )
            properties_info.append(property_info)

        return pd.concat(properties_info, ignore_index=True)

    def _extract_dates_prices(
        property_card: BeautifulSoup,
    ) -> tuple[list[str], list[int | str]]:
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
                    prices.append("")

        return dates, prices
