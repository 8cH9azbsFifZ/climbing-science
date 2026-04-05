"""Validate that every citation in the repo resolves to a BibTeX key.

Scans Python docstrings for ``:cite:`KEY``` and Markdown files for
``\\[cite:KEY\\]`` patterns.  Compares against keys defined in
``docs/references.bib``.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BIB_FILE = REPO / "docs" / "references.bib"

PY_CITE = re.compile(r":cite:`(\w+)`")
MD_CITE = re.compile(r"\[cite:(\w+)\]")


def _parse_bib_keys(bib_path: Path) -> set[str]:
    return set(re.findall(r"@\w+\{(\w+)\s*,", bib_path.read_text()))


def _scan_file(path: Path) -> dict[str, list[int]]:
    hits: dict[str, list[int]] = {}
    pattern = PY_CITE if path.suffix == ".py" else MD_CITE
    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        for m in pattern.finditer(line):
            hits.setdefault(m.group(1), []).append(lineno)
    return hits


class TestCitations:
    """Ensure all :cite: and [cite:] keys resolve to references.bib."""

    def test_bib_file_exists(self):
        assert BIB_FILE.exists(), f"{BIB_FILE} not found"

    def test_no_dangling_citations(self):
        """Every citation key used in src/ and docs/ must exist in .bib."""
        bib_keys = _parse_bib_keys(BIB_FILE)
        source_files = list((REPO / "src").rglob("*.py")) + list((REPO / "docs").rglob("*.md"))

        dangling = []
        for path in sorted(source_files):
            for key, lines in _scan_file(path).items():
                if key not in bib_keys:
                    dangling.append(f"{path.relative_to(REPO)}:{','.join(map(str, lines))} → {key}")

        assert not dangling, "Dangling citations (used but NOT in .bib):\n" + "\n".join(dangling)

    def test_bib_has_entries(self):
        """The .bib file must contain at least one entry."""
        bib_keys = _parse_bib_keys(BIB_FILE)
        assert len(bib_keys) > 0, "references.bib is empty"
