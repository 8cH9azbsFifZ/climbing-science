"""Basic tests for climbing_science package."""

import re
from pathlib import Path

from climbing_science import __version__


def test_version():
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject.read_text(), re.MULTILINE)
    assert match, "Could not find version in pyproject.toml"
    assert __version__ == match.group(1)
