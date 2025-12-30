from pathlib import Path

import polars as pl
import responses
from click.testing import CliRunner

from rightprice.cli import retrieve_sold_prices


@responses.activate
def test_retrieve_sold_prices(fixture_dir: Path, tmp_path: Path) -> None:
    """
    Test the retrieve_sold_prices CLI command.
    """
    # Register mock HTTP responses.
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

    runner = CliRunner()
    result = runner.invoke(
        retrieve_sold_prices,
        [
            "--postcode",
            "HA0 1AQ",
            "--radius",
            "0.25",
            "--years",
            "3",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0

    # Check that output file was created with correct name.
    output_file = tmp_path / "ha0-1aq_radius-0.25_years-3.csv"
    assert output_file.exists()

    # Check that the CSV contains the correct data.
    sold_prices = pl.read_csv(output_file)
    assert sold_prices.columns == [
        "address",
        "property_type",
        "n_bedrooms",
        "date",
        "price",
    ]
    assert sold_prices.shape[0] > 0
