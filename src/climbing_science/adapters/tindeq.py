"""Tindeq Progressor adapter — parse FingerForceTraining JSON exports.

The Tindeq Progressor force gauge pairs with the *FingerForceTraining*
iOS / Android app which exports session data as JSON files.  This
adapter reads those files and produces canonical data structures usable
by the climbing-science analysis pipeline.

Supported formats:
    - Current JSON format (UInt64 microsecond timestamps)
    - Legacy format (UInt32 millisecond timestamps)

References:
    Tindeq Progressor hardware specification:
    https://tindeq.com — sampling rate 80 Hz, resolution 0.1 kg.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from climbing_science.signal import (
    Peak,
    best_n_second_average,
    detect_peaks,
    smooth,
)

__all__ = [
    "TindeqSession",
    "load",
    "load_all",
    "extract_mvc7",
    "extract_peaks",
]

TINDEQ_SAMPLE_RATE_HZ: float = 80.0
"""Default sampling rate for Tindeq Progressor (80 Hz)."""


@dataclass(frozen=True)
class TindeqSession:
    """Parsed Tindeq session data.

    Attributes:
        filename: Source file name.
        sample_rate_hz: Sampling rate in Hz.
        values: Force values in kg.
        timestamps_us: Timestamps in microseconds (may be empty if
            reconstructed from sample rate).
        metadata: Raw metadata from the JSON file.
    """

    filename: str
    sample_rate_hz: float
    values: list[float]
    timestamps_us: list[int] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def duration_s(self) -> float:
        """Total recording duration in seconds."""
        if self.timestamps_us and len(self.timestamps_us) >= 2:
            return (self.timestamps_us[-1] - self.timestamps_us[0]) / 1_000_000
        return len(self.values) / self.sample_rate_hz if self.sample_rate_hz > 0 else 0.0

    @property
    def num_samples(self) -> int:
        return len(self.values)


def load(source: str | Path) -> TindeqSession:
    """Load a single Tindeq FingerForceTraining JSON session.

    Handles both file paths and raw JSON strings.

    Args:
        source: Path to JSON file, or raw JSON string.

    Returns:
        :class:`TindeqSession` with parsed force data.

    Raises:
        ValueError: If JSON structure is not recognised.
        FileNotFoundError: If file path does not exist.

    References:
        Tindeq Progressor specification (80 Hz, 0.1 kg resolution).
    """
    if isinstance(source, Path) or (
        isinstance(source, str) and not source.lstrip().startswith(("{", "["))
    ):
        path = Path(source)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        raw = path.read_text(encoding="utf-8")
        filename = path.name
    else:
        raw = source
        filename = "<string>"

    data = json.loads(raw)

    if isinstance(data, list):
        return _parse_array_format(data, filename)

    return _parse_session(data, filename)


def load_all(directory: str | Path) -> list[TindeqSession]:
    """Load all Tindeq JSON sessions from a directory.

    Scans for ``*.json`` files and attempts to parse each.
    Files that fail to parse are silently skipped.

    Args:
        directory: Path to directory containing JSON files.

    Returns:
        List of successfully parsed sessions, sorted by filename.

    References:
        Tindeq Progressor specification (80 Hz, 0.1 kg resolution).
    """
    d = Path(directory)
    if not d.is_dir():
        raise NotADirectoryError(f"Not a directory: {d}")

    sessions: list[TindeqSession] = []
    for f in sorted(d.glob("*.json")):
        try:
            sessions.append(load(f))
        except (ValueError, KeyError, json.JSONDecodeError):
            continue
    return sessions


def extract_mvc7(
    session: TindeqSession,
    n_seconds: float = 7.0,
    smooth_ms: float = 50.0,
) -> float:
    """Extract MVC-7 (best 7-second average) from a Tindeq session.

    Applies smoothing before extraction.

    Args:
        session: Parsed Tindeq session.
        n_seconds: Window duration (default: 7.0 s).
        smooth_ms: Smoothing window in ms (0 to disable).

    Returns:
        Best n-second average force in kg.

    References:
        Giles et al. (2006) :cite:`giles2006` — MVC-7 protocol.
    """
    values = session.values
    if smooth_ms > 0:
        values = smooth(values, session.sample_rate_hz, window_ms=smooth_ms)
    return best_n_second_average(values, session.sample_rate_hz, n_seconds)


def extract_peaks(
    session: TindeqSession,
    min_force_kg: float = 5.0,
    min_duration_s: float = 1.0,
    smooth_ms: float = 50.0,
) -> list[Peak]:
    """Extract force peaks from a Tindeq session.

    Args:
        session: Parsed Tindeq session.
        min_force_kg: Minimum force threshold.
        min_duration_s: Minimum peak duration.
        smooth_ms: Smoothing window in ms (0 to disable).

    Returns:
        List of detected peaks.

    References:
        Levernier & Laffaye (2019) :cite:`levernier2019`
        — force peak detection methodology.
    """
    values = session.values
    if smooth_ms > 0:
        values = smooth(values, session.sample_rate_hz, window_ms=smooth_ms)
    return detect_peaks(values, session.sample_rate_hz, min_force_kg, min_duration_s)


# ---------------------------------------------------------------------------
# Internal parsing
# ---------------------------------------------------------------------------


def _parse_session(data: dict, filename: str) -> TindeqSession:
    """Parse a JSON dict into a TindeqSession."""
    # FingerForceTraining format detection
    if "samples" in data:
        return _parse_fft_format(data, filename)
    if "data" in data and isinstance(data["data"], list):
        return _parse_simple_format(data, filename)
    if isinstance(data, list):
        return _parse_array_format(data, filename)

    raise ValueError(
        f"Unrecognised Tindeq JSON structure in {filename}. "
        f"Expected 'samples', 'data', or array format. "
        f"Top-level keys: {list(data.keys()) if isinstance(data, dict) else 'array'}"
    )


def _parse_fft_format(data: dict, filename: str) -> TindeqSession:
    """Parse FingerForceTraining app format with 'samples' key."""
    samples = data["samples"]
    values: list[float] = []
    timestamps: list[int] = []

    for s in samples:
        if isinstance(s, dict):
            values.append(float(s.get("value", s.get("force", s.get("v", 0)))))
            ts = s.get("timestamp", s.get("time", s.get("t", 0)))
            timestamps.append(int(ts))
        elif isinstance(s, (list, tuple)):
            if len(s) >= 2:
                timestamps.append(int(s[0]))
                values.append(float(s[1]))
            else:
                values.append(float(s[0]))

    sample_rate = _detect_sample_rate(timestamps) if timestamps else TINDEQ_SAMPLE_RATE_HZ

    metadata = {k: v for k, v in data.items() if k != "samples"}

    return TindeqSession(
        filename=filename,
        sample_rate_hz=sample_rate,
        values=values,
        timestamps_us=timestamps,
        metadata=metadata,
    )


def _parse_simple_format(data: dict, filename: str) -> TindeqSession:
    """Parse simple format with 'data' array of force values."""
    raw_data = data["data"]
    values: list[float] = []
    timestamps: list[int] = []

    for item in raw_data:
        if isinstance(item, dict):
            values.append(float(item.get("force", item.get("value", 0))))
            if "time" in item or "timestamp" in item:
                timestamps.append(int(item.get("time", item.get("timestamp", 0))))
        elif isinstance(item, (int, float)):
            values.append(float(item))

    sample_rate = data.get("sampleRate", data.get("sample_rate", None))
    if sample_rate is None:
        sample_rate = _detect_sample_rate(timestamps) if timestamps else TINDEQ_SAMPLE_RATE_HZ
    else:
        sample_rate = float(sample_rate)

    metadata = {k: v for k, v in data.items() if k != "data"}

    return TindeqSession(
        filename=filename,
        sample_rate_hz=sample_rate,
        values=values,
        timestamps_us=timestamps,
        metadata=metadata,
    )


def _parse_array_format(data: list, filename: str) -> TindeqSession:
    """Parse bare array of force values."""
    values = [float(v) for v in data]
    return TindeqSession(
        filename=filename,
        sample_rate_hz=TINDEQ_SAMPLE_RATE_HZ,
        values=values,
    )


def _detect_sample_rate(timestamps: list[int]) -> float:
    """Detect sample rate from timestamp intervals."""
    if len(timestamps) < 2:
        return TINDEQ_SAMPLE_RATE_HZ

    # Detect if timestamps are in microseconds or milliseconds
    diffs: list[int] = []
    for i in range(1, min(100, len(timestamps))):
        d = timestamps[i] - timestamps[i - 1]
        if d > 0:
            diffs.append(d)

    if not diffs:
        return TINDEQ_SAMPLE_RATE_HZ

    median_diff = sorted(diffs)[len(diffs) // 2]

    # Microseconds: typical diff ~12500 for 80 Hz
    if median_diff > 5000:
        return 1_000_000.0 / median_diff

    # Milliseconds: typical diff ~12-13 for 80 Hz
    if median_diff > 5:
        return 1_000.0 / median_diff

    return TINDEQ_SAMPLE_RATE_HZ
