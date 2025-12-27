import re
import time
from pathlib import Path

import click
import pandas as pd
import requests
from bs4 import BeautifulSoup


@click.command(
    help="""
    Scrape sold house data from Right Move and save to CSV.

    URL setup: Go to rightmove.co.uk/house-prices.html, apply filters,
    navigate to page 2, copy URL up to "pageNumber=" (exclude the number).
    """
)
@click.option(
    "--url",
    type=str,
    required=True,
    help="Right Move URL ending with 'pageNumber=' (without page number).",
)
@click.option(
    "--output-path",
    type=click.Path(path_type=Path),
    required=True,
    help="Path to save CSV output.",
)
def scrape_rightmove_cli(url: str, output_path: Path) -> None:
    """Scrape sold house data from Right Move."""
    df = scrape_sold_houses(url)
    df.to_csv(output_path, index=False)
    click.echo(f"Saved {len(df)} records to {output_path}")


def scrape_sold_houses(url: str) -> pd.DataFrame:
    """
    Scrape all pages of sold house data from Right Move.

    Args:
        url: Right Move search URL ending with "pageNumber=".

    Returns:
        DataFrame with columns: property_type, address, date, price, bedrooms.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    n_pages = _extract_page_count(soup)
    time.sleep(2)

    properties_info_pages = []
    for i in range(n_pages):
        response = requests.get(url + str(i + 1), headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        properties_info_pages.append(_parse_property_page(soup))
        time.sleep(3)

    return pd.concat(properties_info_pages, ignore_index=True)


def _extract_page_count(soup: BeautifulSoup) -> int:
    """Extract total number of pages from pagination dropdown."""
    dropdown = soup.find_all("div", class_="dsrm_dropdown_section")[0]
    page_text = dropdown.find_all("span")[1].text
    return int(page_text.replace("of ", ""))


def _parse_property_page(soup: BeautifulSoup) -> pd.DataFrame:
    """
    Parse all property cards from a single page.

    Returns:
        DataFrame with one row per sale transaction.
    """
    property_cards = soup.find_all("a", attrs={"data-testid": "propertyCard"})
    properties_info = []

    for card in property_cards:
        address = card.find("h3").text

        property_type_div = card.find_all(
            "div", attrs={"aria-label": re.compile(r"property type:", re.IGNORECASE)}
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

        dates, prices = _extract_dates_prices(card)

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


def _extract_dates_prices(property_card: BeautifulSoup) -> tuple[list[str], list[int | str]]:
    """
    Extract sale dates and prices from property card table.

    Returns:
        Tuple of (dates, prices) where dates are strings and prices are integers or empty strings.
    """
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
