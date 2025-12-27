from pathlib import Path


import click


@click.command(
    help="""
    Add one to each line in the input file.
    """
)
@click.option(
    "--input-path",
    type=click.Path(exists=True, path_type=Path),
    required=True,
    help="Path to the input files containing one integer per line.",
)
@click.option(
    "--output-path",
    type=click.Path(path_type=Path),
    required=True,
    help="Path to the output file containing the integers plus one.",
)
def add_one_cli(input_path: Path, output_path: Path) -> None:
    """
    Add one to each line in the input file.
    """
    with open(output_path, "w") as output_file:
        for n_plus_1 in add_one_file(input_path):
            output_file.write(str(n_plus_1) + "\n")


def add_one_file(input_file: Path) -> list[int]:
    """
    Example function that adds one to the input.

    Args:
        input_file: The input file containing one integer per line.

    Returns:
        A list of integers, one for each line in the input file.
    """
    with open(input_file, "r") as f:
        return [add_one(int(line.strip())) for line in f]


def add_one(x: int) -> int:
    """
    Example function that adds one to the input.

    Args:
        x: The input number.

    Returns:
        The input number plus one.
    """

    return x + 1
