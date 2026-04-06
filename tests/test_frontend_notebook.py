"""Tests for climbing_science.frontends.notebook — Jupyter helpers.

Plotting tests only verify that figures are created without errors
(no visual assertions). DataFrame tests check structure and values.
"""

import pytest

from climbing_science.frontends.notebook import (
    plot_force_session,
    plot_protocol_comparison,
    plot_rohmert_curve,
    plot_strength_benchmark,
    session_to_dataframe,
)

# Skip all plotting tests if matplotlib not installed
plt = pytest.importorskip("matplotlib.pyplot")


# ---------------------------------------------------------------------------
# plot_force_session
# ---------------------------------------------------------------------------


class TestPlotForceSession:
    def test_basic_plot(self):
        values = [0.0] * 100 + [50.0] * 600 + [0.0] * 100
        fig = plot_force_session(values, sample_rate_hz=80.0, show=False)
        assert fig is not None
        plt.close(fig)

    def test_with_peaks(self):
        from climbing_science.signal import Peak

        values = [0.0] * 100 + [50.0] * 600 + [0.0] * 100
        peaks = [Peak(start_idx=100, end_idx=699, peak_idx=400, peak_value=50.0, duration_s=7.5, mean_value=50.0)]
        fig = plot_force_session(values, peaks=peaks, show=False)
        assert fig is not None
        plt.close(fig)

    def test_custom_title(self):
        fig = plot_force_session([10.0] * 100, title="My Test", show=False)
        assert fig is not None
        plt.close(fig)


# ---------------------------------------------------------------------------
# plot_rohmert_curve
# ---------------------------------------------------------------------------


class TestPlotRohmertCurve:
    def test_all_models(self):
        fig = plot_rohmert_curve(show=False)
        assert fig is not None
        plt.close(fig)

    def test_single_model(self):
        fig = plot_rohmert_curve(models=["expert"], show=False)
        assert fig is not None
        plt.close(fig)

    def test_unknown_model_ignored(self):
        fig = plot_rohmert_curve(models=["expert", "nonexistent"], show=False)
        assert fig is not None
        plt.close(fig)


# ---------------------------------------------------------------------------
# plot_strength_benchmark
# ---------------------------------------------------------------------------


class TestPlotStrengthBenchmark:
    def test_without_ratio(self):
        fig = plot_strength_benchmark(show=False)
        assert fig is not None
        plt.close(fig)

    def test_with_ratio(self):
        fig = plot_strength_benchmark(mvc_bw_ratio=1.35, show=False)
        assert fig is not None
        plt.close(fig)


# ---------------------------------------------------------------------------
# plot_protocol_comparison
# ---------------------------------------------------------------------------


class TestPlotProtocolComparison:
    def test_basic(self):
        fig = plot_protocol_comparison(mvc7_kg=92.0, body_weight_kg=72.0, show=False)
        assert fig is not None
        plt.close(fig)


# ---------------------------------------------------------------------------
# session_to_dataframe
# ---------------------------------------------------------------------------


class TestSessionToDataframe:
    def test_basic(self):
        pytest.importorskip("pandas")
        values = [10.0, 20.0, 30.0, 40.0]
        df = session_to_dataframe(values, sample_rate_hz=100.0)
        assert len(df) == 4
        assert "time_s" in df.columns
        assert "force_kg" in df.columns
        assert df["force_kg"].iloc[2] == pytest.approx(30.0)
        assert df["time_s"].iloc[1] == pytest.approx(0.01)

    def test_custom_columns(self):
        pytest.importorskip("pandas")
        df = session_to_dataframe([1.0, 2.0], columns={"time": "t", "force": "f"})
        assert "t" in df.columns
        assert "f" in df.columns
