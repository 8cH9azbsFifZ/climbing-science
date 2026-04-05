# Edge Depth Correction

## Why Edge Depth Matters

Different hangboards and measurement devices use different edge depths.
A 20 mm edge is the most common standard, but devices may use 15 mm,
18 mm, 23 mm, or even deeper holds.  **Force measured on a narrow edge
is always lower** than on a wider edge — comparing raw numbers across
devices is therefore misleading without correction.

## The Linear Correction Model

Amca et al. (2012) showed that maximal grip force decreases approximately
linearly with decreasing edge depth.  The widely adopted model uses a
correction rate of **2.5 % per millimetre** relative to a 20 mm reference:

$$
F_{ref} = F_{measured} \times \left(1 + 0.025 \times (d_{ref} - d_{test})\right)
$$

where:

- $F_{ref}$ — equivalent force at reference edge depth
- $F_{measured}$ — force measured at test edge depth
- $d_{ref}$ — reference edge depth (default: 20 mm)
- $d_{test}$ — test edge depth

### Examples

- Measured **50 kg on 15 mm** → $50 \times 1.125 = 56.25$ kg at 20 mm
- Measured **50 kg on 25 mm** → $50 \times 0.875 = 43.75$ kg at 20 mm

## Correction Factor Table

Use this table for quick pen-and-paper corrections:

| Edge (mm) | Factor | Equivalent of 50 kg |
|-----------|--------|---------------------|
| 10 | 1.250 | 62.5 kg |
| 12 | 1.200 | 60.0 kg |
| 14 | 1.150 | 57.5 kg |
| 15 | 1.125 | 56.3 kg |
| 16 | 1.100 | 55.0 kg |
| 18 | 1.050 | 52.5 kg |
| 20 | 1.000 | 50.0 kg |
| 22 | 0.950 | 47.5 kg |
| 23 | 0.925 | 46.3 kg |
| 25 | 0.875 | 43.8 kg |
| 28 | 0.800 | 40.0 kg |
| 30 | 0.750 | 37.5 kg |
| 35 | 0.625 | 31.3 kg |

## Limitations

The linear 2.5 %/mm model is an approximation that works well in the
**10–30 mm range**.  At very small edges (< 8 mm), biomechanical factors
(skin pain, tendon geometry) dominate and the relationship becomes
non-linear.  At very deep edges (> 35 mm), the correction becomes
less meaningful as grip posture changes fundamentally.

!!! tip "Best Practice"
    Always test on a **20 mm edge** when possible. This is the IRCRA and
    Lattice Training standard.  If you must use a different edge, apply
    the correction before comparing with published benchmarks.

## Usage

```python
from climbing_science.edge_depth import (
    correction_factor,
    normalize_to_reference,
    convert_force,
)

# Normalise a 15 mm measurement to 20 mm
f_20 = normalize_to_reference(50.0, edge_mm=15.0)  # → 56.25

# Convert between any two edges
f_25 = convert_force(50.0, from_edge_mm=15.0, to_edge_mm=25.0)  # → 64.29
```

## References

- Amca A. M., Vigouroux L., Aritan S., Berton E. (2012).
  *Effect of hold depth and grip technique on maximal finger forces
  in rock climbing.* Journal of Sports Sciences, 30(7), 669–677.
  [:doi:`10.1080/02640414.2012.658845`](https://doi.org/10.1080/02640414.2012.658845)
