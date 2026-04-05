#!/usr/bin/env python3
"""Grade conversion examples.

Demonstrates converting between UIAA, French, YDS (route) and
Font, V-Scale (boulder) grading systems.
"""

from climbing_science.grades import (
    all_grades,
    compare,
    convert,
    from_index,
    parse,
)

# --- Basic conversion ---
print("=== Route Grade Conversion ===")
print(f"UIAA VII+ → French: {convert('VII+', 'UIAA', 'French')}")
print(f"French 7a → YDS:    {convert('7a', 'French', 'YDS')}")
print(f"YDS 5.12a → UIAA:  {convert('5.12a', 'YDS', 'UIAA')}")

print("\n=== Boulder Grade Conversion ===")
print(f"Font 7A → V-Scale:  {convert('7A', 'Font', 'V-Scale')}")
print(f"V5 → Font:          {convert('V5', 'V-Scale', 'Font')}")

# --- Auto-detect system from grade string ---
print("\n=== Auto-Detection (parse) ===")
for grade_str in ["6b+", "5.11a", "VII", "7A+", "V4"]:
    g = parse(grade_str)
    print(f"  '{grade_str}' → system={g.system.value}, index={g.difficulty_index}")

# --- Compare grades across systems ---
print("\n=== Cross-System Comparison ===")
pairs = [("VII+", "6b+"), ("5.12a", "7a+"), ("V5", "6C")]
for a, b in pairs:
    result = compare(a, b)
    symbol = "=" if result == 0 else (">" if result > 0 else "<")
    print(f"  {a} {symbol} {b}")

# --- Reverse lookup: IRCRA index → grade ---
print("\n=== Index → Grade (from_index) ===")
for idx in [15, 20, 25, 30]:
    print(f"  IRCRA {idx}: UIAA={from_index(idx, 'UIAA')}, French={from_index(idx, 'French')}, YDS={from_index(idx, 'YDS')}")

# --- Full grade table ---
print("\n=== All French Route Grades ===")
for g in all_grades("French"):
    print(f"  {g.value:>4}  (IRCRA {g.difficulty_index})")
