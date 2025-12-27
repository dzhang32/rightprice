from rightprice.add_one import add_one, add_one_file

from rightprice.__main__ import cli

from click.testing import CliRunner
import tempfile


from pathlib import Path


def test_add_one_cli(test_data_dir: Path) -> None:
    """
    Test the add_one_cli function works correctly.
    """
    input_path = test_data_dir / "test_add_one" / "integers.txt"

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "output.txt"

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "add-one-cli",
                "--input-path",
                str(input_path),
                "--output-path",
                str(output_path),
            ],
        )

        assert result.exit_code == 0
        assert output_path.read_text() == "2\n3\n4\n"


def test_add_one_file(test_data_dir: Path) -> None:
    """
    Test that the add_one_file function works correctly.
    """
    assert add_one_file(test_data_dir / "test_add_one" / "integers.txt") == [2, 3, 4]

def test_add_one() -> None:
    """
    Test that the add_one function works correctly.
    """
    assert add_one(31) == 32