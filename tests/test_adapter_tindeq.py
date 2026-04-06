"""Tests for climbing_science.adapters.tindeq — Tindeq Progressor adapter."""

import json
from pathlib import Path

import pytest

from climbing_science.adapters.tindeq import (
    TINDEQ_SAMPLE_RATE_HZ,
    TindeqSession,
    extract_mvc7,
    extract_peaks,
    load,
    load_all,
)

# ---------------------------------------------------------------------------
# Helpers — synthetic Tindeq JSON
# ---------------------------------------------------------------------------


def _fft_json(n_samples: int = 800, force_kg: float = 50.0, rate_hz: float = 80.0) -> str:
    """Generate FingerForceTraining-style JSON with 'samples' key."""
    interval_us = int(1_000_000 / rate_hz)
    samples = []
    for i in range(n_samples):
        samples.append({"timestamp": i * interval_us, "value": force_kg})
    return json.dumps(
        {
            "testType": "MVC",
            "holdType": "half_crimp",
            "samples": samples,
        }
    )


def _simple_json(n_samples: int = 800, force_kg: float = 50.0, rate_hz: float = 80.0) -> str:
    """Generate simple format with 'data' key."""
    data = [{"force": force_kg, "time": int(i * 1_000_000 / rate_hz)} for i in range(n_samples)]
    return json.dumps({"sampleRate": rate_hz, "data": data})


def _array_json(n_samples: int = 800, force_kg: float = 50.0) -> str:
    """Generate bare array format."""
    return json.dumps([force_kg] * n_samples)


def _mvc7_session_json(bw_force: float = 40.0, peak_force: float = 80.0) -> str:
    """Session with low baseline and 7s+ peak — for MVC-7 extraction."""
    rate = 80.0
    interval_us = int(1_000_000 / rate)
    samples = []
    # 3s baseline
    for i in range(240):
        samples.append({"timestamp": i * interval_us, "value": bw_force})
    # 8s peak
    for i in range(240, 880):
        samples.append({"timestamp": i * interval_us, "value": peak_force})
    # 2s cooldown
    for i in range(880, 1040):
        samples.append({"timestamp": i * interval_us, "value": bw_force * 0.5})
    return json.dumps({"testType": "MVC", "samples": samples})


# ---------------------------------------------------------------------------
# load()
# ---------------------------------------------------------------------------


class TestLoad:
    def test_fft_format_from_string(self):
        session = load(_fft_json())
        assert isinstance(session, TindeqSession)
        assert len(session.values) == 800
        assert session.values[0] == pytest.approx(50.0)
        assert session.metadata.get("testType") == "MVC"

    def test_simple_format(self):
        session = load(_simple_json())
        assert len(session.values) == 800
        assert session.sample_rate_hz == pytest.approx(80.0)

    def test_array_format(self):
        session = load(_array_json())
        assert len(session.values) == 800
        assert session.sample_rate_hz == TINDEQ_SAMPLE_RATE_HZ

    def test_load_from_file(self, tmp_path):
        path = tmp_path / "test.json"
        path.write_text(_fft_json())
        session = load(path)
        assert session.filename == "test.json"
        assert len(session.values) == 800

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load(Path("/nonexistent/file.json"))

    def test_invalid_json_raises(self):
        with pytest.raises((ValueError, json.JSONDecodeError)):
            load('{"unknown_key": 42}')

    def test_duration(self):
        session = load(_fft_json(n_samples=800))
        assert session.duration_s == pytest.approx(10.0, abs=0.2)

    def test_num_samples(self):
        session = load(_fft_json(n_samples=400))
        assert session.num_samples == 400

    def test_sample_rate_detection_microseconds(self):
        session = load(_fft_json(rate_hz=80.0))
        assert session.sample_rate_hz == pytest.approx(80.0, rel=0.05)

    def test_fft_list_samples(self):
        """Test samples as [timestamp, value] arrays."""
        rate_hz = 80.0
        interval_us = int(1_000_000 / rate_hz)
        samples = [[i * interval_us, 45.0] for i in range(400)]
        raw = json.dumps({"samples": samples})
        session = load(raw)
        assert len(session.values) == 400
        assert session.values[0] == pytest.approx(45.0)


# ---------------------------------------------------------------------------
# load_all()
# ---------------------------------------------------------------------------


class TestLoadAll:
    def test_loads_multiple_files(self, tmp_path):
        for i in range(3):
            (tmp_path / f"session_{i}.json").write_text(_fft_json(force_kg=40.0 + i * 5))
        sessions = load_all(tmp_path)
        assert len(sessions) == 3

    def test_skips_invalid_files(self, tmp_path):
        (tmp_path / "good.json").write_text(_fft_json())
        (tmp_path / "bad.json").write_text("not json at all")
        sessions = load_all(tmp_path)
        assert len(sessions) == 1

    def test_sorted_by_filename(self, tmp_path):
        for name in ["c.json", "a.json", "b.json"]:
            (tmp_path / name).write_text(_fft_json())
        sessions = load_all(tmp_path)
        assert [s.filename for s in sessions] == ["a.json", "b.json", "c.json"]

    def test_not_a_directory(self):
        with pytest.raises(NotADirectoryError):
            load_all("/nonexistent/dir")

    def test_empty_directory(self, tmp_path):
        sessions = load_all(tmp_path)
        assert sessions == []


# ---------------------------------------------------------------------------
# extract_mvc7()
# ---------------------------------------------------------------------------


class TestExtractMVC7:
    def test_constant_session(self):
        session = load(_fft_json(n_samples=800, force_kg=50.0))
        mvc7 = extract_mvc7(session)
        assert mvc7 == pytest.approx(50.0, abs=1.0)

    def test_session_with_peak(self):
        session = load(_mvc7_session_json(bw_force=20.0, peak_force=80.0))
        mvc7 = extract_mvc7(session)
        assert mvc7 == pytest.approx(80.0, abs=2.0)

    def test_no_smoothing(self):
        session = load(_fft_json(n_samples=800, force_kg=50.0))
        mvc7 = extract_mvc7(session, smooth_ms=0)
        assert mvc7 == pytest.approx(50.0, abs=0.1)


# ---------------------------------------------------------------------------
# extract_peaks()
# ---------------------------------------------------------------------------


class TestExtractPeaks:
    def test_session_with_one_peak(self):
        session = load(_mvc7_session_json(bw_force=2.0, peak_force=80.0))
        peaks = extract_peaks(session, min_force_kg=10.0, min_duration_s=1.0)
        assert len(peaks) >= 1
        assert peaks[0].peak_value == pytest.approx(80.0, abs=2.0)

    def test_constant_low_no_peaks(self):
        session = load(_fft_json(force_kg=3.0))
        peaks = extract_peaks(session, min_force_kg=5.0)
        assert len(peaks) == 0
