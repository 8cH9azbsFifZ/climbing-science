"""Protocol library — hangboard training protocol registry.

Defines a registry of well-known hangboard training protocols with
full parameters, energy system classification, and progression rules.

Data sources:
    - López-Rivera & González-Badillo 2012 (:cite:`lopezrivera2012`)
    - López-Rivera 2014 (:cite:`lopez2014`)
    - Hörst 2016 (:cite:`horst2016`)
    - Anderson & Anderson 2014 (:cite:`anderson2014`)
    - Medernach et al. 2015 (:cite:`medernach2015`)
"""

from __future__ import annotations

from climbing_science.models import (
    ClimberLevel,
    EnergySystem,
    GripType,
    ProgressionRule,
    ProtocolDefinition,
    ProtocolParams,
)

__all__ = [
    "REGISTRY",
    "get_protocol",
    "list_protocols",
    "select_protocols",
    "format_notation",
]


# ---------------------------------------------------------------------------
# Protocol Registry
# ---------------------------------------------------------------------------

REGISTRY: dict[str, ProtocolDefinition] = {
    "lopez-maxhang-maw": ProtocolDefinition(
        id="lopez-maxhang-maw",
        name="MaxHangs Medium Added Weight",
        author="Eva López",
        energy_system=EnergySystem.ALACTIC,
        min_level=ClimberLevel.INTERMEDIATE,
        params=ProtocolParams(
            edge_size_mm=18,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=10.0,
            rest_between_reps_sec=0.0,
            reps_per_set=1,
            rest_between_sets_sec=180.0,
            sets=4,
            intensity_percent_mvc=(88.0, 103.0),
        ),
        progression=ProgressionRule(
            duration_weeks=4,
            volume_per_week=[2, 3, 4, 4],
        ),
        reference_key="lopezrivera2012",
    ),
    "lopez-maxhang-haw": ProtocolDefinition(
        id="lopez-maxhang-haw",
        name="MaxHangs High Added Weight",
        author="Eva López",
        energy_system=EnergySystem.ALACTIC,
        min_level=ClimberLevel.ADVANCED,
        params=ProtocolParams(
            edge_size_mm=18,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=5.0,
            rest_between_reps_sec=0.0,
            reps_per_set=1,
            rest_between_sets_sec=180.0,
            sets=5,
            intensity_percent_mvc=(95.0, 106.0),
        ),
        progression=ProgressionRule(
            duration_weeks=4,
            volume_per_week=[2, 3, 4, 4],
        ),
        reference_key="lopezrivera2012",
    ),
    "lopez-inthangs": ProtocolDefinition(
        id="lopez-inthangs",
        name="Intermittent Dead Hangs",
        author="Eva López",
        energy_system=EnergySystem.LACTIC,
        min_level=ClimberLevel.INTERMEDIATE,
        params=ProtocolParams(
            edge_size_mm=18,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=10.0,
            rest_between_reps_sec=5.0,
            reps_per_set=4,
            rest_between_sets_sec=60.0,
            sets=4,
            intensity_percent_mvc=(60.0, 80.0),
        ),
        progression=ProgressionRule(
            duration_weeks=4,
            volume_per_week=[2, 3, 4, 4],
        ),
        reference_key="lopez2014",
    ),
    "lopez-subhangs": ProtocolDefinition(
        id="lopez-subhangs",
        name="Submaximal Dead Hangs",
        author="Eva López",
        energy_system=EnergySystem.LACTIC,
        min_level=ClimberLevel.BEGINNER,
        params=ProtocolParams(
            edge_size_mm=20,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=30.0,
            rest_between_reps_sec=0.0,
            reps_per_set=1,
            rest_between_sets_sec=120.0,
            sets=3,
            intensity_percent_mvc=(55.0, 85.0),
        ),
        progression=ProgressionRule(
            duration_weeks=4,
            volume_per_week=[2, 3, 3, 4],
        ),
        reference_key="lopez2014",
    ),
    "horst-7-53": ProtocolDefinition(
        id="horst-7-53",
        name="7-53 Repeaters",
        author="Eric Hörst",
        energy_system=EnergySystem.ALACTIC,
        min_level=ClimberLevel.INTERMEDIATE,
        params=ProtocolParams(
            edge_size_mm=20,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=7.0,
            rest_between_reps_sec=53.0,
            reps_per_set=3,
            rest_between_sets_sec=180.0,
            sets=3,
            intensity_percent_mvc=(92.0, 97.0),
        ),
        progression=ProgressionRule(
            duration_weeks=4,
            volume_per_week=[2, 3, 3, 2],
        ),
        reference_key="horst2016",
    ),
    "bechtel-ladders": ProtocolDefinition(
        id="bechtel-ladders",
        name="3-6-9 Ladders",
        author="Steve Bechtel",
        energy_system=EnergySystem.ALACTIC,
        min_level=ClimberLevel.INTERMEDIATE,
        params=ProtocolParams(
            edge_size_mm=20,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=12.0,
            rest_between_reps_sec=0.0,
            reps_per_set=1,
            rest_between_sets_sec=180.0,
            sets=3,
            intensity_percent_mvc=(88.0, 95.0),
        ),
        reference_key="",
    ),
    "repeaters-7-3": ProtocolDefinition(
        id="repeaters-7-3",
        name="7/3 Repeaters",
        author="Industry Standard",
        energy_system=EnergySystem.LACTIC,
        min_level=ClimberLevel.BEGINNER,
        params=ProtocolParams(
            edge_size_mm=20,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=7.0,
            rest_between_reps_sec=3.0,
            reps_per_set=6,
            rest_between_sets_sec=180.0,
            sets=6,
            intensity_percent_mvc=(40.0, 80.0),
        ),
        reference_key="",
    ),
    "endurance-repeaters": ProtocolDefinition(
        id="endurance-repeaters",
        name="Endurance Repeaters",
        author="Industry Standard",
        energy_system=EnergySystem.AEROBIC,
        min_level=ClimberLevel.BEGINNER,
        params=ProtocolParams(
            edge_size_mm=20,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=7.0,
            rest_between_reps_sec=3.0,
            reps_per_set=12,
            rest_between_sets_sec=0.0,
            sets=1,
            intensity_percent_mvc=(25.0, 60.0),
        ),
        reference_key="",
    ),
    "density-hangs": ProtocolDefinition(
        id="density-hangs",
        name="Density Hangs",
        author="Tyler Nelson",
        energy_system=EnergySystem.LACTIC,
        min_level=ClimberLevel.INTERMEDIATE,
        params=ProtocolParams(
            edge_size_mm=20,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=20.0,
            rest_between_reps_sec=10.0,
            reps_per_set=1,
            rest_between_sets_sec=120.0,
            sets=5,
            intensity_percent_mvc=(50.0, 80.0),
        ),
        reference_key="",
    ),
    "one-arm-hangs": ProtocolDefinition(
        id="one-arm-hangs",
        name="One-Arm Dead Hangs",
        author="Webb-Parsons",
        energy_system=EnergySystem.ALACTIC,
        min_level=ClimberLevel.ELITE,
        params=ProtocolParams(
            edge_size_mm=20,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=7.0,
            rest_between_reps_sec=0.0,
            reps_per_set=1,
            rest_between_sets_sec=180.0,
            sets=3,
            intensity_percent_mvc=(94.0, 106.0),
        ),
        reference_key="",
    ),
    "anderson-repeaters": ProtocolDefinition(
        id="anderson-repeaters",
        name="Anderson Repeaters",
        author="Mark & Mike Anderson",
        energy_system=EnergySystem.LACTIC,
        min_level=ClimberLevel.INTERMEDIATE,
        params=ProtocolParams(
            edge_size_mm=20,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=7.0,
            rest_between_reps_sec=3.0,
            reps_per_set=6,
            rest_between_sets_sec=180.0,
            sets=4,
            intensity_percent_mvc=(50.0, 75.0),
        ),
        progression=ProgressionRule(
            duration_weeks=4,
            volume_per_week=[3, 4, 4, 2],
        ),
        reference_key="anderson2014",
    ),
    "lattice-maxhangs": ProtocolDefinition(
        id="lattice-maxhangs",
        name="Lattice MaxHangs",
        author="Lattice Training",
        energy_system=EnergySystem.ALACTIC,
        min_level=ClimberLevel.INTERMEDIATE,
        params=ProtocolParams(
            edge_size_mm=20,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=7.0,
            rest_between_reps_sec=0.0,
            reps_per_set=1,
            rest_between_sets_sec=180.0,
            sets=4,
            intensity_percent_mvc=(90.0, 100.0),
        ),
        reference_key="",
    ),
    "lattice-cf-training": ProtocolDefinition(
        id="lattice-cf-training",
        name="Lattice CF Training",
        author="Lattice Training",
        energy_system=EnergySystem.AEROBIC,
        min_level=ClimberLevel.INTERMEDIATE,
        params=ProtocolParams(
            edge_size_mm=20,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=7.0,
            rest_between_reps_sec=3.0,
            reps_per_set=8,
            rest_between_sets_sec=120.0,
            sets=3,
            intensity_percent_mvc=(35.0, 50.0),
        ),
        reference_key="",
    ),
    "medernach-bw-repeaters": ProtocolDefinition(
        id="medernach-bw-repeaters",
        name="Bodyweight Repeaters",
        author="Medernach et al.",
        energy_system=EnergySystem.LACTIC,
        min_level=ClimberLevel.BEGINNER,
        params=ProtocolParams(
            edge_size_mm=23,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=10.0,
            rest_between_reps_sec=5.0,
            reps_per_set=5,
            rest_between_sets_sec=120.0,
            sets=5,
            intensity_percent_mvc=(40.0, 70.0),
        ),
        progression=ProgressionRule(
            duration_weeks=4,
            volume_per_week=[3, 4, 4, 2],
        ),
        reference_key="medernach2015",
    ),
    "lopez-maxhang-mse": ProtocolDefinition(
        id="lopez-maxhang-mse",
        name="MaxHangs Minimum Stimulus Edge",
        author="Eva López",
        energy_system=EnergySystem.ALACTIC,
        min_level=ClimberLevel.ADVANCED,
        params=ProtocolParams(
            edge_size_mm=12,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=13.0,
            rest_between_reps_sec=0.0,
            reps_per_set=1,
            rest_between_sets_sec=180.0,
            sets=4,
            intensity_percent_mvc=(85.0, 95.0),
        ),
        progression=ProgressionRule(
            duration_weeks=4,
            volume_per_week=[2, 3, 4, 4],
        ),
        reference_key="lopez2014",
    ),
    "horst-min-edge": ProtocolDefinition(
        id="horst-min-edge",
        name="Minimum Edge MaxHangs",
        author="Eric Hörst",
        energy_system=EnergySystem.ALACTIC,
        min_level=ClimberLevel.ADVANCED,
        params=ProtocolParams(
            edge_size_mm=10,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=10.0,
            rest_between_reps_sec=0.0,
            reps_per_set=1,
            rest_between_sets_sec=180.0,
            sets=5,
            intensity_percent_mvc=(85.0, 95.0),
        ),
        reference_key="horst2016",
    ),
    "open-hand-repeaters": ProtocolDefinition(
        id="open-hand-repeaters",
        name="Open-Hand Repeaters",
        author="Industry Standard",
        energy_system=EnergySystem.LACTIC,
        min_level=ClimberLevel.INTERMEDIATE,
        params=ProtocolParams(
            edge_size_mm=25,
            grip_type=GripType.OPEN_HAND,
            hang_duration_sec=7.0,
            rest_between_reps_sec=3.0,
            reps_per_set=6,
            rest_between_sets_sec=180.0,
            sets=4,
            intensity_percent_mvc=(40.0, 75.0),
        ),
        reference_key="",
    ),
    "three-finger-drag-hangs": ProtocolDefinition(
        id="three-finger-drag-hangs",
        name="Three-Finger Drag Hangs",
        author="Industry Standard",
        energy_system=EnergySystem.ALACTIC,
        min_level=ClimberLevel.ADVANCED,
        params=ProtocolParams(
            edge_size_mm=20,
            grip_type=GripType.THREE_FINGER_DRAG,
            hang_duration_sec=10.0,
            rest_between_reps_sec=0.0,
            reps_per_set=1,
            rest_between_sets_sec=180.0,
            sets=3,
            intensity_percent_mvc=(80.0, 95.0),
        ),
        reference_key="",
    ),
    "full-crimp-maxhangs": ProtocolDefinition(
        id="full-crimp-maxhangs",
        name="Full Crimp MaxHangs",
        author="Industry Standard",
        energy_system=EnergySystem.ALACTIC,
        min_level=ClimberLevel.ADVANCED,
        params=ProtocolParams(
            edge_size_mm=20,
            grip_type=GripType.FULL_CRIMP,
            hang_duration_sec=7.0,
            rest_between_reps_sec=0.0,
            reps_per_set=1,
            rest_between_sets_sec=180.0,
            sets=3,
            intensity_percent_mvc=(85.0, 95.0),
        ),
        reference_key="",
    ),
    "lopez-strength-endurance": ProtocolDefinition(
        id="lopez-strength-endurance",
        name="Strength-Endurance Cycle",
        author="Eva López",
        energy_system=EnergySystem.LACTIC,
        min_level=ClimberLevel.INTERMEDIATE,
        params=ProtocolParams(
            edge_size_mm=18,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=15.0,
            rest_between_reps_sec=5.0,
            reps_per_set=3,
            rest_between_sets_sec=90.0,
            sets=4,
            intensity_percent_mvc=(60.0, 80.0),
        ),
        progression=ProgressionRule(
            duration_weeks=4,
            volume_per_week=[2, 3, 4, 4],
        ),
        reference_key="lopez2014",
    ),
    "ttf-endurance-3pt": ProtocolDefinition(
        id="ttf-endurance-3pt",
        name="3-Point Time-to-Failure Test",
        author="Jones / Fryer",
        energy_system=EnergySystem.AEROBIC,
        min_level=ClimberLevel.INTERMEDIATE,
        params=ProtocolParams(
            edge_size_mm=20,
            grip_type=GripType.HALF_CRIMP,
            hang_duration_sec=999.0,
            rest_between_reps_sec=300.0,
            reps_per_set=1,
            rest_between_sets_sec=600.0,
            sets=3,
            intensity_percent_mvc=(45.0, 80.0),
        ),
        reference_key="jones2010",
    ),
}


def get_protocol(protocol_id: str) -> ProtocolDefinition:
    """Look up a protocol by its unique identifier.

    Args:
        protocol_id: Protocol ID (e.g. "lopez-maxhang-maw").

    Returns:
        The protocol definition.

    Raises:
        KeyError: If protocol not found.

    References:
        Protocol sources documented per-protocol in ``docs/references.bib``.

    Examples:
        >>> p = get_protocol("lopez-maxhang-maw")
        >>> p.name
        'MaxHangs Medium Added Weight'
    """
    if protocol_id not in REGISTRY:
        raise KeyError(f"Unknown protocol '{protocol_id}'. Available: {', '.join(sorted(REGISTRY.keys()))}")
    return REGISTRY[protocol_id]


def list_protocols(
    energy_system: EnergySystem | None = None,
    min_level: ClimberLevel | None = None,
) -> list[ProtocolDefinition]:
    """List protocols, optionally filtered by energy system or level.

    Args:
        energy_system: Filter by targeted energy system (optional).
        min_level: Filter by minimum athlete level (optional).

    Returns:
        List of matching protocol definitions.

    References:
        Protocol sources documented per-protocol in ``docs/references.bib``.

    Examples:
        >>> len(list_protocols(energy_system=EnergySystem.ALACTIC)) >= 5
        True
    """
    level_order = {
        ClimberLevel.BEGINNER: 0,
        ClimberLevel.INTERMEDIATE: 1,
        ClimberLevel.ADVANCED: 2,
        ClimberLevel.ELITE: 3,
    }

    result = []
    for proto in REGISTRY.values():
        if energy_system is not None and proto.energy_system != energy_system:
            continue
        if min_level is not None and level_order.get(proto.min_level, 0) > level_order.get(min_level, 0):
            continue
        result.append(proto)
    return result


def select_protocols(
    weakness: str,
    level: ClimberLevel = ClimberLevel.INTERMEDIATE,
) -> list[ProtocolDefinition]:
    """Recommend protocols based on weakness and athlete level.

    Decision logic:
        - "strength" → alactic protocols
        - "endurance" → aerobic/lactic protocols
        - "power-endurance" → lactic protocols
        - "strength-endurance" → lactic protocols with moderate intensity

    Args:
        weakness: Primary weakness: "strength", "endurance",
            "power-endurance", or "strength-endurance".
        level: Athlete level for filtering.

    Returns:
        List of recommended protocol definitions.

    References:
        Coaching decision logic based on López 2014 (:cite:`lopez2014`),
        Hörst 2016 (:cite:`horst2016`).

    Examples:
        >>> protos = select_protocols("strength", ClimberLevel.INTERMEDIATE)
        >>> all(p.energy_system == EnergySystem.ALACTIC for p in protos)
        True
    """
    weakness_to_system = {
        "strength": EnergySystem.ALACTIC,
        "endurance": EnergySystem.AEROBIC,
        "power-endurance": EnergySystem.LACTIC,
        "strength-endurance": EnergySystem.LACTIC,
    }

    if weakness not in weakness_to_system:
        raise ValueError(f"Unknown weakness '{weakness}'. Choose from: {', '.join(sorted(weakness_to_system.keys()))}")

    target_system = weakness_to_system[weakness]
    return list_protocols(energy_system=target_system, min_level=level)


def format_notation(protocol: ProtocolDefinition, added_weight_kg: float = 0.0) -> str:
    """Format a protocol in standard hangboard notation.

    Produces notation like: ``4× MaxHang @18mm HC W+10.0kg 10s(0):180s``

    Args:
        protocol: Protocol definition.
        added_weight_kg: Added weight in kg (for display).

    Returns:
        Formatted notation string.

    References:
        Notation follows conventions from López 2014 (:cite:`lopez2014`)
        and Hörst 2016 (:cite:`horst2016`).

    Examples:
        >>> p = get_protocol("lopez-maxhang-maw")
        >>> format_notation(p, 15.0)
        '4× MaxHang @18mm HC W+15.0kg 10s(0):180s'
    """
    p = protocol.params
    grip_short = {
        GripType.HALF_CRIMP: "HC",
        GripType.FULL_CRIMP: "FC",
        GripType.OPEN_HAND: "OH",
        GripType.THREE_FINGER_DRAG: "3FD",
    }
    grip = grip_short.get(p.grip_type, str(p.grip_type.value))

    weight_str = f"W+{added_weight_kg:.1f}kg" if added_weight_kg >= 0 else f"W{added_weight_kg:.1f}kg"

    if p.hang_duration_sec == int(p.hang_duration_sec):
        hang = f"{p.hang_duration_sec:.0f}s"
    else:
        hang = f"{p.hang_duration_sec}s"
    rest_rep = f"({p.reps_per_set})" if p.reps_per_set > 1 else "(0)"

    return f"{p.sets}× MaxHang @{p.edge_size_mm}mm {grip} {weight_str} {hang}{rest_rep}:{p.rest_between_sets_sec:.0f}s"
