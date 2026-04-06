"""Tests for the CLI runner (frontends/cli.py)."""

from climbing_science.frontends.cli import main


def test_version(capsys):
    """CLI --version prints the package version."""
    from climbing_science import __version__

    try:
        main(["--version"])
    except SystemExit:
        pass
    captured = capsys.readouterr()
    assert __version__ in captured.out or __version__ in captured.err


def test_grade_single(capsys):
    """Convert a single grade to another system."""
    main(["grade", "7a+", "--to", "uiaa"])
    assert "VIII+" in capsys.readouterr().out


def test_grade_all(capsys):
    """Convert a grade to all systems."""
    main(["grade", "7a+", "--to", "all"])
    out = capsys.readouterr().out
    assert "FRENCH" in out
    assert "UIAA" in out
    assert "YDS" in out


def test_grade_boulder(capsys):
    """Convert a boulder grade."""
    main(["grade", "V5", "--to", "all"])
    out = capsys.readouterr().out
    assert "FONT" in out


def test_analyze(capsys):
    """Analyze MVC-7 strength."""
    main(["analyze", "--mvc7", "105", "--bw", "72"])
    out = capsys.readouterr().out
    assert "145.8% BW" in out
    assert "Predicted route" in out


def test_analyze_with_grade(capsys):
    """Analyze with current grade classification."""
    main(["analyze", "--mvc7", "105", "--bw", "72", "--grade", "7a"])
    out = capsys.readouterr().out
    assert "advanced" in out


def test_analyze_edge_correction(capsys):
    """Edge correction applied for non-20mm edge."""
    main(["analyze", "--mvc7", "45", "--bw", "72", "--edge", "15"])
    out = capsys.readouterr().out
    assert "Edge correction" in out
    assert "20mm" in out


def test_protocols(capsys):
    """List all protocols."""
    main(["protocols"])
    out = capsys.readouterr().out
    assert "lopez" in out.lower()
    assert "Energy" in out or "alactic" in out


def test_protocols_filter_energy(capsys):
    """Filter protocols by energy system."""
    main(["protocols", "--energy", "alactic"])
    out = capsys.readouterr().out
    assert "alactic" in out
    assert "aerobic" not in out.lower().split("energy")[0]  # No aerobic in the results


def test_endurance(capsys):
    """Compute Critical Force."""
    main(["endurance", "--intensities", "80", "60", "45", "--durations", "77", "136", "323"])
    out = capsys.readouterr().out
    assert "CF:" in out
    assert "W':" in out
    assert "R²:" in out


def test_endurance_with_ratio(capsys):
    """Compute CF with MVC/BW ratio."""
    main(
        [
            "endurance",
            "--intensities",
            "80",
            "60",
            "45",
            "--durations",
            "77",
            "136",
            "323",
            "--mvc7",
            "105",
            "--bw",
            "72",
        ]
    )
    out = capsys.readouterr().out
    assert "CF/BW" in out
    assert "Category" in out


def test_no_command(capsys):
    """No subcommand prints help and exits cleanly."""
    try:
        main([])
    except SystemExit as exc:
        assert exc.code == 0
