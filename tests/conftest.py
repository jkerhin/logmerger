from pathlib import Path

import pytest


@pytest.fixture
def test_data_root() -> Path:
    this_file = Path(__file__)
    return this_file.parent.parent / "files"
