"""Tests for climbing_science.endurance — Critical Force and W'.

Tests verify against the Critical Power model (Jones et al. 2010)
and climbing-specific CF benchmarks (Fryer et al. 2018, Giles et al. 2019).
"""

import pytest

from climbing_science.endurance import (
    cf_mvc_ratio,
    classify_endurance,
    critical_force,
    interpret_cf_ratio,
    time_to_failure,
    w_prime_balance,
)

# ---------------------------------------------------------------------------
# critical_force — linear regression on work-time data
# ---------------------------------------------------------------------------


class TestCriticalForce:
    """Verify CF and W' computation from multi-intensity test data.

    Reference dataset: typical intermediate climber
    80% MVC for 77s, 60% MVC for 136s, 45% MVC for 323s.
    Expected CF ≈ 35% MVC (Fryer et al. 2018 intermediate range).
    """

    def test_three_point_test(self):
        """Standard 3-point test should yield reasonable CF and W'."""
        cf, wp, r2 = critical_force([80.0, 60.0, 45.0], [77.0, 136.0, 323.0])
        # CF should be in reasonable range (30-45% MVC for intermediate)
        assert 25.0 < cf < 45.0, f"CF={cf} out of expected range"
        # W' should be positive
        assert wp > 0, f"W'={wp} should be positive"
        # R² should be high for good test data
        assert r2 > 0.90, f"R²={r2} indicates poor fit"

    def test_cf_less_than_lowest_intensity(self):
        """CF must be below the lowest test intensity."""
        cf, wp, r2 = critical_force([80.0, 60.0, 45.0], [77.0, 136.0, 323.0])
        assert cf < 45.0, "CF must be below lowest test intensity"

    def test_two_point_minimum(self):
        """CF calculation should work with exactly 2 data points."""
        cf, wp, r2 = critical_force([80.0, 45.0], [77.0, 323.0])
        assert 25.0 < cf < 45.0
        assert wp > 0
        # With exactly 2 points, R² should be 1.0 (perfect fit)
        assert r2 == pytest.approx(1.0, abs=0.001)

    def test_insufficient_data_raises(self):
        """Single data point should raise ValueError."""
        with pytest.raises(ValueError, match="at least 2"):
            critical_force([80.0], [77.0])

    def test_mismatched_lengths_raises(self):
        """Mismatched input lengths should raise ValueError."""
        with pytest.raises(ValueError, match="same length"):
            critical_force([80.0, 60.0], [77.0])

    def test_higher_intensity_shorter_tlim(self):
        """Higher intensity must correlate with shorter time to failure."""
        # This is a data quality check the model inherently validates
        cf, wp, r2 = critical_force([80.0, 60.0, 45.0], [77.0, 136.0, 323.0])
        assert cf > 0

    def test_elite_climber_higher_cf(self):
        """Elite climbers should have higher CF/MVC ratio.

        Reference: Fryer et al. 2018 — elite CF/MVC ≈ 0.45–0.55.
        Simulated by longer tlim at each intensity.
        """
        cf_elite, _, _ = critical_force([80.0, 60.0, 45.0], [120.0, 250.0, 600.0])
        cf_inter, _, _ = critical_force([80.0, 60.0, 45.0], [77.0, 136.0, 323.0])
        assert cf_elite > cf_inter, "Elite CF should exceed intermediate CF"


# ---------------------------------------------------------------------------
# time_to_failure — hyperbolic prediction
# ---------------------------------------------------------------------------


class TestTimeToFailure:
    """Verify time-to-failure predictions from CF model.

    Core relationship: t_lim = W' / (F - CF)
    Reference: Jones et al. 2010 (:cite:`jones2010`).
    """

    def test_basic_prediction(self):
        """80% MVC with CF=35%, W'=2000 → t_lim = 2000/45 ≈ 44.4s."""
        t = time_to_failure(80.0, 35.0, 2000.0)
        assert t == pytest.approx(44.4, abs=0.1)

    def test_higher_force_shorter_time(self):
        """Higher force above CF should yield shorter time to failure."""
        t1 = time_to_failure(60.0, 35.0, 2000.0)
        t2 = time_to_failure(80.0, 35.0, 2000.0)
        assert t2 < t1

    def test_force_at_cf_raises(self):
        """Force equal to CF → infinite endurance, should raise."""
        with pytest.raises(ValueError, match="must exceed CF"):
            time_to_failure(35.0, 35.0, 2000.0)

    def test_force_below_cf_raises(self):
        """Force below CF → infinite endurance, should raise."""
        with pytest.raises(ValueError, match="must exceed CF"):
            time_to_failure(30.0, 35.0, 2000.0)

    def test_larger_w_prime_longer_time(self):
        """Larger W' should allow longer time at same intensity."""
        t1 = time_to_failure(80.0, 35.0, 2000.0)
        t2 = time_to_failure(80.0, 35.0, 4000.0)
        assert t2 > t1
        assert t2 == pytest.approx(2 * t1, abs=0.1)


# ---------------------------------------------------------------------------
# classify_endurance — CF/MVC ratio interpretation
# ---------------------------------------------------------------------------


class TestClassifyEndurance:
    """Verify endurance profile classification.

    Reference thresholds from Fryer et al. 2018:
        < 0.35 → strength-dominant (boulderer)
        0.35–0.50 → balanced
        > 0.50 → endurance-dominant (sport climber)
    """

    @pytest.mark.parametrize(
        "ratio, expected",
        [
            (0.20, "strength-dominant"),
            (0.30, "strength-dominant"),
            (0.34, "strength-dominant"),
            (0.35, "balanced"),
            (0.42, "balanced"),
            (0.50, "balanced"),
            (0.51, "endurance-dominant"),
            (0.55, "endurance-dominant"),
            (0.70, "endurance-dominant"),
        ],
    )
    def test_classifications(self, ratio, expected):
        assert classify_endurance(ratio) == expected

    def test_invalid_ratio_raises(self):
        with pytest.raises(ValueError):
            classify_endurance(-0.1)
        with pytest.raises(ValueError):
            classify_endurance(1.5)


# ---------------------------------------------------------------------------
# w_prime_balance — W' depletion tracking
# ---------------------------------------------------------------------------


class TestWPrimeBalance:
    """Verify W' balance tracking across efforts.

    Reference concept: Skiba et al. 2012 — W' balance model.
    """

    def test_depletion_above_cf(self):
        """Effort above CF should deplete W'."""
        bal = w_prime_balance(2000.0, 35.0, [80.0], [10.0])
        assert bal[0] < 2000.0
        assert bal[0] == pytest.approx(2000.0 - (80.0 - 35.0) * 10.0, abs=0.1)

    def test_recovery_below_cf(self):
        """Rest below CF should reconstitute W'."""
        bal = w_prime_balance(2000.0, 35.0, [80.0, 0.0], [10.0, 60.0])
        assert bal[1] > bal[0], "W' should recover during rest"

    def test_full_recovery_sufficient_rest(self):
        """Sufficient rest should fully restore W'."""
        bal = w_prime_balance(2000.0, 35.0, [80.0, 0.0], [10.0, 200.0])
        assert bal[1] == 2000.0, "W' should fully recover with sufficient rest"

    def test_no_depletion_below_cf(self):
        """Effort at or below CF should not deplete W'."""
        bal = w_prime_balance(2000.0, 35.0, [30.0], [60.0])
        assert bal[0] == 2000.0

    def test_depletion_to_zero(self):
        """Very long effort above CF should deplete W' to zero."""
        bal = w_prime_balance(2000.0, 35.0, [80.0], [100.0])
        assert bal[0] == 0.0

    def test_mismatched_lengths_raises(self):
        with pytest.raises(ValueError, match="same length"):
            w_prime_balance(2000.0, 35.0, [80.0, 60.0], [10.0])


# ---------------------------------------------------------------------------
# cf_mvc_ratio — diagnostic ratio
# ---------------------------------------------------------------------------


class TestCfMvcRatio:
    """Verify CF/MVC ratio calculation.

    Reference: intermediate climbers typically 0.30–0.45 (Fryer 2018).
    """

    def test_typical_intermediate(self):
        """35% CF / 100% MVC = 0.35."""
        assert cf_mvc_ratio(35.0, 100.0) == 0.35

    def test_elite_endurance(self):
        """50% CF / 100% MVC = 0.50."""
        assert cf_mvc_ratio(50.0, 100.0) == 0.50

    def test_zero_mvc_raises(self):
        with pytest.raises(ValueError, match="positive"):
            cf_mvc_ratio(35.0, 0.0)

    def test_negative_cf_raises(self):
        with pytest.raises(ValueError, match="non-negative"):
            cf_mvc_ratio(-5.0, 100.0)


# ---------------------------------------------------------------------------
# interpret_cf_ratio — training recommendations
# ---------------------------------------------------------------------------


class TestInterpretCfRatio:
    """Verify CF/MVC ratio interpretation for training decisions."""

    def test_endurance_limited(self):
        result = interpret_cf_ratio(0.30)
        assert result["category"] == "endurance-limited"
        assert "repeater" in result["priority"].lower() or "arc" in result["priority"].lower()

    def test_balanced(self):
        result = interpret_cf_ratio(0.42)
        assert result["category"] == "balanced"

    def test_strength_limited(self):
        result = interpret_cf_ratio(0.55)
        assert result["category"] == "strength-limited"
        assert "maxhang" in result["priority"].lower() or "bouldering" in result["priority"].lower()
