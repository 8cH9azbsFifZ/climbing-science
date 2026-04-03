# Hangboard Training & the Rohmert Curve

## The Problem

You tested your MVC-7 at 125% BW on a 20 mm edge. But in training, you often
use different hold times — 10-second hangs, 5-second hangs, or 3-second explosive
pulls.  **How do you compare these?**

This is exactly what Rohmert's endurance curve solves.

## Rohmert's Insight

Walter Rohmert (1960) discovered that the maximum time a muscle can sustain a
static contraction follows a predictable curve.  At 100% MVC, you can hold for
~0 seconds.  At 15% MVC, you can hold essentially forever.

The `rohmert_conversion()` function normalises any (force × duration) pair to
its MVC-7 equivalent — the standard we use for all benchmarks.

## Practical Example

You can hang 10 seconds at bodyweight (100% BW) on an 18 mm edge, but can't
do a proper 7-second max hang.  What's your MVC-7 equivalent?

```python
from climbing_science.strength import rohmert_conversion

# You held 80% of your max for 10 seconds.
# What force could you sustain for exactly 7 seconds?
mvc7_equivalent = rohmert_conversion(
    force_percent_mvc=80.0,
    duration_sec=10.0,
    target_duration_sec=7.0,
)
print(f"MVC-7 equivalent: {mvc7_equivalent}% MVC")
# → ~84.6% MVC — you're stronger than you think for 7s
```

## Training Load Implications

| Protocol | Hang Time | Typical %MVC | Rohmert MVC-7 Equiv. |
|----------|-----------|-------------|---------------------|
| MaxHangs (López) | 10 s | 85–95% | → 89–98% MVC-7 |
| IntHangs | 7 s | 70–80% | = 70–80% MVC-7 |
| Density Hangs (Nelson) | 20–40 s | 40–60% | → 50–72% MVC-7 |
| ARC / Endurance | 60+ s | 20–35% | → 30–48% MVC-7 |

## Further Reading

- **[The Math: Rohmert Curve](../science/rohmert-curve.md)** — Full formula, three model variants, interactive plot
- **[Grade Prediction](grade-prediction.md)** — How MVC-7 maps to climbing grades
- **API Reference**: [`rohmert_conversion()`](../api/strength.md)

## References

- Rohmert, W. (1960). *Ermittlung von Erholungspausen für statische Arbeit des Menschen.* \[cite:rohmert1960\]
- López-Rivera, E. (2014). *Entrenamiento en escalada.* \[cite:lopez2014\]
