# climbing-science — Implementierungsplan

## Vision

Open-Source Python-Bibliothek für Climbing-Science-Berechnungen.
Füllt die Lücke zwischen proprietären Web-Calculators (StrengthClimbing.com)
und den Rohdaten aus Tindeq/Climbro-Kraftmessungen.

**Prinzipien:**

- Jede Formel mit Quellenangabe (Paper, Buch, Seite)
- Validiert gegen publizierte Benchmarks (Lattice, Giles et al.)
- Zero Dependencies im Core (nur stdlib + numpy optional)
- Kompatibel mit Tindeq-JSON aus FingerForceTraining iOS-App

---

## Gap-Analyse

### Was existiert wo

| Fähigkeit                        | SC (JS/Web)    | iOS App (Swift) | Skills (Prosa) | Python |
| -------------------------------- | -------------- | --------------- | -------------- | ------ |
| Rohmert-Kurve (Fatigue-Modell)   | ✅ proprietär  | ❌              | ✅ beschrieben | ❌     |
| Edge-Depth-Korrektur (Amca)      | ✅ proprietär  | ❌              | ✅ beschrieben | ❌     |
| MVC-7 → Grad-Prediction          | ✅ proprietär  | ❌ (Phase 2c)   | ✅ Tabelle     | ❌     |
| Critical Force (CF/W')           | ✅ proprietär  | ❌ (Phase 3a)   | ✅ beschrieben | ❌     |
| Hangboard Load Calculator        | ✅ proprietär  | ❌              | ✅ beschrieben | ❌     |
| Sport Climbing Level Calculator  | ✅ Premium     | ❌              | ❌             | ❌     |
| RFD-Analyse                      | ✅ Premium     | ❌ (Phase 3a)   | ❌             | ❌     |
| Tindeq JSON → Assessment         | ❌             | Rohdaten ✅     | ❌             | ❌     |
| Force-Curve Signalverarbeitung   | ❌             | ❌              | ❌             | ❌     |

### Kernlücke

Es gibt **keine offene, validierte Python-Bibliothek** für Climbing-Science-Berechnungen.
StrengthClimbing hat alles als proprietäres JavaScript hinter einer Paywall.
Die Copilot-Skills *beschreiben* die Formeln. Die iOS-App *misst*.
Aber **niemand rechnet offen und reproduzierbar**.

---

## Architektur — Drei-Schichten-Trennung

```
┌─────────────────────────────────────────────────────────┐
│                    Layer 3: APP                          │
│         Führt durch Tests & Workouts                    │
│                                                         │
│  cli.py          Session-Runner, interaktive Prompts    │
│  tindeq_io.py    Tindeq JSON lesen/schreiben            │
│  report.py       Assessment-Reports generieren          │
└──────────────────────┬──────────────────────────────────┘
                       │ nutzt
┌──────────────────────▼──────────────────────────────────┐
│                 Layer 2: EXERCISES                       │
│         Protokoll-Definitionen & Trainingsplanung       │
│                                                         │
│  protocols.py    Alle Hangboard-Protokolle (Daten)      │
│  hangboard_calc  Trainingslasten berechnen              │
│  periodization   Makro/Meso/Mikro-Zyklen (optional)    │
└──────────────────────┬──────────────────────────────────┘
                       │ nutzt
┌──────────────────────▼──────────────────────────────────┐
│                 Layer 1: MODELS                          │
│         Reine Mathematik — kein I/O, kein State         │
│                                                         │
│  rohmert.py          Isometrische Fatigue-Kurve         │
│  edge_depth.py       Edge-Depth-Korrektur               │
│  critical_force.py   CF/W' aus 3-Punkt-Test             │
│  strength_analyzer   MVC → Grad-Prediction              │
│  grades.py           Grad-Konvertierung                 │
│  signal.py           Force-Curve Signalverarbeitung     │
└─────────────────────────────────────────────────────────┘
```

### Warum diese Trennung?

| Schicht | Verantwortung | Abhängigkeiten | Änderungs­frequenz |
| ------- | ------------- | -------------- | ------------------- |
| **Models** | Physik & Mathematik | Keine (pure functions) | Selten (Paper-basiert) |
| **Exercises** | Was wird trainiert, wie | Nur Models | Mittel (neue Protokolle) |
| **App** | Wie wird durchgeführt, I/O | Models + Exercises | Oft (UX, Formate) |

**Regel:** Jede Schicht kennt nur die darunterliegende. Models wissen nichts von
Protokollen. Protokolle wissen nichts von Tindeq-JSON oder CLI.

---

## Datei-Struktur

```
src/climbing_science/
├── __init__.py
│
├── models/                    # Layer 1: Pure Math
│   ├── __init__.py
│   ├── rohmert.py             # Isometrische Fatigue-Kurve
│   ├── edge_depth.py          # Edge-Depth-Korrektur (Amca)
│   ├── critical_force.py      # CF/W' Regression
│   ├── strength_analyzer.py   # MVC → Grad-Prediction
│   ├── grades.py              # Grad-Konvertierung (UIAA/French/V/Font/YDS)
│   └── signal.py              # Signalverarbeitung (Smoothing, Peak Detection, RFD)
│
├── exercises/                 # Layer 2: Protokolle & Planung
│   ├── __init__.py
│   ├── protocols.py           # Protokoll-Definitionen (Datenklassen)
│   └── hangboard_calc.py      # Trainingslasten aus MVC + Protokoll
│
└── app/                       # Layer 3: I/O & Durchführung
    ├── __init__.py
    ├── tindeq_io.py           # Tindeq JSON lesen, Sessions parsen
    ├── report.py              # Assessment-Report generieren
    └── cli.py                 # CLI-Runner (optional)

tests/
├── models/
│   ├── test_rohmert.py
│   ├── test_edge_depth.py
│   ├── test_critical_force.py
│   ├── test_strength_analyzer.py
│   ├── test_grades.py
│   └── test_signal.py
├── exercises/
│   ├── test_protocols.py
│   └── test_hangboard_calc.py
└── app/
    ├── test_tindeq_io.py
    └── test_report.py
```

---

## Module — Layer 1: Models

### Modul 1: `rohmert.py` — Isometrische Fatigue-Kurve

**Priorität:** 🔴 Fundament für alles andere

**Wissenschaftliche Basis:**

- Rohmert W. (1960). *Ermittlung von Erholungspausen für statische Arbeit des Menschen.*
  Internationale Zeitschrift für Angewandte Physiologie, 18, 123–164.
- Monod H., Scherrer J. (1965). *The work capacity of a synergic muscular group.*
  Ergonomics, 8(3), 329–338.

**Formeln:**

```
# Rohmert (1960) — Original
t_max = f(F/MVC)  # Zeit bis Ermüdung als Funktion der relativen Intensität

# Klassische Approximation (Sjøgaard 1986 / Frey-Law & Avin 2010):
t_max(p) = a * (p / (1 - p))^b   wobei p = F/MVC (0..1)

# SC-Variante (Banaszczyk):
# 3 Modelle: Beginner / Intermediate / Expert
# Unterschiedliche Koeffizienten für Ermüdungsresistenz
# → Parameter aus SC-Website reverse-engineeren oder eigene Fits publizieren
```

**Funktionen:**

```python
def time_to_failure(force_ratio: float, model: str = "intermediate") -> float:
    """Maximale Haltezeit bei gegebener relativer Intensität (F/MVC).

    Args:
        force_ratio: Relative Kraft (0.0 – 1.0), z.B. 0.8 für 80% MVC
        model: "beginner" | "intermediate" | "expert"

    Returns:
        Geschätzte Zeit bis Ermüdung in Sekunden

    References:
        Rohmert (1960), Sjøgaard (1986)
    """

def force_ratio_for_time(target_time: float, model: str = "intermediate") -> float:
    """Inverse: Welche relative Intensität erlaubt Hang für target_time Sekunden?"""

def mvc7_from_test(total_load_kg: float, hang_time_s: float,
                   model: str = "intermediate") -> float:
    """Konvertiert beliebigen Test-Hang zu MVC-7 (7-Sekunden-Maximum).

    Beispiel: 85 kg Last, 23 Sekunden gehalten → MVC-7 = 110.5 kg
    """
```

**Tests:**

- Bekannte Punkte: bei 100% MVC → t_max ≈ 7s, bei 15% MVC → t_max > 600s
- Vergleich der 3 Modelle: Expert hält länger bei gleicher %MVC als Beginner
- Round-Trip: `force_ratio_for_time(time_to_failure(p)) ≈ p`
- Validierung gegen SC Hangboard Calculator Beispiel:
  BW=65, +20kg, 15mm Edge, 23s → MVC-7 @20mm = 110.5 kg

---

### Modul 2: `edge_depth.py` — Edge-Depth-Korrektur

**Priorität:** 🟡 Benötigt für korrekte Vergleiche

**Wissenschaftliche Basis:**

- Amca A.M. et al. (2012). *The effect of hold depth on grip strength and endurance.*
- StrengthClimbing: 2.5%/mm Korrektur relativ zu 20mm Referenz

**Formeln:**

```
# Lineare Korrektur (SC-Modell):
correction_factor(edge_mm) = 1 + 0.025 * (20 - edge_mm)

# Beispiel: 15mm Edge → Faktor 1.125 (12.5% schwerer als 20mm)
# Beispiel: 25mm Edge → Faktor 0.875 (12.5% leichter als 20mm)

# Kraft auf Referenz-Edge:
F_20mm = F_measured * correction_factor(test_edge_mm)
```

**Funktionen:**

```python
def correction_factor(edge_mm: float, reference_mm: float = 20.0) -> float:
    """Korrekturfaktor für Edge-Tiefe relativ zur Referenz.

    References:
        Amca et al. (2012), StrengthClimbing.com
    """

def convert_force(force_kg: float, from_edge_mm: float,
                  to_edge_mm: float) -> float:
    """Konvertiert Kraft zwischen verschiedenen Edge-Tiefen."""
```

**Tests:**

- 20mm → 20mm: Faktor = 1.0
- Symmetrie: convert(convert(F, 15, 20), 20, 15) ≈ F
- Bekannte Werte aus SC Calculator verifizieren

---

### Modul 3: `signal.py` — Force-Curve Signalverarbeitung

**Priorität:** 🟡 Basis für Tindeq-Auswertung

**Schicht:** Models — reine Mathematik auf Zeitreihen, kein I/O

**Funktionen:**

```python
def smooth(values: list[float], timestamps_us: list[int],
           method: str = "moving_average",
           window_ms: int = 50) -> list[float]:
    """Glättet ein Force-Signal. Methoden: moving_average, exponential."""

def detect_peaks(values: list[float], timestamps_us: list[int],
                 min_value: float = 5.0,
                 min_duration_s: float = 1.0) -> list[Peak]:
    """Erkennt Kraft-Peaks (für automatische Segmentierung).

    Returns:
        Liste von Peak(start_idx, end_idx, peak_idx, peak_value, duration_s)
    """

def compute_rfd(values: list[float], timestamps_us: list[int],
                window: tuple[float, float] = (0.2, 0.8)) -> RFDResult:
    """Rate of Force Development: Kraftanstieg im 20–80% Fenster.

    Returns:
        RFDResult(peak_rfd_kg_s, time_to_peak_s, avg_rfd_kg_s)
    """

def best_n_second_average(values: list[float], timestamps_us: list[int],
                          n_seconds: float = 7.0) -> float:
    """Bester Durchschnitt über ein gleitendes N-Sekunden-Fenster.

    Zentral für MVC-7 Extraktion.
    """

def compute_impulse(values: list[float], timestamps_us: list[int]) -> float:
    """Kraft-Impuls (Integral: kg·s) via Trapezregel."""
```

**Tests:**

- Konstantes Signal → Smoothing ändert nichts
- Dreieckspuls → Peak Detection findet genau einen Peak
- Linearer Anstieg → RFD ist exakt die Steigung
- Rechteck 7s @ 50kg → best_7s_average = 50.0
- Bekannter Impuls: 10s @ 50kg → impulse = 500 kg·s

---

### Modul 4: `strength_analyzer.py` — Grad-Prediction aus Fingerkraft

**Priorität:** 🔴 Kernfeature

**Schicht:** Models — nutzt Rohmert + Edge-Depth + Grades, kein I/O

**Wissenschaftliche Basis:**

- Giles D. et al. (2019). *The Determination of Finger-Flexor Critical Force in Rock Climbers.*
  Int J Sports Physiol Perform, 1–8.
- Hörst E. (2016). *Training for Climbing.* 3rd ed., Table 4.2 (MVC/BW → Grade)
- Lattice Training Assessment Benchmarks (n=436)
- r/climbharder Survey 2017 (n=555)
- StrengthClimbing: toclimb8a.shinyapps.io/maxtograde

**Datenquellen für Regression:**

```
# Per-Hand MVC/BW → UIAA Grade (interpoliert aus Hörst §4.2)
# Diese Tabelle ist der Kern des Analyzers:
GRADE_TABLE = {
    # MVC_per_hand_%BW : UIAA_grade
    50:  "5",      # ~V0
    60:  "6-",     # ~V1
    65:  "6",      # ~V2
    70:  "6+",     # ~V3
    75:  "7-",     # ~V4
    80:  "7",      # ~V5
    85:  "7+",     # ~V6
    90:  "8-",     # ~V7
    95:  "8",      # ~V8
    100: "8+",     # ~V9
    105: "9-",     # ~V10
    110: "9",      # ~V11
    115: "9+",     # ~V12
    120: "10-",    # ~V13
    130: "10",     # ~V14
    140: "10+",    # ~V15
}
# HINWEIS: SC verwendet 2-Hand-Total, Lattice ebenfalls.
# Hörst §4.2 gibt Per-Hand-Werte.
# → Klare Dokumentation welche Konvention verwendet wird!
```

**Funktionen:**

```python
def predict_grade(mvc7_kg: float, bodyweight_kg: float,
                  edge_mm: float = 20,
                  training_mode: int = 1,
                  height_cm: float | None = None,
                  arm_span_cm: float | None = None) -> GradeResult:
    """Sagt Klettergrad aus Fingerkraft voraus.

    Args:
        mvc7_kg: MVC-7 Gesamtlast (BW + Zusatzgewicht) in kg
        bodyweight_kg: Körpergewicht in kg
        edge_mm: Test-Edge-Tiefe (5–35mm)
        training_mode: 1=kein Hangboard, 2=Repeaters, 3=MaxHangs, 4=MaxHangs+added
        height_cm: Optional — für Ape-Index-Korrektur
        arm_span_cm: Optional — für Ape-Index-Korrektur

    Returns:
        GradeResult mit boulder_grade, sport_grade, mvc_bw_ratio,
        assessment_text, training_recommendations
    """

@dataclass
class GradeResult:
    boulder_uiaa: str          # z.B. "8-"
    boulder_font: str          # z.B. "7A"
    boulder_v: str             # z.B. "V7"
    sport_french: str | None   # z.B. "7b+" (wenn CF verfügbar)
    mvc_bw_ratio: float        # z.B. 1.62
    mvc_bw_per_hand: float     # z.B. 0.81
    percentile: str            # z.B. "Advanced"
    assessment: str            # Freitext-Bewertung
```

**Tests:**

- Bekannte Lattice-Benchmarks reproduzieren
- SC Analyzer Beispiele verifizieren (aus Webseite)
- Edge cases: Anfänger (ratio < 0.5), Elite (ratio > 1.4)

---

### Modul 4: `critical_force.py` — Critical Force & W'

**Priorität:** 🔴 Einziges offenes CF-Modell

**Wissenschaftliche Basis:**

- Monod H., Scherrer J. (1965). *The work capacity of a synergic muscular group.*
- Giles D. et al. (2019). *Finger-Flexor Critical Force in Rock Climbers.*
- Poole D.C. et al. (2016). *Critical Power: An Important Fatigue Threshold.*
  Medicine & Science in Sports & Exercise, 48(11), 2320–2334.

**Modell:**

```
# Critical Power / Critical Force Konzept:
# t_lim = W' / (P - CF)
# wobei: t_lim = Time to failure, P = Power/Force, CF = Critical Force, W' = Anaerobic capacity

# Umgestellt für 7/3 Repeaters (intermittent protocol):
# Tlim_total(P) = W' / (P_eff - CF)
# P_eff berücksichtigt Work/Rest-Verhältnis (7s on / 3s off)

# 3-Punkt-Test:
# t80 = kumulative Hangzeit bei 80% MVC-7 (7/3 Repeaters bis Failure)
# t60 = kumulative Hangzeit bei 60% MVC-7
# t45 = kumulative Hangzeit bei 45% MVC-7 (oder 50%/55%)
#
# Lineare Regression: W_total = CF * t_total + W'
# → CF = Steigung, W' = y-Achsenabschnitt
```

**Funktionen:**

```python
def calculate_cf(mvc7_kg: float, bodyweight_kg: float,
                 t80_s: float, t60_s: float,
                 t_low_s: float, low_pct: float = 0.45,
                 edge_mm: float = 20) -> CFResult:
    """Berechnet Critical Force aus 3-Punkt-Test.

    Args:
        mvc7_kg: MVC-7 Gesamtlast in kg
        bodyweight_kg: Körpergewicht
        t80_s: Kumulative Hangzeit bei 80% MVC (7/3 Repeaters)
        t60_s: Kumulative Hangzeit bei 60% MVC
        t_low_s: Kumulative Hangzeit bei low_pct MVC
        low_pct: Dritter Testpunkt (0.45, 0.50 oder 0.55)
        edge_mm: Test-Edge (10–35mm)

    Returns:
        CFResult mit CF, W', CF/BW-Ratio, Assessment
    """

@dataclass
class CFResult:
    cf_kg: float               # Critical Force in kg
    w_prime_kgs: float         # Anaerobic capacity in kg·s
    cf_bw_ratio: float         # CF / Bodyweight
    cf_mvc_ratio: float        # CF / MVC-7 (typisch 0.35–0.55)
    predicted_sport_grade: str # French-Grad basierend auf CF
    endurance_assessment: str  # "Below average" / "Average" / "Above average"
    training_load_cf_kg: float # Empfohlene Last für CF-Training
    r_squared: float           # Güte des linearen Fits
```

**Tests:**

- SC Demo-Datensatz: BW=65, MVC-7=105, t80=77, t60=136, t45=323
- Giles et al. (2019) publizierte CF-Werte verschiedener Leistungsgruppen
- R² > 0.95 für gute Testdaten
- CF muss immer < MVC-7 sein

---

---

## Module — Layer 2: Exercises

### Modul 5: `protocols.py` — Protokoll-Definitionen

**Priorität:** 🟡 Reine Daten, keine Logik

**Schicht:** Exercises — beschreibt *was* trainiert wird, nicht *wie* berechnet

```python
@dataclass(frozen=True)
class HangboardProtocol:
    """Unveränderbare Protokoll-Definition."""
    id: str
    name: str
    author: str
    intensity_range: tuple[float, float]  # %MVC-7, z.B. (0.88, 1.04)
    hang_s: float
    rest_s: float
    sets: int
    reps: int | None                      # None = "bis Failure"
    set_rest_s: float
    energy_system: str                    # "alactic" | "lactic" | "aerobic"
    notes: str

PROTOCOLS: dict[str, HangboardProtocol] = {
    "lopez_maxhangs":      HangboardProtocol("lopez_maxhangs", "Eva López MaxHangs (MAW)", "López", (0.88, 1.04), 10, 180, 4, 1, 180, "alactic", "..."),
    "lopez_inthangs":      HangboardProtocol("lopez_inthangs", "Eva López IntHangs", "López", (0.60, 0.80), 10, 5, 4, 4, 60, "lactic", "..."),
    "lopez_subhangs":      HangboardProtocol("lopez_subhangs", "Eva López SubHangs", "López", (0.55, 0.85), 30, 120, 3, 1, 120, "lactic", "..."),
    "horst_7_53":          HangboardProtocol("horst_7_53", 'Eric Hörst "7-53"', "Hörst", (0.92, 0.97), 7, 53, 3, 3, 180, "alactic", "..."),
    "bechtel_ladders":     HangboardProtocol("bechtel_ladders", "Steve Bechtel 3-6-9 Ladders", "Bechtel", (0.88, 0.95), 12, 180, 3, 1, 180, "alactic", "..."),
    "repeaters_7_3":       HangboardProtocol("repeaters_7_3", "7/3 Repeaters", "Industry", (0.40, 0.80), 7, 3, 6, 6, 180, "lactic", "..."),
    "endurance_repeaters": HangboardProtocol("endurance_repeaters", "Endurance Repeaters", "Industry", (0.25, 0.60), 7, 3, 1, None, 0, "aerobic", "..."),
    "density_hangs":       HangboardProtocol("density_hangs", "Tyler Nelson Density Hangs", "Nelson", (0.50, 0.80), 20, 10, 5, 1, 120, "lactic", "..."),
    "one_arm_hangs":       HangboardProtocol("one_arm_hangs", "One-Arm Hangs", "Webb-Parsons", (0.94, 1.06), 7, 180, 3, 1, 180, "alactic", "..."),
}
```

**Wichtig:** Protokolle sind *Daten*, keine Berechnungen. Sie wissen nichts
von Rohmert oder Edge-Depth. Sie beschreiben nur Struktur und Intensitätsbereiche.

---

### Modul 6: `hangboard_calc.py` — Training Load Calculator

**Priorität:** 🟡 Höchster Alltagsnutzen

**Schicht:** Exercises — verbindet Protokoll-Definitionen mit Model-Berechnungen

**Abhängigkeiten:** `models.rohmert`, `models.edge_depth`, `exercises.protocols`

```python
def calculate_training_load(mvc7_kg: float, bodyweight_kg: float,
                            protocol: str | HangboardProtocol,
                            edge_mm: float = 20,
                            model: str = "intermediate") -> TrainingPlan:
    """Berechnet exakte Trainingslasten für ein gegebenes Protokoll.

    Nutzt Rohmert für Time-to-Failure und Edge-Depth für Kantenkorrektur.
    Das Protokoll liefert nur die Struktur (Sets, Reps, Intensität).

    Returns:
        TrainingPlan mit added_load_kg, tut_per_set, total_tut, difficulty
    """

def compare_protocols(mvc7_kg: float, bodyweight_kg: float,
                      protocols: list[str] | None = None) -> list[ProtocolComparison]:
    """Vergleicht mehrere Protokolle nebeneinander (TUT, Volumen, Last)."""
```

**Tests:**

- SC Hangboard Calculator Beispiel: BW=65, +20kg, 15mm, 23s → MVC-7@20mm = 110.5 kg
- Protokoll-spezifische Lasten gegen SC-Ergebnisse prüfen
- Edge-Konvertierung: gleiche relative Intensität auf verschiedenen Edges

---

## Module — Layer 3: App

### Modul 7: `tindeq_io.py` — Tindeq JSON Pipeline

**Priorität:** 🟡 Verbindet Messung mit Analyse

**Schicht:** App — I/O, Dateisystem, Format-Parsing

**Abhängigkeiten:** `models.signal` (für Smoothing/Peak Detection)

```python
def load_session(path: str) -> ForceSession:
    """Lädt eine FingerForceTraining JSON-Session.

    Kompatibel mit dem Format aus der iOS-App:
    {
        "samples": [{"forceKg": 51.2, "timestampUs": 0}, ...],
        "segments": [...],
        "testType": "MaxHang",
        ...
    }
    """

def extract_mvc7(session: ForceSession) -> float:
    """Extrahiert MVC-7 aus einer MaxHang/MVC-Session.

    Findet den besten 7-Sekunden-Durchschnitt über alle Work-Segmente.
    Nutzt models.signal für Smoothing.
    """

def extract_rfd(session: ForceSession,
                window: tuple[float, float] = (0.2, 0.8)) -> RFDResult:
    """Berechnet Rate of Force Development aus Rohdaten.

    Nutzt models.signal für Peak Detection und Slope-Berechnung.
    """
```

**Tests:**

- Synthetische Testdaten (Sinuswelle, Rechteck, realistisches MVC-Profil)
- MVC-7 Extraktion: bekannter Peak bei bekanntem Zeitpunkt
- Backward-Kompatibilität: UInt32-Timestamps aus älteren Sessions

---

### Modul 8: `report.py` — Assessment-Report Generator

**Priorität:** 🟢 End-to-End-Ergebnis

**Schicht:** App — orchestriert alle Layer zu einem Gesamtergebnis

**Abhängigkeiten:** Alle Models + Exercises

```python
def generate_report(session: ForceSession,
                    bodyweight_kg: float,
                    edge_mm: float = 20,
                    height_cm: float | None = None) -> AssessmentReport:
    """End-to-End Pipeline:

    1. tindeq_io.extract_mvc7(session)       → MVC-7
    2. models.strength_analyzer.predict_grade → Grad-Prediction
    3. exercises.hangboard_calc               → Trainingsempfehlungen
    4. Optional: CF-Test → critical_force     → Endurance-Assessment

    Gibt strukturierten Report zurück (dict/dataclass), kein Rendering.
    """

@dataclass
class AssessmentReport:
    mvc7_kg: float
    mvc_bw_ratio: float
    predicted_boulder: str
    predicted_sport: str | None
    cf_result: CFResult | None
    training_recommendations: list[ProtocolRecommendation]
    weaknesses: list[str]
```

---

### Modul 9: `cli.py` — CLI Runner (optional)

**Priorität:** 🟢 Nice-to-have

**Schicht:** App — interaktive Benutzerführung

```python
# Beispiel-Aufrufe:

# Grad-Prediction aus MVC-7:
$ climbing-science analyze --mvc7 105 --bw 65 --edge 20

# Trainingsplan berechnen:
$ climbing-science plan --mvc7 105 --bw 65 --protocol lopez_maxhangs

# Tindeq-Session auswerten:
$ climbing-science report session_20260401.json --bw 65

# Protokolle vergleichen:
$ climbing-science compare --mvc7 105 --bw 65

# Grade konvertieren:
$ climbing-science grade "7a+" --to uiaa
```

---

## Abhängigkeits-Graph

```
Layer 1 — MODELS (pure functions, kein I/O)
┌──────────┐  ┌───────────┐
│ grades   │  │ rohmert   │ ← Fundament
└──────────┘  └─────┬─────┘
                    │
              ┌─────┴─────┐
              ▼           ▼
         ┌──────────┐ ┌───────────────────┐
         │edge_depth│ │strength_analyzer  │
         └──────────┘ │(rohmert + grades) │
              │       └───────────────────┘
              │
         ┌────┘   ┌──────────────────┐
         │        │ critical_force   │ (eigenständig)
         │        └──────────────────┘
         │
         ▼
    ┌──────────┐
    │ signal   │ (eigenständig, pure math)
    └──────────┘

Layer 2 — EXERCISES (Protokoll-Daten + Berechnung)
┌──────────────┐    ┌────────────────────────────┐
│ protocols    │───▶│ hangboard_calc             │
│ (pure data)  │    │ (protocols + rohmert + edge)│
└──────────────┘    └────────────────────────────┘

Layer 3 — APP (I/O, Orchestrierung)
┌─────────────┐  ┌──────────┐  ┌─────────┐
│ tindeq_io   │  │ report   │  │  cli    │
│ (signal)    │  │ (alles)  │  │ (alles) │
└─────────────┘  └──────────┘  └─────────┘
```

## Implementierungsreihenfolge

**Layer 1 zuerst (bottom-up):**

1. **`models/grades.py`** — Lookup-Tabellen, kein Mathe, schneller Win
2. **`models/rohmert.py`** — Mathematisches Fundament, gut testbar
3. **`models/edge_depth.py`** — Einfach, braucht Rohmert nicht direkt
4. **`models/signal.py`** — Smoothing, Peak Detection, RFD (pure math)
5. **`models/strength_analyzer.py`** — Nutzt Rohmert + Edge + Grades, erstes "Wow"
6. **`models/critical_force.py`** — Eigenständiges Modell, lineare Regression

**Dann Layer 2:**

7. **`exercises/protocols.py`** — Reine Datenklassen, sofort testbar
8. **`exercises/hangboard_calc.py`** — Verbindet Protokolle mit Models

**Zuletzt Layer 3:**

9. **`app/tindeq_io.py`** — JSON-Parsing + Signal-Extraktion
10. **`app/report.py`** — End-to-End Assessment
11. **`app/cli.py`** — Interaktives CLI

## Referenzen

1. Rohmert W. (1960). Ermittlung von Erholungspausen für statische Arbeit des Menschen. Int Z Angew Physiol, 18, 123–164.
2. Monod H., Scherrer J. (1965). The work capacity of a synergic muscular group. Ergonomics, 8(3), 329–338.
3. Giles D. et al. (2019). Finger-Flexor Critical Force in Rock Climbers. Int J Sports Physiol Perform.
4. Amca A.M. et al. (2012). Effect of hold depth on grip strength and endurance.
5. Hörst E. (2016). Training for Climbing. 3rd ed., Falcon Guides.
6. Poole D.C. et al. (2016). Critical Power: An Important Fatigue Threshold. Med Sci Sports Exerc, 48(11).
7. López-Rivera E., González-Badillo J.J. (2012). The effects of two maximum grip strength training methods. JSCR, 26(4), 1078–1085.
8. Lattice Training Assessment Data (n=436). latticetraining.com.
9. Sjøgaard G. (1986). Intramuscular changes during long-term contraction. In: The Ergonomics of Working Postures.
10. Frey-Law L.A., Avin K.G. (2010). Endurance time is joint-specific. Muscle & Nerve, 42(5), 799–807.
11. Banaszczyk J. StrengthClimbing.com — Finger Strength Analyzer, Hangboard Calculator, CF Calculator.
