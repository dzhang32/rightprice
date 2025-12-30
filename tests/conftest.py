from pathlib import Path

import pytest


@pytest.fixture
def fixture_dir() -> Path:
    """
    Return path to test fixtures directory.
    """
    return Path(__file__).parent / "fixtures"
