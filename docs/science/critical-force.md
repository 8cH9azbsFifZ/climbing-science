# Critical Force — Science

> *Critical Force (CF) is the climbing-specific equivalent of Critical Power:
> the maximum force that can be sustained indefinitely through aerobic metabolism.*

## Background

The Critical Power model (Jones et al. 2010) separates performance into two
components:

1. **Critical Force (CF)** — the aerobic ceiling, sustainable indefinitely
2. **W' (W-prime)** — the finite anaerobic work capacity above CF

For climbers, CF determines **endurance on a route**: how long you can hold on
during sustained sequences. W' determines how many **hard moves above CF** you
can do before falling.

## The Model

Total work above CF follows:

$$
W' = \int_0^{t_{lim}} (F(t) - CF) \, dt
$$

For constant-force efforts:

$$
t_{lim} = \frac{W'}{F - CF}
$$

Where:
- $F$ = applied force (must be > CF)
- $CF$ = critical force
- $W'$ = anaerobic capacity (in kg·s or N·s)
- $t_{lim}$ = time to exhaustion

## Test Protocol

The standard test uses **7/3 repeaters** (7 s hang, 3 s rest) at multiple
intensities until failure:

1. **Set 1:** 80% MVC-7 → hang until failure
2. **Rest:** 15–30 min full recovery
3. **Set 2:** 60% MVC-7 → hang until failure
4. **Rest:** 15–30 min full recovery
5. **Set 3:** 45% MVC-7 → hang until failure

Plot *force vs. 1/time-to-failure* → CF = y-intercept, W' = slope.

## CF/MVC-7 Ratio — The Diagnostic Key

| CF/MVC-7 Ratio | Interpretation | Training Priority |
|----------------|----------------|-------------------|
| > 50% | Endurance good → train strength | MaxHangs, limit bouldering |
| 35–50% | Balanced | Mixed training |
| < 35% | Endurance limiter → train endurance | Repeaters, ARC, SubHangs |

## Implementation

```python
# Coming in M2: endurance module
from climbing_science.endurance import critical_force

# From 7/3 repeater test data:
test_data = [
    {"force_pct_mvc": 80, "time_to_failure_sec": 45},
    {"force_pct_mvc": 60, "time_to_failure_sec": 180},
    {"force_pct_mvc": 45, "time_to_failure_sec": 600},
]

cf, w_prime = critical_force(test_data)
print(f"Critical Force: {cf}% MVC")
print(f"W': {w_prime} %MVC·s")
```

## References

- Jones, A.M. et al. (2010). *Critical power: implications for determination of VO2max and exercise tolerance.* Medicine and Science in Sports and Exercise, 42(10), 1876–1890. \[cite:jones2010\]
- Fryer, S. et al. (2018). *Forearm muscle oxidative capacity index predicts sport rock-climbing performance.* European Journal of Applied Physiology, 118(5), 1083–1091. \[cite:fryer2018\]
- Giles, L.V. et al. (2006). *The physiology of rock climbing.* \[cite:giles2006\]
