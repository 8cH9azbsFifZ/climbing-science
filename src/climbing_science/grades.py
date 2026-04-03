"""Grade conversion between climbing grading systems.

Supports: UIAA, French (sport), YDS, V-Scale (Hueco), Fontainebleau (boulder).
Based on the IRCRA position statement (Draper et al. 2015, :cite:`draper2015`).

Every grade maps to an internal difficulty index (0–100) which serves as the
canonical comparison axis across systems.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Optional

__all__ = [
    "GradeSystem",
    "Grade",
    "convert",
    "parse",
    "compare",
    "difficulty_index",
]


class GradeSystem(str, Enum):
    """Supported grading systems."""

    UIAA = "uiaa"
    FRENCH = "french"
    YDS = "yds"
    V_SCALE = "v_scale"
    FONT = "font"


# ---------------------------------------------------------------------------
# Internal grade table
# ---------------------------------------------------------------------------
# Each row: (difficulty_index, uiaa, french, yds, v_scale, font)
# Sources:
#   - Draper et al. 2015 (IRCRA comparative grading scales, :cite:`draper2015`)
#   - Supplemented with commonly accepted correspondences
#
# Route grades and boulder grades overlap in difficulty_index but represent
# different disciplines.  v_scale and font are None for pure route grades
# at the lower end, and vice versa.
# ---------------------------------------------------------------------------

_GRADE_TABLE: list[tuple[int, str, str, str, Optional[str], Optional[str]]] = [
    # idx, uiaa,  french, yds,     v_scale, font
    (10, "III", "2", "5.3", None, None),
    (14, "IV", "3", "5.5", None, None),
    (18, "V", "4a", "5.6", None, None),
    (22, "V+", "4b", "5.7", None, None),
    (26, "VI-", "4c", "5.8", None, None),
    (30, "VI", "5a", "5.9", None, "3"),
    (33, "VI+", "5b", "5.10a", "V0", "4"),
    (36, "VII-", "5c", "5.10b", "V0+", "4+"),
    (39, "VII", "5c+", "5.10c", "V1", "5"),
    (42, "VII+", "6a", "5.10d", "V2", "5+"),
    (45, "VIII-", "6a+", "5.11a", "V3", "6A"),
    (48, "VIII", "6b", "5.11b", "V3+", "6A+"),
    (51, "VIII+", "6b+", "5.11c", "V4", "6B"),
    (54, "IX-", "6c", "5.11d", "V4+", "6B+"),
    (57, "IX", "6c+", "5.12a", "V5", "6C"),
    (59, "IX+", "7a", "5.12b", "V5+", "6C+"),
    (62, "X-", "7a+", "5.12c", "V6", "7A"),
    (65, "X", "7b", "5.12d", "V7", "7A+"),
    (68, "X+", "7b+", "5.13a", "V8", "7B"),
    (70, "X+/XI-", "7c", "5.13b", "V8+", "7B+"),
    (73, "XI-", "7c+", "5.13c", "V9", "7C"),
    (76, "XI", "8a", "5.13d", "V10", "7C+"),
    (78, "XI+", "8a+", "5.14a", "V11", "8A"),
    (81, "XI+/XII-", "8b", "5.14b", "V12", "8A+"),
    (84, "XII-", "8b+", "5.14c", "V13", "8B"),
    (86, "XII", "8c", "5.14d", "V14", "8B+"),
    (89, "XII+", "8c+", "5.15a", "V15", "8C"),
    (92, "XII+/XIII-", "9a", "5.15b", "V16", "8C+"),
    (94, "XIII-", "9a+", "5.15c", "V17", "9A"),
]

# Build lookup dicts: system -> {normalised_grade_str: row_index}
_SYSTEM_COL = {
    GradeSystem.UIAA: 1,
    GradeSystem.FRENCH: 2,
    GradeSystem.YDS: 3,
    GradeSystem.V_SCALE: 4,
    GradeSystem.FONT: 5,
}

_LOOKUP: dict[GradeSystem, dict[str, int]] = {}
for _sys, _col in _SYSTEM_COL.items():
    _LOOKUP[_sys] = {}
    for _i, _row in enumerate(_GRADE_TABLE):
        _val = _row[_col]
        if _val is not None:
            _LOOKUP[_sys][_val.lower()] = _i

# Regex patterns for auto-detection
_PATTERNS: list[tuple[GradeSystem, re.Pattern[str]]] = [
    (GradeSystem.YDS, re.compile(r"^5\.\d{1,2}[a-d]?$", re.IGNORECASE)),
    (GradeSystem.V_SCALE, re.compile(r"^V\d{1,2}\+?$", re.IGNORECASE)),
    (GradeSystem.FONT, re.compile(r"^\d[A-C]\+?$")),  # uppercase only → Font
    (GradeSystem.FRENCH, re.compile(r"^\d[a-c]\+?$")),  # lowercase only → French
    (GradeSystem.UIAA, re.compile(r"^[IVX]{1,5}[-+]?(/[IVX]{1,5}[-+]?)?$")),
]


class Grade:
    """A climbing grade with its system and difficulty index.

    Attributes:
        raw: The original grade string as provided.
        system: The grading system this grade belongs to.
        index: Internal difficulty index (0–100).

    References:
        Draper et al. 2015 (:cite:`draper2015`)
    """

    def __init__(self, raw: str, system: GradeSystem, index: int) -> None:
        self.raw = raw
        self.system = system
        self.index = index

    def __repr__(self) -> str:
        return f"Grade({self.raw!r}, {self.system.value}, idx={self.index})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Grade):
            return NotImplemented
        return self.index == other.index

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Grade):
            return NotImplemented
        return self.index < other.index

    def __le__(self, other: object) -> bool:
        if not isinstance(other, Grade):
            return NotImplemented
        return self.index <= other.index

    def __hash__(self) -> int:
        return hash((self.system, self.raw.lower()))


def _find_row(grade_str: str, system: GradeSystem) -> int:
    """Return the row index in _GRADE_TABLE for the given grade string.

    Raises:
        ValueError: If grade_str is not found in the given system.
    """
    normalised = grade_str.strip().lower()
    lookup = _LOOKUP.get(system)
    if lookup is None:
        raise ValueError(f"Unknown system: {system}")
    idx = lookup.get(normalised)
    if idx is None:
        raise ValueError(
            f"Grade '{grade_str}' not found in {system.value} system. "
            f"Known grades: {', '.join(k for k in lookup)}"
        )
    return idx


def difficulty_index(grade_str: str, system: GradeSystem) -> int:
    """Return the numeric difficulty index (0–100) for a grade.

    The index provides a system-independent, monotonically increasing
    measure of route/boulder difficulty.

    Args:
        grade_str: Grade string (e.g. "7a", "V5", "5.12a").
        system: The grading system of the input.

    Returns:
        Integer difficulty index.

    References:
        Draper et al. 2015 — IRCRA comparative grading scales
        (:cite:`draper2015`).
    """
    row_idx = _find_row(grade_str, system)
    return _GRADE_TABLE[row_idx][0]


def convert(grade_str: str, from_system: GradeSystem, to_system: GradeSystem) -> str:
    """Convert a grade from one system to another.

    Uses the IRCRA correspondence table.  If the target system does not
    have an equivalent at the same difficulty (e.g. converting a low route
    grade to V-Scale), raises ``ValueError``.

    Args:
        grade_str: Grade string in the source system.
        from_system: Source grading system.
        to_system: Target grading system.

    Returns:
        Grade string in the target system.

    Raises:
        ValueError: If grade not found or no equivalent exists.

    References:
        Draper et al. 2015 (:cite:`draper2015`).

    Examples:
        >>> convert("7a", GradeSystem.FRENCH, GradeSystem.YDS)
        '5.12b'
        >>> convert("V5", GradeSystem.V_SCALE, GradeSystem.UIAA)
        'IX'
    """
    row_idx = _find_row(grade_str, from_system)
    target_col = _SYSTEM_COL[to_system]
    result = _GRADE_TABLE[row_idx][target_col]
    if result is None:
        raise ValueError(
            f"No {to_system.value} equivalent for {grade_str} ({from_system.value})"
        )
    return result


def parse(grade_str: str) -> Grade:
    """Auto-detect the grading system and return a Grade object.

    Detection order: YDS → V-Scale → Font → UIAA → French.

    Args:
        grade_str: Any common grade string (e.g. "7a", "V5", "5.12a", "VIII-").

    Returns:
        A Grade instance with system and difficulty index populated.

    Raises:
        ValueError: If the grade cannot be recognised.

    References:
        Draper et al. 2015 (:cite:`draper2015`).

    Examples:
        >>> parse("7a")
        Grade('7a', french, idx=59)
        >>> parse("V5")
        Grade('V5', v_scale, idx=57)
    """
    cleaned = grade_str.strip()
    for system, pattern in _PATTERNS:
        if pattern.match(cleaned):
            try:
                row_idx = _find_row(cleaned, system)
                return Grade(cleaned, system, _GRADE_TABLE[row_idx][0])
            except ValueError:
                continue
    raise ValueError(f"Cannot auto-detect grading system for '{grade_str}'")


def compare(a: str, b: str) -> int:
    """Compare two grades, potentially from different systems.

    Both grades are auto-detected via ``parse()``.

    Args:
        a: First grade string.
        b: Second grade string.

    Returns:
        -1 if a < b, 0 if equal, 1 if a > b.

    References:
        Draper et al. 2015 (:cite:`draper2015`).

    Examples:
        >>> compare("7a", "V5")
        1
        >>> compare("V4", "6b+")
        0
    """
    ga = parse(a)
    gb = parse(b)
    if ga.index < gb.index:
        return -1
    elif ga.index > gb.index:
        return 1
    return 0
