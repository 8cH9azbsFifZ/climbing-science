# Grade Conversion — Science

## The IRCRA Standard

The International Rock Climbing Research Association (IRCRA) published a position
statement (Draper et al. 2015) standardising the comparison of climbing grades
across different systems worldwide.

## Supported Systems

| System | Region | Range | Example |
|--------|--------|-------|---------|
| **French** | Europe (sport) | 1 – 9c | 7a, 8b+ |
| **UIAA** | Central Europe | I – XIII | VII+, X- |
| **YDS** | North America | 5.0 – 5.15d | 5.12a, 5.14c |
| **V-Scale** (Hueco) | Worldwide (boulder) | V0 – V17 | V5, V10 |
| **Font** (Fontainebleau) | Europe (boulder) | 3 – 9A | 7A, 8B+ |

## Difficulty Index

All grades map to an internal **difficulty index** (0–100), which serves as the
canonical comparison axis. This allows cross-system comparison:

```python
from climbing_science.grades import parse, compare

# Are these the same difficulty?
print(compare("V5", "6c+"))  # → 0 (equal)
print(compare("8a", "V10"))  # → 0 (equal)
print(compare("7a", "V5"))   # → 1 (7a is harder)
```

## French ↔ Font Disambiguation

French sport grades and Fontainebleau boulder grades overlap in notation
(both use numbers + letters). The library disambiguates by **case**:

- **Lowercase** → French sport: `7a`, `6b+`, `8c`
- **Uppercase** → Font boulder: `7A`, `6B+`, `8C`

## Usage

```python
from climbing_science.grades import convert, GradeSystem

# French → YDS
print(convert("7a", GradeSystem.FRENCH, GradeSystem.YDS))  # → 5.12b

# V-Scale → UIAA
print(convert("V10", GradeSystem.V_SCALE, GradeSystem.UIAA))  # → XI
```

## References

- Draper, N. et al. (2015). *Comparative grading scales, statistical analyses, climber descriptors and ability grouping: International Rock Climbing Research Association position statement.* Sports Technology, 8(3–4), 88–94. \[cite:draper2015\]
