import click

from rightprice.scrape_rightmove import scrape_rightmove_cli

@click.group()
def cli() -> None:
    pass


# Add subcommands.
cli.add_command(scrape_rightmove_cli)