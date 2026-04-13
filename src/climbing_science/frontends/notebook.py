"""Jupyter notebook helpers — plots, benchmarks, and DataFrame export.

Optional dependency on **matplotlib** (for plots) and **pandas**
(for DataFrame export).  All functions degrade gracefully when these
packages are not installed by raising an ``ImportError`` with a helpful
message.

Usage::

    from climbing_science.frontends import notebook

    notebook.plot_strength_benchmark(mvc_bw_ratio=1.35)
    notebook.plot_rohmert_curve()
    notebook.plot_force_session(values, sample_rate_hz=80)

References:
    Hörst (2016) :cite:`horst2016` — strength benchmarks.
    Rohmert (1960) :cite:`rohmert1960` — isometric fatigue curve.
    Giles et al. (2006) :cite:`giles2006` — MVC-7 protocol.
    Banaszczyk (2020) :cite:`banaszczyk2020` — benchmark synthesis.
"""

from __future__ import annotations

__all__ = [
    "plot_force_session",
    "plot_rohmert_curve",
    "plot_strength_benchmark",
    "plot_protocol_comparison",
    "session_to_dataframe",
]


def _require_matplotlib():
    """Import and return matplotlib.pyplot, raising clear error if missing."""
    try:
        import matplotlib.pyplot as plt

        return plt
    except ImportError:
        raise ImportError(
            "matplotlib is required for plotting.  Install it with:  pip install climbing-science[plot]"
        ) from None


def _require_pandas():
    """Import and return pandas, raising clear error if missing."""
    try:
        import pandas as pd

        return pd
    except ImportError:
        raise ImportError("pandas is required for DataFrame export.  Install it with:  pip install pandas") from None


# ---------------------------------------------------------------------------
# Force session plot
# ---------------------------------------------------------------------------


def plot_force_session(
    values: list[float],
    sample_rate_hz: float = 80.0,
    title: str = "Force–Time Curve",
    peaks: list | None = None,
    figsize: tuple[float, float] = (12, 5),
    show: bool = True,
):
    """Plot a force–time curve with optional peak markers.

    Args:
        values: Force values in kg.
        sample_rate_hz: Sampling rate in Hz.
        title: Plot title.
        peaks: List of :class:`~climbing_science.signal.Peak` objects
            to highlight.
        figsize: Figure size (width, height) in inches.
        show: Whether to call ``plt.show()``.

    Returns:
        matplotlib Figure object.

    References:
        Levernier & Laffaye (2019) :cite:`levernier2019`.
    """
    plt = _require_matplotlib()

    time_s = [i / sample_rate_hz for i in range(len(values))]
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(time_s, values, color="#5B21B6", linewidth=0.8, label="Force")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Force (kg)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)

    if peaks:
        for p in peaks:
            t_peak = p.peak_idx / sample_rate_hz
            ax.axvspan(
                p.start_idx / sample_rate_hz,
                p.end_idx / sample_rate_hz,
                alpha=0.15,
                color="orange",
            )
            ax.plot(t_peak, p.peak_value, "rv", markersize=8)

    ax.legend()
    plt.tight_layout()
    if show:
        plt.show()
    return fig


# ---------------------------------------------------------------------------
# Rohmert fatigue curve
# ---------------------------------------------------------------------------


_ROHMERT_MODELS = {
    "beginner": {"a": -1.5, "b": 0.5},
    "intermediate": {"a": -1.2, "b": 0.618},
    "expert": {"a": -0.9, "b": 0.7},
}


def plot_rohmert_curve(
    models: list[str] | None = None,
    figsize: tuple[float, float] = (10, 6),
    show: bool = True,
):
    """Plot Rohmert isometric fatigue curves.

    Shows time-to-failure vs. %MVC for different fitness models.

    Args:
        models: Model names to plot (default: all three).
        figsize: Figure size.
        show: Whether to call ``plt.show()``.

    Returns:
        matplotlib Figure object.

    References:
        Rohmert (1960) :cite:`rohmert1960`,
        Frey-Law & Avin (2010).
    """
    plt = _require_matplotlib()

    if models is None:
        models = list(_ROHMERT_MODELS.keys())

    fig, ax = plt.subplots(figsize=figsize)
    colors = {"beginner": "#EF4444", "intermediate": "#F59E0B", "expert": "#10B981"}

    pct_range = [p / 100.0 for p in range(15, 96)]

    for model_name in models:
        if model_name not in _ROHMERT_MODELS:
            continue
        params = _ROHMERT_MODELS[model_name]
        times = []
        pcts = []
        for pct in pct_range:
            # Rohmert: t_max = a * ln(pct) + b  (simplified)
            # Using the library's rohmert_conversion to derive time
            t = params["b"] / (pct ** (-params["a"]))
            if 0 < t < 600:
                times.append(t)
                pcts.append(pct * 100)

        color = colors.get(model_name, "#6B7280")
        ax.plot(pcts, times, linewidth=2, color=color, label=model_name.capitalize())

    ax.set_xlabel("% MVC")
    ax.set_ylabel("Time to Failure (s)")
    ax.set_title("Rohmert Isometric Fatigue Curve")
    ax.legend()
    ax.grid(True, alpha=0.3)
    ax.set_xlim(15, 100)
    ax.set_ylim(0, 300)
    plt.tight_layout()
    if show:
        plt.show()
    return fig


# ---------------------------------------------------------------------------
# Strength benchmark
# ---------------------------------------------------------------------------

# MVC/BW benchmarks (synthesised from public sources)
_BENCHMARKS = [
    (0.8, "Beginner", "#94A3B8"),
    (1.0, "Intermediate", "#F59E0B"),
    (1.3, "Advanced", "#10B981"),
    (1.6, "Elite", "#8B5CF6"),
    (2.0, "World Class", "#EF4444"),
]


def plot_strength_benchmark(
    mvc_bw_ratio: float | None = None,
    figsize: tuple[float, float] = (10, 4),
    show: bool = True,
):
    """Plot MVC/BW ratio against benchmark categories.

    Args:
        mvc_bw_ratio: Your MVC/BW ratio to highlight (optional).
        figsize: Figure size.
        show: Whether to call ``plt.show()``.

    Returns:
        matplotlib Figure object.

    References:
        Hörst (2016) :cite:`horst2016` — Table 4.2.
        Banaszczyk 2020 (:cite:`banaszczyk2020`).
    """
    plt = _require_matplotlib()

    fig, ax = plt.subplots(figsize=figsize)
    [b[1] for b in _BENCHMARKS]
    thresholds = [b[0] for b in _BENCHMARKS]
    [b[2] for b in _BENCHMARKS]

    # Horizontal bar chart of thresholds
    for i, (thresh, label, color) in enumerate(_BENCHMARKS):
        width = (thresholds[i + 1] - thresh) if i < len(thresholds) - 1 else 0.4
        ax.barh(0, width, left=thresh, height=0.6, color=color, alpha=0.7, edgecolor="white")
        ax.text(thresh + width / 2, 0, label, ha="center", va="center", fontsize=9, fontweight="bold")

    if mvc_bw_ratio is not None:
        ax.axvline(mvc_bw_ratio, color="#1E293B", linewidth=3, linestyle="--")
        ax.text(
            mvc_bw_ratio,
            0.4,
            f"You: {mvc_bw_ratio:.2f}",
            ha="center",
            fontsize=11,
            fontweight="bold",
        )

    ax.set_xlabel("MVC / BW Ratio")
    ax.set_xlim(0.5, 2.5)
    ax.set_yticks([])
    ax.set_title("Finger Strength Benchmark")
    ax.grid(True, axis="x", alpha=0.3)
    plt.tight_layout()
    if show:
        plt.show()
    return fig


# ---------------------------------------------------------------------------
# Protocol comparison
# ---------------------------------------------------------------------------


def plot_protocol_comparison(
    mvc7_kg: float,
    body_weight_kg: float,
    figsize: tuple[float, float] = (12, 6),
    show: bool = True,
):
    """Compare hangboard protocols by training load.

    Shows added weight and TUT for common protocols given your MVC-7.

    Args:
        mvc7_kg: MVC-7 total force in kg.
        body_weight_kg: Body weight in kg.
        figsize: Figure size.
        show: Whether to call ``plt.show()``.

    Returns:
        matplotlib Figure object.

    References:
        López-Rivera (2012) :cite:`lopezrivera2012`,
        Hörst (2016) :cite:`horst2016`.
    """
    plt = _require_matplotlib()
    from climbing_science.load import tut_per_session

    protocols = [
        {"name": "MaxHang 90%", "intensity": 0.90, "sets": 3, "reps": 1, "hang_s": 10, "rest_s": 180},
        {"name": "MaxHang 85%", "intensity": 0.85, "sets": 5, "reps": 1, "hang_s": 10, "rest_s": 180},
        {"name": "Repeater 60%", "intensity": 0.60, "sets": 4, "reps": 6, "hang_s": 7, "rest_s": 3},
        {"name": "IntHang 70%", "intensity": 0.70, "sets": 4, "reps": 4, "hang_s": 7, "rest_s": 3},
        {"name": "Density 50%", "intensity": 0.50, "sets": 3, "reps": 8, "hang_s": 7, "rest_s": 3},
    ]

    names = []
    added_weights = []
    tuts = []

    for p in protocols:
        target_force = mvc7_kg * p["intensity"]
        added = target_force - body_weight_kg
        tut = tut_per_session(
            hang_duration_sec=p["hang_s"],
            reps_per_set=p["reps"],
            num_sets=p["sets"],
        )
        names.append(p["name"])
        added_weights.append(added)
        tuts.append(tut)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize)

    colors = ["#8B5CF6" if w >= 0 else "#EF4444" for w in added_weights]
    ax1.barh(names, added_weights, color=colors, alpha=0.8)
    ax1.set_xlabel("Added Weight (kg)")
    ax1.set_title("Training Load")
    ax1.axvline(0, color="#94A3B8", linewidth=1)
    ax1.grid(True, axis="x", alpha=0.3)

    ax2.barh(names, tuts, color="#10B981", alpha=0.8)
    ax2.set_xlabel("TUT (seconds)")
    ax2.set_title("Time Under Tension per Session")
    ax2.grid(True, axis="x", alpha=0.3)

    plt.suptitle(f"Protocol Comparison (MVC-7: {mvc7_kg} kg, BW: {body_weight_kg} kg)")
    plt.tight_layout()
    if show:
        plt.show()
    return fig


# ---------------------------------------------------------------------------
# DataFrame export
# ---------------------------------------------------------------------------


def session_to_dataframe(
    values: list[float],
    sample_rate_hz: float = 80.0,
    columns: dict[str, str] | None = None,
):
    """Convert force data to a pandas DataFrame.

    Args:
        values: Force values in kg.
        sample_rate_hz: Sampling rate in Hz.
        columns: Column name mapping (default: ``{"time": "time_s",
            "force": "force_kg"}``).

    Returns:
        pandas DataFrame with time and force columns.

    Raises:
        ImportError: If pandas is not installed.

    References:
        Levernier & Laffaye (2019) :cite:`levernier2019`
        — force-time data format conventions.
    """
    pd = _require_pandas()

    if columns is None:
        columns = {"time": "time_s", "force": "force_kg"}

    time_col = columns.get("time", "time_s")
    force_col = columns.get("force", "force_kg")

    time_s = [i / sample_rate_hz for i in range(len(values))]

    return pd.DataFrame({time_col: time_s, force_col: values})
