"""Command-line interface for climbing-science.

Provides subcommands for quick analysis without writing Python code.

Usage::

    $ climbing-science grade "7a+" --to uiaa
    $ climbing-science analyze --mvc7 105 --bw 72
    $ climbing-science protocols --level intermediate

References:
    climbing-science library (:cite:`banaszczyk2020`)
"""

from __future__ import annotations

import argparse
import sys
import textwrap


def _cmd_grade(args: argparse.Namespace) -> None:
    """Convert a climbing grade between systems."""
    from climbing_science import convert, parse
    from climbing_science.grades import BoulderSystem

    # Map short names to system identifiers accepted by convert()
    sys_map = {
        "french": "french",
        "uiaa": "uiaa",
        "yds": "yds",
        "font": "font",
        "v": "v-scale",
        "v-scale": "v-scale",
    }
    systems_route = ["french", "uiaa", "yds"]
    systems_boulder = ["font", "v-scale"]
    grade_str = args.grade
    target = args.to.lower()

    # Detect source system
    parsed = parse(grade_str)
    from_sys = sys_map.get(str(parsed.system.value).lower().replace(" ", "-"), str(parsed.system.value))
    is_boulder = isinstance(parsed.system, BoulderSystem)
    all_targets = systems_boulder if is_boulder else systems_route

    # Short display names
    display_names = {"french": "FRENCH", "uiaa": "UIAA", "yds": "YDS", "font": "FONT", "v-scale": "V-SCALE"}

    if target == "all":
        results = []
        for sys_name in all_targets:
            try:
                converted = convert(grade_str, from_sys, sys_name)
                display = display_names.get(sys_name, sys_name.upper())
                results.append(f"  {display:>8s}: {converted}")
            except Exception:
                pass
        if results:
            print(f"Grade {grade_str} ({display_names.get(from_sys, from_sys.upper())}):")
            print("\n".join(results))
        else:
            print(f"Error: could not convert '{grade_str}'", file=sys.stderr)
            sys.exit(1)
    else:
        target_sys = sys_map.get(target, target)
        try:
            result = convert(grade_str, from_sys, target_sys)
            print(result)
        except Exception as exc:
            print(f"Error: {exc}", file=sys.stderr)
            sys.exit(1)


def _cmd_analyze(args: argparse.Namespace) -> None:
    """Analyze finger strength from MVC-7 data."""
    from climbing_science import (
        mvc7_to_grade,
        power_to_weight,
    )
    from climbing_science.diagnostics import classify_level
    from climbing_science.edge_depth import normalize_to_reference

    mvc7 = args.mvc7
    bw = args.bw
    edge = args.edge

    # Edge correction
    if edge != 20:
        mvc7_corrected = normalize_to_reference(mvc7, edge)
        print(f"Edge correction: {mvc7:.1f} kg @ {edge}mm → {mvc7_corrected:.1f} kg @ 20mm")
        mvc7 = mvc7_corrected

    ratio, _level = power_to_weight(mvc7, bw)
    predicted_route = mvc7_to_grade(ratio, model="COMPOSITE")
    predicted_boulder = mvc7_to_grade(ratio, model="MAXTOGRADE")

    print(f"\n{'═' * 45}")
    print("  🧗 Climbing Strength Analysis")
    print(f"{'═' * 45}")
    print(f"  Body weight:        {bw:.1f} kg")
    print(f"  MVC-7 (20mm):       {mvc7:.1f} kg")
    print(f"  Power-to-weight:    {ratio:.1f}% BW")
    print(f"  Predicted route:    {predicted_route}")
    print(f"  Predicted boulder:  {predicted_boulder}")
    if args.grade:
        level = classify_level(args.grade)
        print(f"  Current grade:      {args.grade} ({level})")
    print(f"{'═' * 45}")


def _cmd_protocols(args: argparse.Namespace) -> None:
    """List and filter hangboard protocols."""
    from climbing_science.protocols import format_notation, list_protocols

    energy_filter = None
    level_filter = None
    if args.energy:
        from climbing_science.models import EnergySystem

        energy_filter = EnergySystem(args.energy)
    if args.level:
        from climbing_science.models import ClimberLevel

        level_filter = ClimberLevel(args.level)

    protos = list_protocols(energy_system=energy_filter, min_level=level_filter)

    if not protos:
        print("No protocols found matching your criteria.")
        return

    print(f"{'ID':<25s} {'Name':<40s} {'Energy':<10s} {'Notation'}")
    print(f"{'─' * 25} {'─' * 40} {'─' * 10} {'─' * 30}")
    for p in protos:
        notation = format_notation(p)
        energy = p.energy_system.value if p.energy_system else "—"
        print(f"{p.id:<25s} {p.name:<40s} {energy:<10s} {notation}")


def _cmd_endurance(args: argparse.Namespace) -> None:
    """Compute Critical Force from 3-point test data."""
    from climbing_science import power_to_weight
    from climbing_science.endurance import (
        cf_mvc_ratio,
        critical_force,
        interpret_cf_ratio,
    )

    intensities = args.intensities
    durations = args.durations

    if len(intensities) != len(durations):
        print("Error: --intensities and --durations must have the same length", file=sys.stderr)
        sys.exit(1)

    cf_pct, w_prime, r_squared = critical_force(intensities, durations)
    print(f"\n{'═' * 45}")
    print("  🫁 Critical Force Analysis")
    print(f"{'═' * 45}")
    print(f"  CF:       {cf_pct:.1f}% MVC")
    print(f"  W':       {w_prime:.1f}% MVC·s")
    print(f"  R²:       {r_squared:.4f}")

    if args.mvc7 and args.bw:
        ratio, _ = power_to_weight(args.mvc7, args.bw)
        cf_ratio = cf_mvc_ratio(cf_pct, ratio)
        interp = interpret_cf_ratio(cf_ratio)
        print(f"  CF/BW:    {cf_ratio:.2f}")
        print(f"  Category: {interp['category']}")
        print(f"  Note:     {interp['interpretation']}")
        print(f"  Priority: {interp['priority']}")
    print(f"{'═' * 45}")


def main(argv: list[str] | None = None) -> None:
    """Entry point for the climbing-science CLI.

    References:
        climbing-science library (:cite:`banaszczyk2020`)
    """
    parser = argparse.ArgumentParser(
        prog="climbing-science",
        description="Evidence-based climbing training analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              climbing-science grade "7a+" --to uiaa
              climbing-science grade "5.12a" --to all
              climbing-science analyze --mvc7 105 --bw 72
              climbing-science analyze --mvc7 45 --bw 72 --edge 15
              climbing-science protocols --level intermediate
              climbing-science endurance --intensities 80 60 45 --durations 77 136 323
        """),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {_get_version()}")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # grade
    p_grade = subparsers.add_parser("grade", help="Convert climbing grades between systems")
    p_grade.add_argument("grade", help="Grade string (e.g. '7a+', '5.12a', 'V5', '6+')")
    p_grade.add_argument("--to", default="all", help="Target system: french, uiaa, yds, font, v, all (default: all)")
    p_grade.set_defaults(func=_cmd_grade)

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Analyze finger strength from MVC-7")
    p_analyze.add_argument("--mvc7", type=float, required=True, help="MVC-7 in kg (total load: BW + added weight)")
    p_analyze.add_argument("--bw", type=float, required=True, help="Body weight in kg")
    p_analyze.add_argument("--edge", type=float, default=20, help="Test edge depth in mm (default: 20)")
    p_analyze.add_argument("--grade", help="Current redpoint grade for level classification")
    p_analyze.set_defaults(func=_cmd_analyze)

    # protocols
    p_proto = subparsers.add_parser("protocols", help="List hangboard training protocols")
    p_proto.add_argument("--level", help="Filter by level: beginner, intermediate, advanced, elite")
    p_proto.add_argument("--energy", help="Filter by energy system: alactic, lactate, aerobic")
    p_proto.set_defaults(func=_cmd_protocols)

    # endurance
    p_endurance = subparsers.add_parser("endurance", help="Compute Critical Force from 3-point test")
    p_endurance.add_argument(
        "--intensities", type=float, nargs="+", required=True, help="Test intensities in %%MVC (e.g. 80 60 45)"
    )
    p_endurance.add_argument(
        "--durations", type=float, nargs="+", required=True, help="Cumulative hang times in seconds (e.g. 77 136 323)"
    )
    p_endurance.add_argument("--mvc7", type=float, help="MVC-7 in kg (for CF/BW ratio)")
    p_endurance.add_argument("--bw", type=float, help="Body weight in kg (for CF/BW ratio)")
    p_endurance.set_defaults(func=_cmd_endurance)

    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


def _get_version() -> str:
    """Return the package version string."""
    try:
        from climbing_science import __version__

        return __version__
    except ImportError:
        return "unknown"


if __name__ == "__main__":
    main()
