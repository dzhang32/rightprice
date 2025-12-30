import logging
from pathlib import Path

import click

from rightprice.sold_prices import SoldPriceRetriever

logger = logging.getLogger(__name__)


@click.command()
@click.argument("postcode")
@click.option(
    "--radius",
    type=float,
    default=None,
    help="Search radius in miles. Valid values: 0.25, 0.5, 1, 3, 5, 10.",
)
@click.option(
    "--years",
    type=int,
    default=None,
    help="Number of years back to search. Valid values: 2, 3, 5, 10, 15, 20.",
)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(),
    default=".",
    help="Output directory. Defaults to current directory.",
)
def retrieve_sold_prices(
    postcode: str, radius: float | None, years: int | None, output_dir: str
) -> None:
    """
    Retrieve sold property prices for a given postcode.
    """
    logger.info(f"Retrieving sold prices for {postcode}...")

    retriever = SoldPriceRetriever(postcode, radius=radius, years=years)
    sold_prices = retriever.retrieve()

    # Create output directory if it doesn't exist.
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Build filename from input parameters.
    filename_parts = [retriever.postcode]
    if retriever.radius is not None:
        filename_parts.append(f"radius-{retriever.radius}")
    if retriever.years is not None:
        filename_parts.append(f"years-{retriever.years}")
    filename = "_".join(filename_parts) + ".csv"

    output_file = output_path / filename
    sold_prices.write_csv(output_file)

    logger.info(f"Saved {sold_prices.shape[0]} sold prices to {output_file}")
