# Grade Conversion — Science

## The IRCRA Standard

The International Rock Climbing Research Association (IRCRA) published a position
statement (Draper et al. 2015) standardising the comparison of climbing grades
across different systems worldwide.

Every grade in this library maps to an **IRCRA difficulty index** (integers 1-35),
which serves as the canonical comparison axis.

## Two Domains

Climbing grades fall into two separate domains:

### Route Grades (lead / top-rope)

| System | Region | Range | Example |
|--------|--------|-------|---------|
| **UIAA** | Central Europe | I - XII+ | VII+, X- |
| **French** | Europe (sport) | 1 - 9c | 7a, 8b+ |
| **YDS** | North America | 5.0 - 5.15d | 5.12a, 5.14c |

### Boulder Grades

| System | Region | Range | Example |
|--------|--------|-------|---------|
| **Font** (Fontainebleau) | Europe | 3 - 9A | 7A, 8B+ |
| **V-Scale** (Hueco) | Worldwide | V0 - V17 | V5, V10 |

!!! warning "Domain Separation"
    Converting between route and boulder systems (e.g. French -> V-Scale)
    raises a `GradeDomainError`. Use `from_index()` for cross-domain
    difficulty comparison.

## Difficulty Index

All grades map to an **IRCRA difficulty index** (1-35), which allows
cross-system comparison:

```python
from climbing_science.grades import parse, compare

# Are these the same difficulty?
print(compare("V5", "6c+"))  # compares by IRCRA index
print(compare("8a", "V10"))  # cross-domain comparison works
```

## French vs Font Disambiguation

French sport grades and Fontainebleau boulder grades overlap in notation
(both use numbers + letters). The library disambiguates by **case**:

- **Lowercase** -> French sport: `7a`, `6b+`, `8c`
- **Uppercase** -> Font boulder: `7A`, `6B+`, `8C`

## Usage

```python
from climbing_science.grades import convert, RouteSystem, BoulderSystem

# Within route domain: French -> YDS
print(convert("7a", "French", "YDS"))  # -> "5.11d"

# Within boulder domain: V-Scale -> Font
print(convert("V5", "V-Scale", "Font"))  # -> "7A"

# Cross-domain via index
from climbing_science.grades import from_index, difficulty_index
idx = difficulty_index("7a", "French")
print(from_index(idx, BoulderSystem.V_SCALE))  # approximate boulder equivalent
```

## Primary Sources

| Source | Used for |
|--------|----------|
| Draper et al. 2015 | IRCRA numerical index (1-35) |
| CAI / Mandelli 2016 | UIAA official conversion tables |
| Mountain Project 2024 | Community consensus cross-check |
| Rockfax 2022 | European standard cross-check |

---

## Complete Grade Tables

These tables are the authoritative reference used by `climbing-science`.
Every conversion in the library is a lookup against these rows.
Print this page for pen-and-paper use.

### Route Grades (UIAA — French — YDS)

| Idx | UIAA | French | YDS |
|----:|------|--------|-----|
| 1 | I | 1 | 5.2 |
| 2 | II | 2 | 5.3 |
| 3 | III | 3 | 5.4 |
| 4 | III+ | 3+ | 5.4+ |
| 5 | IV | 4a | 5.5 |
| 6 | IV+ | 4b | 5.6 |
| 7 | V- | 4b+ | 5.6+ |
| 8 | V | 4c | 5.7 |
| 9 | V+ | 5a | 5.7+ |
| 10 | VI- | 5b | 5.8 |
| 11 | VI | 5c | 5.9 |
| 12 | VI+ | 6a | 5.10a |
| 13 | VII- | 6a+ | 5.10b |
| 14 | VII | 6b | 5.10c |
| 15 | VII+ | 6b+ | 5.10d |
| 16 | VIII- | 6c | 5.11a |
| 17 | VIII- | 6c+ | 5.11b |
| 18 | VIII | 7a | 5.11d |
| 19 | VIII+ | 7a+ | 5.12a |
| 20 | IX- | 7b | 5.12b |
| 21 | IX- | 7b+ | 5.12c |
| 22 | IX | 7c | 5.12d |
| 23 | IX+ | 7c+ | 5.13a |
| 24 | X- | 8a | 5.13b |
| 25 | X- | 8a+ | 5.13c |
| 26 | X | 8b | 5.13d |
| 27 | X+ | 8b+ | 5.14a |
| 28 | XI- | 8c | 5.14b |
| 29 | XI- | 8c+ | 5.14c |
| 30 | XI | 9a | 5.14d |
| 31 | XI+ | 9a+ | 5.15a |
| 32 | XII- | 9b | 5.15b |
| 33 | XII | 9b+ | 5.15c |
| 34 | XII+ | 9c | 5.15d |

### Boulder Grades (Font — V-Scale)

| Idx | Font | V-Scale |
|----:|------|---------|
| 11 | 3 | VB |
| 12 | 4- | V0- |
| 13 | 4 | V0 |
| 14 | 4+ | V0+ |
| 15 | 5 | V1 |
| 16 | 5+ | V2 |
| 17 | 6A | V3 |
| 18 | 6A+ | V3+ |
| 19 | 6B | V4 |
| 20 | 6B+ | V4+ |
| 21 | 6C | V5 |
| 22 | 6C+ | V5+ |
| 23 | 7A | V6 |
| 24 | 7A+ | V7 |
| 25 | 7B | V8 |
| 26 | 7B+ | V8+ |
| 27 | 7C | V9 |
| 28 | 7C+ | V10 |
| 29 | 8A | V11 |
| 30 | 8A+ | V12 |
| 31 | 8B | V13 |
| 32 | 8B+ | V14 |
| 33 | 8C | V15 |
| 34 | 8C+ | V16 |
| 35 | 9A | V17 |

### How to read the table

The **Difficulty Index** (Idx) is a shared scale from Draper et al. 2015.
Rows with the same index across both tables represent approximately equivalent
difficulty. For example, Idx 23 is **IX+ / 7c+ / 5.13a** on routes and
**7A / V6** in bouldering.

!!! tip "Pen-and-paper shortcut"
    To estimate your boulder grade from your route grade (or vice versa),
    find your grade in one table, note the index, then look up that index
    in the other table.
