"""Tests for climbing_science.edge_depth — edge depth correction."""

import pytest

from climbing_science.edge_depth import (
    CORRECTION_RATE,
    MAX_EDGE_MM,
    MIN_EDGE_MM,
    REFERENCE_EDGE_MM,
    convert_force,
    correction_factor,
    estimate_force_at_depth,
    normalize_to_reference,
)

# ---------------------------------------------------------------------------
# correction_factor
# ---------------------------------------------------------------------------


class TestCorrectionFactor:
    """Tests for correction_factor()."""

    def test_identity_at_reference(self):
        assert correction_factor(20.0) == 1.0

    def test_15mm(self):
        assert correction_factor(15.0) == pytest.approx(1.125)

    def test_25mm(self):
        assert correction_factor(25.0) == pytest.approx(0.875)

    def test_10mm(self):
        assert correction_factor(10.0) == pytest.approx(1.25)

    def test_30mm(self):
        assert correction_factor(30.0) == pytest.approx(0.75)

    def test_custom_reference(self):
        # 15mm relative to 18mm reference
        expected = 1.0 + CORRECTION_RATE * (18.0 - 15.0)
        assert correction_factor(15.0, reference_mm=18.0) == pytest.approx(expected)

    def test_linearity(self):
        """Factor difference is constant per mm (linear model)."""
        d1 = correction_factor(15.0) - correction_factor(16.0)
        d2 = correction_factor(16.0) - correction_factor(17.0)
        d3 = correction_factor(19.0) - correction_factor(20.0)
        assert d1 == pytest.approx(d2)
        assert d2 == pytest.approx(d3)

    def test_edge_zero_raises(self):
        with pytest.raises(ValueError, match="must be > 0"):
            correction_factor(0.0)

    def test_edge_negative_raises(self):
        with pytest.raises(ValueError, match="must be > 0"):
            correction_factor(-5.0)

    def test_reference_zero_raises(self):
        with pytest.raises(ValueError, match="must be > 0"):
            correction_factor(20.0, reference_mm=0.0)

    def test_very_small_edge(self):
        """Model still works at small edges (though less accurate)."""
        f = correction_factor(MIN_EDGE_MM)
        assert f > 1.0

    def test_very_large_edge(self):
        f = correction_factor(MAX_EDGE_MM)
        assert f < 1.0


# ---------------------------------------------------------------------------
# convert_force
# ---------------------------------------------------------------------------


class TestConvertForce:
    """Tests for convert_force()."""

    def test_same_edge_identity(self):
        assert convert_force(50.0, 20.0, 20.0) == pytest.approx(50.0)

    def test_zero_force(self):
        assert convert_force(0.0, 15.0, 20.0) == 0.0

    def test_15_to_20(self):
        # 50kg at 15mm → 50 * 1.125 / 1.0 = 56.25 at 20mm
        assert convert_force(50.0, 15.0, 20.0) == pytest.approx(56.25)

    def test_20_to_15(self):
        # 56.25kg at 20mm → 56.25 * 1.0 / 1.125 = 50 at 15mm
        assert convert_force(56.25, 20.0, 15.0) == pytest.approx(50.0)

    def test_symmetry_roundtrip(self):
        """convert(convert(F, a, b), b, a) ≈ F."""
        original = 73.5
        intermediate = convert_force(original, 15.0, 20.0)
        recovered = convert_force(intermediate, 20.0, 15.0)
        assert recovered == pytest.approx(original)

    def test_15_to_25(self):
        """Direct conversion between two non-reference edges."""
        f = convert_force(50.0, 15.0, 25.0)
        # 50 * 1.125 / 0.875 = 64.2857...
        expected = 50.0 * correction_factor(15.0) / correction_factor(25.0)
        assert f == pytest.approx(expected)

    def test_negative_force_raises(self):
        with pytest.raises(ValueError, match="force must be >= 0"):
            convert_force(-10.0, 15.0, 20.0)

    def test_edge_zero_raises(self):
        with pytest.raises(ValueError, match="must be > 0"):
            convert_force(50.0, 0.0, 20.0)


# ---------------------------------------------------------------------------
# normalize_to_reference
# ---------------------------------------------------------------------------


class TestNormalizeToReference:
    """Tests for normalize_to_reference()."""

    def test_at_reference_unchanged(self):
        assert normalize_to_reference(50.0, 20.0) == pytest.approx(50.0)

    def test_15mm(self):
        assert normalize_to_reference(50.0, 15.0) == pytest.approx(56.25)

    def test_25mm(self):
        assert normalize_to_reference(50.0, 25.0) == pytest.approx(43.75)

    def test_custom_reference(self):
        result = normalize_to_reference(50.0, 15.0, reference_mm=18.0)
        expected = 50.0 * correction_factor(15.0, 18.0)
        assert result == pytest.approx(expected)

    def test_negative_force_raises(self):
        with pytest.raises(ValueError):
            normalize_to_reference(-1.0, 20.0)


# ---------------------------------------------------------------------------
# estimate_force_at_depth
# ---------------------------------------------------------------------------


class TestEstimateForceAtDepth:
    """Tests for estimate_force_at_depth()."""

    def test_at_reference_unchanged(self):
        assert estimate_force_at_depth(50.0, 20.0) == pytest.approx(50.0)

    def test_to_15mm(self):
        # Force at reference is 56.25 → at 15mm should be 50
        assert estimate_force_at_depth(56.25, 15.0) == pytest.approx(50.0)

    def test_roundtrip_with_normalize(self):
        """normalize then estimate back ≈ original."""
        original = 42.0
        normalised = normalize_to_reference(original, 15.0)
        recovered = estimate_force_at_depth(normalised, 15.0)
        assert recovered == pytest.approx(original)

    def test_to_25mm(self):
        result = estimate_force_at_depth(50.0, 25.0)
        expected = 50.0 / correction_factor(25.0)
        assert result == pytest.approx(expected)

    def test_negative_force_raises(self):
        with pytest.raises(ValueError):
            estimate_force_at_depth(-1.0, 20.0)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


class TestConstants:
    """Verify module constants match expected values."""

    def test_reference_edge(self):
        assert REFERENCE_EDGE_MM == 20.0

    def test_correction_rate(self):
        assert CORRECTION_RATE == 0.025

    def test_min_edge(self):
        assert MIN_EDGE_MM == 4.0

    def test_max_edge(self):
        assert MAX_EDGE_MM == 45.0
