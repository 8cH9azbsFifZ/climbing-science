"""Tests for climbing_science.protocols — protocol registry.

Tests verify:
- Registry completeness (≥20 protocols)
- Protocol lookup and filtering
- Selection by weakness and level
- Standard notation formatting
"""

import pytest

from climbing_science.models import ClimberLevel, EnergySystem
from climbing_science.protocols import (
    REGISTRY,
    format_notation,
    get_protocol,
    list_protocols,
    select_protocols,
)


class TestRegistry:
    """Verify protocol registry completeness and data integrity."""

    def test_minimum_20_protocols(self):
        """FR-06.1: at least 20 protocols required."""
        assert len(REGISTRY) >= 21

    def test_all_have_required_fields(self):
        for pid, proto in REGISTRY.items():
            assert proto.id == pid
            assert proto.name, f"{pid}: missing name"
            assert proto.author, f"{pid}: missing author"
            assert proto.params.hang_duration_sec > 0, f"{pid}: invalid hang duration"
            assert proto.params.sets >= 1, f"{pid}: invalid sets"

    def test_lopez_maxhang_exists(self):
        assert "lopez-maxhang-maw" in REGISTRY

    def test_ttf_endurance_3pt_exists(self):
        p = get_protocol("ttf-endurance-3pt")
        assert p.name == "3-Point Time-to-Failure Test"
        assert p.author == "Jones / Fryer"
        assert p.energy_system == EnergySystem.AEROBIC
        assert p.params.sets == 3
        assert p.reference_key == "jones2010"

    def test_energy_system_coverage(self):
        """All three energy systems should be represented."""
        systems = {p.energy_system for p in REGISTRY.values()}
        assert EnergySystem.ALACTIC in systems
        assert EnergySystem.LACTIC in systems
        assert EnergySystem.AEROBIC in systems


class TestGetProtocol:
    """Verify protocol lookup."""

    def test_known_protocol(self):
        p = get_protocol("lopez-maxhang-maw")
        assert p.name == "MaxHangs Medium Added Weight"
        assert p.author == "Eva López"

    def test_unknown_raises(self):
        with pytest.raises(KeyError, match="Unknown protocol"):
            get_protocol("nonexistent-protocol")


class TestListProtocols:
    """Verify protocol filtering."""

    def test_filter_by_energy_system(self):
        alactic = list_protocols(energy_system=EnergySystem.ALACTIC)
        assert len(alactic) >= 5
        assert all(p.energy_system == EnergySystem.ALACTIC for p in alactic)

    def test_filter_by_level(self):
        beginner = list_protocols(min_level=ClimberLevel.BEGINNER)
        assert len(beginner) >= 3

    def test_no_filter_returns_all(self):
        all_protos = list_protocols()
        assert len(all_protos) == len(REGISTRY)


class TestSelectProtocols:
    """Verify weakness-based protocol selection."""

    def test_strength_weakness(self):
        protos = select_protocols("strength", ClimberLevel.INTERMEDIATE)
        assert len(protos) >= 1
        assert all(p.energy_system == EnergySystem.ALACTIC for p in protos)

    def test_endurance_weakness(self):
        protos = select_protocols("endurance", ClimberLevel.INTERMEDIATE)
        assert len(protos) >= 1
        assert all(p.energy_system == EnergySystem.AEROBIC for p in protos)

    def test_unknown_weakness_raises(self):
        with pytest.raises(ValueError, match="Unknown weakness"):
            select_protocols("flexibility")


class TestFormatNotation:
    """Verify standard hangboard notation formatting."""

    def test_lopez_maxhang(self):
        p = get_protocol("lopez-maxhang-maw")
        notation = format_notation(p, 15.0)
        assert "@18mm" in notation
        assert "HC" in notation
        assert "W+15.0kg" in notation
        assert "10s" in notation
