# The Rohmert Curve — Science

> *"The relationship between force and endurance time for static contractions
> is one of the most robust findings in exercise physiology."*
> — Rohmert, 1960

## Background

Walter Rohmert published his seminal work on static muscle endurance in 1960.
He found that the maximum time a muscle can sustain a given force follows a
hyperbolic relationship: higher force → dramatically shorter hold time.

This curve is fundamental to climbing science because hangboard protocols
use different hold durations (3 s, 7 s, 10 s, 30 s, 60 s), and we need a
way to **compare and normalise** across them.

## The Formula

The maximum hold time $t_{max}$ at a relative force $f_{rel}$ (where 1.0 = 100% MVC):

$$
t_{max} = \left( -1.5 + \left( \frac{2.1}{f_{rel} - 0.15} \right)^{0.618} \right) \times 60 \quad \text{[seconds]}
$$

**Domain:** $0.15 < f_{rel} < 1.0$

- At $f_{rel} = 1.0$ (100% MVC): $t_{max} \approx 0$ s (instantaneous failure)
- At $f_{rel} = 0.15$ (15% MVC): $t_{max} \to \infty$ (sustainable indefinitely)
- At $f_{rel} = 0.50$ (50% MVC): $t_{max} \approx 72$ s

## Key Properties

| Force (%MVC) | Max Hold Time | Application |
|-------------|--------------|-------------|
| 95% | ~3 s | Limit bouldering move |
| 85% | ~12 s | MaxHangs (López) |
| 75% | ~30 s | IntHangs |
| 60% | ~80 s | SubHangs |
| 45% | ~180 s | Endurance repeaters |
| 30% | ~480 s | ARC training |

## Three Model Variants

### 1. Rohmert Original (1960)

The formula above. Based on forearm flexor data. Most commonly cited.

### 2. Sjøgaard Extension (1986)

Modified coefficients for smaller muscle groups:

$$
t_{max} = \left( \frac{1.0}{f_{rel} - 0.14} \right)^{2.4} \quad \text{[seconds]}
$$

### 3. Linear Approximation (for quick calculations)

For the range $0.50 \leq f_{rel} \leq 0.95$ (the practical training range):

$$
t_{max} \approx 240 \times (1 - f_{rel})^{1.6} \quad \text{[seconds]}
$$

## Implementation

```python
from climbing_science.strength import rohmert_conversion

# Scenario: You did a 10-second hang at 80% MVC.
# What's the equivalent at the standard 7-second duration?
equivalent = rohmert_conversion(
    force_percent_mvc=80.0,
    duration_sec=10.0,
    target_duration_sec=7.0,
)
print(f"{equivalent}% MVC")  # → ~84.6% MVC
```

### Comparison Across Protocols

```python
from climbing_science.strength import rohmert_conversion

protocols = [
    ("MaxHang 10s @85%", 85.0, 10.0),
    ("IntHang 7s @75%", 75.0, 7.0),
    ("SubHang 30s @50%", 50.0, 30.0),
    ("Density 20s @60%", 60.0, 20.0),
]

print("Protocol                | %MVC  | MVC-7 Equivalent")
print("------------------------|-------|------------------")
for name, pct, dur in protocols:
    equiv = rohmert_conversion(pct, dur, 7.0)
    print(f"{name:24s}| {pct:5.1f} | {equiv:5.1f}%")
```

## References

- Rohmert, W. (1960). *Ermittlung von Erholungspausen für statische Arbeit des Menschen.* Internationale Zeitschrift für angewandte Physiologie, 18(2), 123–164. \[cite:rohmert1960\]
- Sjøgaard, G. (1986). *Intramuscular changes during long-term contraction.* In: The Ergonomics of Working Postures, 136–143.
- Jones, A.M. et al. (2010). *Critical power: implications for VO2max and exercise tolerance.* \[cite:jones2010\]
