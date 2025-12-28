import click


@click.group()
def cli() -> None:
    pass


# Add subcommands.
# cli.add_command(scrape_rightmove_cli)
