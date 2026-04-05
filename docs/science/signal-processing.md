# Signal Processing

## Overview

Climbing force measurement devices (force gauges, load cells) produce
raw time-series data — a sequence of force values sampled at a fixed
rate (typically 40–200 Hz).  Before meaningful analysis, these raw
signals need processing: smoothing, peak detection, and feature
extraction.

The `climbing_science.signal` module provides these tools using **only
the Python standard library** — no NumPy or SciPy required.

## Smoothing

Raw force signals contain high-frequency noise from sensor vibration,
hand tremor, and electrical interference.  Smoothing reduces this
noise while preserving the underlying force profile.

Two methods are available:

- **Moving average** (default) — simple, symmetric, preserves signal
  timing.  A 50 ms window is recommended for climbing data.
- **Exponential moving average (EMA)** — gives more weight to recent
  values, better for real-time applications.

Levernier & Laffaye (2019) used a 50 ms smoothing window for
force-curve analysis in elite climbers.

## Peak Detection

A "peak" is a contiguous region where force exceeds a threshold for
a minimum duration.  The algorithm:

1. Scan the signal for values ≥ `min_force_kg`
2. Track contiguous above-threshold regions
3. Filter by `min_duration_s` to reject artefacts
4. Return start/end indices, peak value, mean value, and duration

This is essential for automatic segmentation of multi-rep recordings.

## Rate of Force Development (RFD)

RFD measures how quickly a climber can generate force — an important
performance indicator independent of maximal strength.

$$
\text{RFD} = \frac{\Delta F}{\Delta t} \quad \text{(kg/s)}
$$

Following Levernier & Laffaye (2019), RFD is calculated in the
**20–80 % window** of peak force to avoid noisy onset and plateau
regions.

!!! info "Sample Rate Requirement"
    For accurate RFD, a sampling rate of **≥ 80 Hz** is recommended.
    At 40 Hz, the time resolution (25 ms) limits RFD precision.

## MVC-7 Extraction

The **best 7-second average** is the gold standard for maximal finger
strength (MVC-7).  A sliding window scans the entire recording and
returns the highest average force over any 7-second interval.

```python
from climbing_science.signal import best_n_second_average

mvc7 = best_n_second_average(force_data, sample_rate_hz=80.0, n_seconds=7.0)
```

## Force Impulse

Force impulse (∫F dt, in kg·s) is the integral of force over time.
It connects to the **W′ (W-prime)** concept in the Critical Force
model (Jones et al. 2010) — the total amount of work above Critical
Force that can be performed before failure.

## Repeater Segmentation

For intermittent protocols (e.g., 7/3 repeaters at various intensities),
`segment_repeaters()` automatically identifies individual work phases
and extracts per-rep statistics.

```python
from climbing_science.signal import segment_repeaters

reps = segment_repeaters(force_data, sample_rate_hz=80.0,
                         work_s=7.0, rest_s=3.0)
for r in reps:
    print(f"Rep {r.rep_number}: {r.mean_force_kg:.1f} kg, "
          f"{r.work_duration_s:.1f} s")
```

## References

- Levernier G., Laffaye G. (2019). *Four weeks of finger grip training
  increases the rate of force development and the maximal force in elite
  and top world-ranking climbers.* JSCR, 33(9), 2471–2480.
  [:doi:`10.1519/JSC.0000000000002230`](https://doi.org/10.1519/JSC.0000000000002230)

- Jones A. M. et al. (2010). *Critical power: implications for determination
  of VO2max and exercise tolerance.* MSSE, 42(10), 1876–1890.
  [:doi:`10.1249/MSS.0b013e3181d9cf7f`](https://doi.org/10.1249/MSS.0b013e3181d9cf7f)

- Fryer S. et al. (2018). *Forearm muscle oxidative capacity index predicts
  sport rock-climbing performance.* Eur J Appl Physiol, 118(5), 1083–1091.
  [:doi:`10.1007/s00421-018-3839-6`](https://doi.org/10.1007/s00421-018-3839-6)
