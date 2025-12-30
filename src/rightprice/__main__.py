import logging

import click

from rightprice.cli import retrieve_sold_prices


@click.group()
def cli() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s -  %(levelname)s - %(message)s",
        datefmt="%H:%M:%S",
    )


cli.add_command(retrieve_sold_prices)
