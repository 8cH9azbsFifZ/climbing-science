"""Edge depth correction — normalise force measurements across edge sizes.

Grip strength on a hangboard depends on the edge depth. Narrower edges
produce lower maximal forces. This module provides a linear correction
model so that measurements taken on different edges can be compared.

The correction follows Amca et al. (2012) who showed that grip force
decreases approximately linearly with decreasing edge depth. The widely
used 2.5 %/mm model is applied relative to a 20 mm reference edge.

References:
    Amca A. M. et al. (2012) :cite:`amca2012`
    — *Effect of hold depth and grip technique on maximal finger forces
    in rock climbing.* Journal of Sports Sciences, 30(7), 669–677.
"""

from __future__ import annotations

__all__ = [
    "CORRECTION_RATE",
    "MAX_EDGE_MM",
    "MIN_EDGE_MM",
    "REFERENCE_EDGE_MM",
    "convert_force",
    "correction_factor",
    "estimate_force_at_depth",
    "normalize_to_reference",
]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

REFERENCE_EDGE_MM: float = 20.0
"""Standard reference edge depth in millimetres (ISO / IRCRA)."""

CORRECTION_RATE: float = 0.025
"""Force change per millimetre deviation from reference (2.5 %/mm).

Based on Amca et al. (2012) :cite:`amca2012`.
"""

MIN_EDGE_MM: float = 4.0
"""Physical lower bound — below this the linear model is unreliable."""

MAX_EDGE_MM: float = 45.0
"""Upper bound — jug-size edges where correction adds little value."""


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------


def _validate_edge(edge_mm: float, name: str = "edge_mm") -> None:
    if edge_mm <= 0:
        raise ValueError(f"{name} must be > 0, got {edge_mm}")


def _validate_force(force_kg: float) -> None:
    if force_kg < 0:
        raise ValueError(f"force must be >= 0, got {force_kg}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def correction_factor(edge_mm: float, reference_mm: float = REFERENCE_EDGE_MM) -> float:
    """Multiplicative correction factor for edge depth.

    .. math::

        f = 1 + r \\times (d_{ref} - d_{test})

    where *r* = 0.025 (2.5 %/mm).

    Args:
        edge_mm: Test edge depth in millimetres.
        reference_mm: Reference edge depth (default 20 mm).

    Returns:
        Factor to multiply measured force by to obtain the equivalent
        force on the reference edge.

    Raises:
        ValueError: If *edge_mm* or *reference_mm* ≤ 0.

    Examples:
        >>> correction_factor(15.0)
        1.125
        >>> correction_factor(20.0)
        1.0
        >>> correction_factor(25.0)
        0.875

    References:
        Amca et al. (2012) :cite:`amca2012`
    """
    _validate_edge(edge_mm, "edge_mm")
    _validate_edge(reference_mm, "reference_mm")
    return 1.0 + CORRECTION_RATE * (reference_mm - edge_mm)


def convert_force(
    force_kg: float,
    from_edge_mm: float,
    to_edge_mm: float,
) -> float:
    """Convert a force measurement between two edge depths.

    Args:
        force_kg: Measured force in kg.
        from_edge_mm: Edge depth of the original measurement.
        to_edge_mm: Target edge depth.

    Returns:
        Equivalent force at *to_edge_mm* in kg.

    Raises:
        ValueError: If any edge ≤ 0 or force < 0.

    Examples:
        >>> round(convert_force(50.0, 15.0, 20.0), 2)
        56.25

    References:
        Amca et al. (2012) :cite:`amca2012`
    """
    _validate_force(force_kg)
    # Normalise to reference first, then convert to target.
    factor_from = correction_factor(from_edge_mm)
    factor_to = correction_factor(to_edge_mm)
    return force_kg * factor_from / factor_to


def normalize_to_reference(
    force_kg: float,
    edge_mm: float,
    reference_mm: float = REFERENCE_EDGE_MM,
) -> float:
    """Normalise a force measurement to the reference edge depth.

    Convenience wrapper: ``force_kg * correction_factor(edge_mm, reference_mm)``.

    Args:
        force_kg: Measured force in kg.
        edge_mm: Edge depth of the measurement.
        reference_mm: Reference edge depth (default 20 mm).

    Returns:
        Equivalent force at the reference edge.

    References:
        Amca et al. (2012) :cite:`amca2012`
    """
    _validate_force(force_kg)
    return force_kg * correction_factor(edge_mm, reference_mm)


def estimate_force_at_depth(
    force_at_reference_kg: float,
    target_edge_mm: float,
    reference_mm: float = REFERENCE_EDGE_MM,
) -> float:
    """Estimate expected force at a given edge depth.

    Inverse of :func:`normalize_to_reference`.

    Args:
        force_at_reference_kg: Force measured (or normalised to) the
            reference edge.
        target_edge_mm: Edge depth to estimate force for.
        reference_mm: Reference edge depth (default 20 mm).

    Returns:
        Estimated force at *target_edge_mm* in kg.

    References:
        Amca et al. (2012) :cite:`amca2012`
    """
    _validate_force(force_at_reference_kg)
    factor = correction_factor(target_edge_mm, reference_mm)
    return force_at_reference_kg / factor
