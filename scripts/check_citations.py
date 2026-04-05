#!/usr/bin/env python3
"""Validate that every citation in the repo resolves to a BibTeX key.

Scans Python docstrings for ``:cite:`KEY``` and Markdown files for
``\\[cite:KEY\\]`` patterns.  Compares against keys defined in
``docs/references.bib``.

Exit codes:
    0 — all citations valid
    1 — dangling citations found (used but not in .bib)
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BIB_FILE = REPO / "docs" / "references.bib"

# Patterns that capture the citation key
PY_CITE = re.compile(r":cite:`(\w+)`")
MD_CITE = re.compile(r"\[cite:(\w+)\]")


def parse_bib_keys(bib_path: Path) -> set[str]:
    """Extract all ``@type{key,`` entries from a .bib file."""
    return set(re.findall(r"@\w+\{(\w+)\s*,", bib_path.read_text()))


def scan_file(path: Path) -> dict[str, list[int]]:
    """Return ``{key: [line_numbers]}`` for every citation in *path*."""
    hits: dict[str, list[int]] = {}
    pattern = PY_CITE if path.suffix == ".py" else MD_CITE
    for lineno, line in enumerate(path.read_text().splitlines(), start=1):
        for m in pattern.finditer(line):
            hits.setdefault(m.group(1), []).append(lineno)
    return hits


def main() -> int:
    if not BIB_FILE.exists():
        print(f"ERROR: {BIB_FILE} not found", file=sys.stderr)
        return 1

    bib_keys = parse_bib_keys(BIB_FILE)
    print(f"📚 {len(bib_keys)} keys in {BIB_FILE.relative_to(REPO)}")

    # Collect all citations across the repo
    used_keys: set[str] = set()
    dangling: list[tuple[str, str, list[int]]] = []

    source_files = list((REPO / "src").rglob("*.py")) + list((REPO / "docs").rglob("*.md"))

    for path in sorted(source_files):
        hits = scan_file(path)
        for key, lines in hits.items():
            used_keys.add(key)
            if key not in bib_keys:
                dangling.append((str(path.relative_to(REPO)), key, lines))

    # Report
    orphaned = bib_keys - used_keys
    ok = True

    if dangling:
        ok = False
        print("\n❌ Dangling citations (used but NOT in .bib):")
        for filepath, key, lines in dangling:
            print(f"   {filepath}:{','.join(map(str, lines))}  →  {key}")

    if orphaned:
        print(f"\n⚠️  Orphaned bib keys (defined but never cited): {', '.join(sorted(orphaned))}")

    if ok:
        print(f"\n✅ All {len(used_keys)} citations resolve to a bib key.")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
