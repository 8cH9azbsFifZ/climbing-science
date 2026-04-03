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

## Architektur — Vier Schichten + kanonisches Datenmodell

### Designziel

Die Bibliothek soll **geräte- und app-unabhängig** sein:

- Tindeq Progressor, Climbro, Griptonite, Crane Scale, manuelle Eingabe — egal
- FingerForceTraining iOS, Tindeq App, Climbro App, CSV-Export — egal
- CLI, Jupyter Notebook, Web-API, Swift-Einbettung — egal

Dafür braucht es ein **kanonisches Datenmodell** als Lingua Franca zwischen
allen Quellen und allen Berechnungen.

### Schichten-Diagramm

```
┌─────────────────────────────────────────────────────────────┐
│                    Layer 4: FRONTENDS                        │
│         Konkrete Anwendungen — austauschbar                 │
│                                                             │
│  cli.py            CLI-Runner ($ climbing-science analyze)  │
│  notebook.py       Jupyter-Helpers (Plot, DataFrame-Export) │
│  report.py         Assessment-Report (Markdown/HTML/dict)   │
└──────────────────────────┬──────────────────────────────────┘
                           │ nutzt
┌──────────────────────────▼──────────────────────────────────┐
│                    Layer 3: I/O ADAPTERS                     │
│         Liest/schreibt externe Formate → kanonisches Modell │
│                                                             │
│  adapters/                                                  │
│    tindeq.py       FingerForceTraining JSON & Tindeq App    │
│    climbro.py      Climbro CSV/JSON                         │
│    griptonite.py   Griptonite-Daten (Format TBD)            │
│    manual.py       Manuelle Eingabe (BW, MVC-7, Hangzeit)   │
│    csv_generic.py  Generischer CSV-Import (Zeit, Kraft)     │
└──────────────────────────┬──────────────────────────────────┘
                           │ erzeugt/konsumiert
┌──────────────────────────▼──────────────────────────────────┐
│              KANONISCHES DATENMODELL (datamodel.py)          │
│         Geräte-unabhängig — die "Währung" der Bibliothek    │
│                                                             │
│  ForceSample(time_s, force_kg)                              │
│  ForceSession(samples, metadata, segments?)                 │
│  AthleteProfile(weight_kg, height_cm?, fmax_r, fmax_l, ..) │
│  TestResult(mvc7_kg, cf_kg?, rfd?, grade_prediction?)       │
└──────────┬───────────────────────────────┬──────────────────┘
           │ nutzt                         │ nutzt
┌──────────▼──────────┐  ┌────────────────▼───────────────────┐
│  Layer 2: EXERCISES  │  │                                    │
│  Protokolle & Plan   │  │                                    │
│                      │  │                                    │
│  protocols.py        │  │                                    │
│  hangboard_calc.py   │  │                                    │
└──────────┬───────────┘  │                                    │
           │ nutzt        │                                    │
┌──────────▼──────────────▼───────────────────────────────────┐
│                    Layer 1: MODELS                            │
│         Reine Mathematik — kein I/O, kein State              │
│                                                              │
│  rohmert.py          Isometrische Fatigue-Kurve              │
│  edge_depth.py       Edge-Depth-Korrektur                    │
│  critical_force.py   CF/W' aus 3-Punkt-Test                  │
│  strength_analyzer   MVC → Grad-Prediction                   │
│  grades.py           Grad-Konvertierung                      │
│  signal.py           Force-Curve Signalverarbeitung          │
└──────────────────────────────────────────────────────────────┘
```

### Warum diese Trennung?

| Schicht | Verantwortung | Abhängigkeiten | Änderungs­frequenz |
| ------- | ------------- | -------------- | ------------------- |
| **Models** | Physik & Mathematik | Keine (pure functions) | Selten (Paper-basiert) |
| **Datenmodell** | Kanonische Typen | Keine (dataclasses) | Selten |
| **Exercises** | Was wird trainiert | Models + Datenmodell | Mittel (neue Protokolle) |
| **I/O Adapters** | Format-Konvertierung | Nur Datenmodell | Mittel (neue Geräte) |
| **Frontends** | Darstellung & UX | Alles | Oft (CLI, Notebook, Web) |

**Regeln:**

1. Jede Schicht kennt nur die darunterliegende
2. Models wissen nichts von Protokollen, Geräten oder UI
3. I/O Adapters importieren **nur** das Datenmodell, nie Models direkt
4. Frontends orchestrieren — sie verbinden Adapter → Models → Output
5. **Alles über dem Datenmodell ist austauschbar**

### Kanonisches Datenmodell — die Brücke

```python
# datamodel.py — Geräte-unabhängig, App-unabhängig

from dataclasses import dataclass, field

@dataclass(frozen=True)
class ForceSample:
    """Ein einzelner Kraftmesswert."""
    time_s: float       # Sekunden seit Session-Start
    force_kg: float     # Kraft in kg

@dataclass
class ForceSession:
    """Eine Mess-Session — egal woher die Daten kommen."""
    samples: list[ForceSample]
    sample_rate_hz: float | None = None  # z.B. 80 (Tindeq), 100 (Climbro)
    metadata: dict = field(default_factory=dict)
    # metadata kann enthalten:
    #   "device": "tindeq_progressor" | "climbro" | "manual" | ...
    #   "test_type": "mvc7" | "continuous" | "repeater" | ...
    #   "hold_type": "20mm_edge" | "18mm_edge" | "pinch" | ...
    #   "hand": "R" | "L" | "both"
    #   "date": "2026-04-01T18:30:00Z"

    @property
    def duration_s(self) -> float:
        if not self.samples:
            return 0.0
        return self.samples[-1].time_s - self.samples[0].time_s

    @property
    def peak_force_kg(self) -> float:
        return max(s.force_kg for s in self.samples) if self.samples else 0.0

@dataclass
class AthleteProfile:
    """Athleten-Profil — alle Berechnungen beziehen sich darauf."""
    weight_kg: float
    height_cm: float | None = None
    arm_span_cm: float | None = None
    sex: str | None = None              # "M" | "F"
    fmax_right_kg: float | None = None  # MVC-7 rechte Hand
    fmax_left_kg: float | None = None   # MVC-7 linke Hand
    training_mode: int = 1              # 1=kein HB, 2=Repeaters, 3=MaxHangs, 4=MaxHangs+added

@dataclass
class TestResult:
    """Ergebnis einer Auswertung — geräte-unabhängig."""
    mvc7_kg: float | None = None
    mvc_bw_ratio: float | None = None
    cf_kg: float | None = None
    w_prime_kgs: float | None = None
    rfd_kg_s: float | None = None
    predicted_boulder: str | None = None
    predicted_sport: str | None = None
    assessment: str | None = None
```

**Warum `frozen=True` bei ForceSample?** Messwerte sind unveränderlich.
Einmal gemessen, nie mutiert. Das macht die Daten hashbar und thread-safe.

### Geräte-Unabhängigkeit in der Praxis

```python
# Tindeq Progressor:
from climbing_science.adapters import tindeq
session = tindeq.load("session_20260401.json")

# Climbro:
from climbing_science.adapters import climbro
session = climbro.load("climbro_export.csv")

# Manuelle Eingabe (kein Gerät nötig):
from climbing_science.adapters import manual
session = manual.from_mvc7_test(bodyweight_kg=65, added_kg=32, hang_time_s=7)

# Generischer CSV (z.B. aus Arduino-Kraftsensor):
from climbing_science.adapters import csv_generic
session = csv_generic.load("kraft_messung.csv", time_col="t_s", force_col="f_kg")

# Ab hier ist alles identisch — egal welches Gerät:
from climbing_science.models import signal, strength_analyzer
mvc7 = signal.best_n_second_average(session, n_seconds=7.0)
grade = strength_analyzer.predict_grade(mvc7_kg=mvc7, bodyweight_kg=65)
```

### Jupyter-Notebook-Nutzung

Layer 1 + 2 sind sofort in Jupyter nutzbar — keine App-Schicht nötig:

```python
# In einem Jupyter Notebook:
import climbing_science.models.rohmert as rohmert
import climbing_science.models.strength_analyzer as sa
import climbing_science.models.critical_force as cf
import climbing_science.exercises.hangboard_calc as hb

# Direkte Berechnung — kein Gerät, keine Datei nötig:
t_fail = rohmert.time_to_failure(0.80)  # 80% MVC → Sekunden
grade = sa.predict_grade(mvc7_kg=105, bodyweight_kg=65)
plan = hb.calculate_training_load(mvc7_kg=105, bodyweight_kg=65, protocol="lopez_maxhangs")

# Mit Gerätedaten:
from climbing_science.adapters import tindeq
session = tindeq.load("meine_session.json")

# Plotting (Jupyter-native):
import matplotlib.pyplot as plt
times = [s.time_s for s in session.samples]
forces = [s.force_kg for s in session.samples]
plt.plot(times, forces)
plt.xlabel("Zeit (s)")
plt.ylabel("Kraft (kg)")

# Optional: Notebook-Helpers für häufige Plots
from climbing_science.frontends import notebook
notebook.plot_session(session)                   # Force-Time-Kurve
notebook.plot_rohmert_curve(model="intermediate") # Fatigue-Modell
notebook.plot_protocol_comparison(mvc7=105, bw=65) # Protokoll-Vergleich
```

---

## Datei-Struktur

```
src/climbing_science/
├── __init__.py
├── datamodel.py               # Kanonisches Datenmodell (ForceSample, ForceSession, ...)
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
├── adapters/                  # Layer 3: I/O Adapter (Format → Datenmodell)
│   ├── __init__.py
│   ├── tindeq.py              # FingerForceTraining JSON & Tindeq App
│   ├── climbro.py             # Climbro CSV/JSON
│   ├── manual.py              # Manuelle Eingabe (kein Gerät nötig)
│   └── csv_generic.py         # Generischer CSV-Import
│
└── frontends/                 # Layer 4: Anwendungen
    ├── __init__.py
    ├── cli.py                 # CLI-Runner
    ├── notebook.py            # Jupyter-Helpers (Plots, DataFrame-Export)
    └── report.py              # Assessment-Report (Markdown/HTML/dict)

notebooks/                         # Auslieferbare Jupyter-Auswertungen
├── 01_my_climbing_assessment.ipynb    # Persönliche Gesamtauswertung
├── 02_rohmert_curve_explained.ipynb   # Theorie: Isometrische Fatigue
├── 03_critical_force_analysis.ipynb   # CF-Test auswerten + verstehen
├── 04_protocol_comparison.ipynb       # Welches Protokoll passt zu mir?
├── 05_session_deep_dive.ipynb         # Tindeq-Session analysieren
├── 06_progress_tracker.ipynb          # Fortschritt über Wochen/Monate
└── 07_edge_depth_science.ipynb        # Warum 20mm? Edge-Depth-Korrektur

tests/
├── test_datamodel.py
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
├── adapters/
│   ├── test_tindeq.py
│   ├── test_climbro.py
│   └── test_manual.py
└── frontends/
    ├── test_report.py
    └── test_notebook.py
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

### Modul: `grades.py` — Grad-Konvertierung & numerischer Schwierigkeitsindex

**Priorität:** 🟢 Schneller Win, kein Mathe, Fundament für strength_analyzer

**Schicht:** Models — reine Lookup-Tabellen + Interpolation, kein I/O, kein State

**Verwandte Pakete:** `pyclimb` v0.2.0 (MIT, nur French↔YDS, veraltet, Python ≤3.10).
Wir schreiben komplett neu — vollständigere Abdeckung, numerischer Index, aktiv gepflegt.

#### Wissenschaftliche Basis & Referenzen

Die Grad-Zuordnungen zwischen Systemen sind **Konvention, keine Berechnung**.
Es gibt keine universelle Formel — nur historisch gewachsene Konsens-Tabellen,
die zwischen Quellen **teilweise voneinander abweichen** (s. Abschnitt Diskrepanzen).

**Primärquellen (akademisch/institutionell):**

1. **[CAI] Mandelli, G; Angriman, A (2016).** *Scales of Difficulty in Climbing.*
   Central School of Mountaineering, Club Alpino Italiano, Italy.
   Verfügbar via Semantic Scholar.
   → Umfassendste akademische Quelle. Erstellt für die UIAA/IFAS.
   Enthält historische Herleitung aller Systeme und offizielle Vergleichstabellen.
   **Dies ist unsere Primärreferenz für die Route-Tabelle.**

2. **[Draper2015] Draper, N; Giles, D; Schöffl, V; Fuss, FK; Watts, P; et al. (2015).**
   *Comparative grading scales, statistical analyses, climber descriptors
   and ability grouping.* Sports Technology, 8(3–4), 88–94.
   DOI: 10.1080/19346182.2015.1107081
   → Peer-reviewed! Definiert numerische IRCRA-Skala (International Rock Climbing
   Research Association) als **einheitlichen numerischen Index** über alle Systeme.
   Genau das, was wir als `difficulty_index` brauchen.

3. **[FoH] The Mountaineers (2017).** *Mountaineering: The Freedom of the Hills.*
   9th ed., Appendix A: Rating Systems, pp. 563–570.
   ISBN 978-1-68051-004-1.
   → Standardwerk. Enthält Vergleichstabellen YDS ↔ French ↔ UIAA.

**Primärquellen (Community-Konsens mit großem N):**

4. **[MP] Mountain Project (2024).** *International Climbing Grades.*
   https://www.mountainproject.com/international-climbing-grades
   → Größte US-Community. Route-Tabelle: YDS, French, UIAA, Ewbanks, SA, British.
   Separate Boulder-Tabelle: Hueco (V-Scale) ↔ Fontainebleau.
   Enthält Zwischengrade (5.10a/b, V3-4) die wir nicht übernehmen.

5. **[Rockfax] Rockfax Publishing (2022).** *Grade Conversions: Alpine Grading System.*
   https://rockfax.com/climbing-guides/grades/
   → Meistverwendete Referenz in europäischen Kletterführern.
   Enthält Route- und Boulder-Tabellen. Stimmt ab ~5.12a/7a+ exakt mit MP überein.

6. **[theCrag] theCrag (2023).** *Grade Conversion.*
   https://www.thecrag.com/en/article/grades
   → Größte internationale Plattform mit Community-validiertem Konverter.
   Nutzt eigenes numerisches Scoring-System (ähnlich IRCRA).

**Sekundärquellen (Validierung & Kontext):**

7. **[Hörst] Hörst, E (2016).** *Training for Climbing*, 3rd ed.
   Table 4.2: MVC/BW → UIAA-Grade.
   → Direkte Verbindung zu strength_analyzer. Verwendet UIAA als Standard.

8. **[Wikipedia] Wikipedia (2025).** *Grade (climbing) — Comparison tables.*
   https://en.wikipedia.org/wiki/Grade_(climbing)
   Quellen: Rockfax (2021), theCrag (2023), CAI/UIAA (2016).
   → Gut dokumentierte Synthese mit expliziten Fußnoten pro Zelle.

9. **[Alpinist] Alpinist Magazine.** *International Grade Comparison Chart.*
   Archiviert: https://web.archive.org/web/20210330142513/http://www.alpinist.com/p//climbing_notes/grades
   → US-Referenz, enthält auch Eis/Mixed/Alpin-Grade.

10. **[pyclimb] pyclimb v0.2.0** (MIT, 2022). Python-Paket von ilias-ant.
    https://github.com/ilias-ant/pyclimb
    → Nur French↔YDS, als Regressionstest verwendbar.

#### Diskrepanzen zwischen Quellen

Grad-Konvertierungen sind **nicht bijektiv und nicht eindeutig**.
Die Quellen weichen systematisch voneinander ab — besonders im Bereich V–VIII (UIAA).
Ab ca. VIII+ / 7a+ / 5.12a konvergieren die Systeme, weil Sport-Klettern
international dominiert und Routen in allen Systemen gleichzeitig bewertet werden
(Wikipedia [CAI]: "above the level of circa 5.12a, most grades closely align").

**Bekannte Diskrepanzen (Route):**

| Bereich | Quelle A | Quelle B | Abweichung |
|---------|----------|----------|------------|
| 5.11c | MP: 6c+ | Rockfax/CAI: 7a | ±½ Grad French |
| UIAA VII | MP: 6b+ | Wikipedia/CAI: 6b | +/- Suffix |
| UIAA VIII- | MP: 6c | CAI: 6c/6c+ | Zwischenstufe |
| 5.9+ | MP: 5c | Rockfax: 5c | Einig — aber UIAA VI vs VI+ je nach Quelle |
| 5.10d | MP: 6b+ | pyclimb: 6b+ | ✅ Einig |

**Bekannte Diskrepanzen (Boulder):**

| Bereich | Quelle A | Quelle B | Abweichung |
|---------|----------|----------|------------|
| V0 | MP: Font 4 | CAI: Font 4 | ✅ Einig |
| V7 | MP: 7A+ | Rockfax: 7A+ | ✅ Einig |
| V8 | MP: 7B | Einige: 7B/7B+ | ± Unschärfe |

→ Ab V9/7C sind alle Quellen exakt identisch (Draper 2015, Wikipedia [CAI]).

**Unsere Strategie für Diskrepanzen:**

1. **Primär: CAI/UIAA (Mandelli 2016)** — akademisch, institutionell, peer-reviewed-nah.
2. **Sekundär: Mountain Project** — größtes N, Community-Konsens.
3. **Validierung: Rockfax + theCrag** — europäischer Konsens.
4. **Bei Widerspruch:** CAI-Tabelle gewinnt. Abweichung wird als Kommentar
   im Code dokumentiert (z.B. `# MP: 6c+, CAI: 7a — wir folgen CAI`).
5. **Test-Suite enthält explizite Diskrepanz-Tests** die dokumentieren,
   welcher Quelle wir folgen und warum.

#### IRCRA-Skala als numerischer Index

Draper et al. (2015) definierten die **IRCRA-Skala** (International Rock Climbing
Research Association) als einheitlichen numerischen Index für Forschungszwecke.
Diese Skala ist **exakt das, was wir als `difficulty_index` brauchen**:

- Monoton steigend
- Peer-reviewed und in >50 Studien seitdem verwendet
- Definiert für alle gängigen Systeme (UIAA, French, YDS, Font, V-Scale)
- Ermöglicht statistische Analysen (Mittelwerte, Regressionen)

**Auszug IRCRA-Werte (Draper 2015, Table 1):**

```
IRCRA  UIAA    French   YDS      Font    V-Scale
 1     I       1        5.2      -       -
 4     III     3        5.4      -       -
 7     IV+     4b       5.5      -       -
10     V+      5a       5.7      -       -
13     VI+     6a       5.10a    -       -
15     VII+    6b+      5.10d    4       V0
17     VIII    7a       5.11d    5+      V2
19     VIII+   7a+      5.12a    6A+     V3+
20     IX-     7b+      5.12c    6B+     V4+
21     IX      7c       5.12d    6C+     V5+
22     IX+     7c+      5.13a    7A      V6
23     X-      8a       5.13b    7A+     V7
24     X       8a+      5.13c    7B      V8
25     X+      8b       5.13d    7B+     V8+
26     XI-     8b+      5.14a    7C      V9
27     XI      8c       5.14b    7C+     V10
28     XI+     8c+      5.14c    8A      V11
29     XII-    9a       5.14d    8A+     V12
30     XII     9a+      5.15a    8B      V13
31     XII+    9b       5.15b    8B+     V14
32     -       9b+      5.15c    8C      V15
33     -       9c       5.15d    8C+     V16
```

**Implementierungsentscheidung:** Wir verwenden die IRCRA-Skala als Basis für
unseren `difficulty_index`. Abweichungen von IRCRA werden dokumentiert.
Vorteil: Wir können in Publikationen schreiben
"difficulty index nach Draper et al. (2015)" statt "selbstgebaut".

#### Alternative Konvertierungsansätze

Neben Lookup-Tabellen gibt es in der Literatur auch **berechnete** Ansätze:

1. **IRCRA lineare Interpolation (Draper 2015).**
   Die IRCRA-Werte sind so konstruiert, dass zwischen benachbarten Graden
   linear interpoliert werden kann. Das nutzen wir für `from_index()`.

2. **theCrag Score-System.**
   theCrag verwendet ein eigenes numerisches Scoring (0–100+) mit
   datengetriebener Kalibrierung aus Millionen von Logbook-Einträgen.
   Nicht öffentlich dokumentiert, aber als Validierung interessant.

3. **Statistische Ansätze (Community-Daten).**
   Pollitt (2017, 8a.nu-Analyse) und r/climbharder-Surveys zeigen,
   dass die *tatsächliche* Schwierigkeit von der *nominellen* Grade
   abweichen kann (regionale Softgrading-Effekte, z.B. Frankreich
   vs. Deutschland). Für unsere Bibliothek irrelevant — wir konvertieren
   *nominelle* Grade, nicht *gefühlte*.

4. **Exponentieller Fit (nicht empfohlen).**
   Manche Quellen (z.B. climbharder-Wiki) versuchen einen exponentiellen
   Fit über alle Systeme. Das funktioniert schlecht, weil die Systeme
   unterschiedliche historische Ursprünge haben und nicht mathematisch
   konstruiert wurden. Wir verwenden explizite Tabellen.

#### Designentscheidungen

1. **UIAA als interner Standard.** Alle Konvertierungen laufen über UIAA als
   Drehscheibe (Hub-and-Spoke). Grund: UIAA ist das offizielle internationale
   System und wird in der deutschsprachigen Literatur durchgängig verwendet.
   Hörst (2016) und Lattice verwenden ebenfalls UIAA-basierte Tabellen.

2. **Numerischer Schwierigkeitsindex (difficulty_index).** Jeder Grad bekommt
   einen monoton steigenden Float-Wert (z.B. UIAA "7-" → 13.0, "7" → 14.0,
   "7+" → 15.0). Dieser Index ermöglicht:
   - Interpolation in strength_analyzer (MVC/BW → Grad)
   - Sortierung und Vergleich von Graden
   - Arithmetik (Durchschnitt, Differenz)
   - Mapping zwischen Systemen via gemeinsamen Index

3. **Zwei getrennte Domänen: Route und Boulder.**
   Route-Grade (UIAA, French, YDS) und Boulder-Grade (Font, V-Scale) sind
   **nicht direkt vergleichbar** (Wikipedia: "Font 4 / V0 entspricht etwa
   French 6a / UIAA VI+ / YDS 5.10a als Einzelzug").
   → Separate Tabellen, separate Enums, kein implizites Cross-Domain-Mapping.

4. **Keine unscharfen Zwischengrade.** Mountain Project listet Zwischenstufen
   wie "5.10a/b" oder "V3-4". Wir speichern nur kanonische Grade
   (5.10a, 5.10b, ...) und bieten `nearest()` für Approximation.

5. **Case-insensitive Input, kanonischer Output.**
   `convert("6A+", "french", "yds")` funktioniert, Ausgabe ist immer
   in kanonischer Schreibweise ("6a+").

#### Unterstützte Gradsysteme

**Route (Sport/Trad):**

| System | Enum-Name | Bereich | Beispiele | Verbreitung |
|--------|-----------|---------|-----------|-------------|
| UIAA | `UIAA` | I – XII+ | "7-", "7", "7+", "8-" | DACH, Osteuropa |
| French Sport | `FRENCH` | 1a – 9c | "6a+", "7b", "8c+" | Europa, weltweit |
| Yosemite Decimal | `YDS` | 5.0 – 5.15d | "5.10a", "5.12c" | Nordamerika |

**Boulder:**

| System | Enum-Name | Bereich | Beispiele | Verbreitung |
|--------|-----------|---------|-----------|-------------|
| Fontainebleau | `FONT` | 3 – 9A | "6A+", "7C+", "8B" | Europa, weltweit |
| V-Scale (Hueco) | `V_SCALE` | V0 – V17 | "V5", "V10", "V14" | Nordamerika |

**Nicht in v1 (aber vorbereitet):** Ewbanks (AUS/NZ), British E-Grade, Südafrika.

#### Konvertierungstabelle — Route

Primärquelle: CAI/Mandelli (2016), kreuzvalidiert mit Mountain Project (2024),
Rockfax (2022) und Wikipedia/theCrag (2023). IRCRA-Index nach Draper (2015).
Bei Diskrepanzen: CAI-Wert, Abweichung als Kommentar.

```python
ROUTE_TABLE = [
    # (ircra, uiaa,    french,  yds)          # Quelle / Anmerkung
    (1,   "I",     "1",     "5.2"),           # CAI, FoH
    (2,   "II",    "2",     "5.3"),           # CAI, FoH
    (3,   "III",   "3",     "5.4"),           # CAI, FoH
    (4,   "III+",  "3+",    "5.4"),           # CAI
    (5,   "IV",    "4a",    "5.5"),           # CAI, Draper2015 (IRCRA ~5–7)
    (6,   "IV+",   "4b",    "5.6"),           # CAI
    (7,   "V-",    "4b",    "5.6"),           # CAI — V- = IV+/V Übergang
    (8,   "V",     "4c",    "5.7"),           # CAI, MP, Rockfax einig
    (9,   "V+",    "5a",    "5.7+"),          # CAI, Draper2015 (IRCRA ~10)
    (10,  "VI-",   "5b",    "5.8"),           # CAI, MP einig
    (11,  "VI",    "5c",    "5.9"),           # CAI, MP, Rockfax einig
    (12,  "VI+",   "6a",    "5.10a"),         # CAI, MP, Rockfax einig. Draper2015 IRCRA=13
    (13,  "VII-",  "6a+",   "5.10b"),         # CAI: 6a+. MP: 6a+. Einig.
    (14,  "VII",   "6b",    "5.10c"),         # CAI, MP einig. Draper2015 IRCRA≈14–15
    (15,  "VII+",  "6b+",   "5.10d"),         # CAI, MP einig
    (16,  "VIII-", "6c",    "5.11a"),         # CAI: 6c. MP: 6c. Einig.
    (17,  "VIII-", "6c+",   "5.11b"),         # CAI: VIII-/6c+. MP: 6c+/5.11b/c
    (18,  "VIII",  "7a",    "5.11d"),         # CAI, MP, Rockfax, Draper einig. IRCRA=17
    (19,  "VIII+", "7a+",   "5.12a"),         # Alle Quellen einig. IRCRA=19. Konvergenzpunkt!
    (20,  "IX-",   "7b",    "5.12b"),         # CAI, MP einig
    (21,  "IX-",   "7b+",   "5.12c"),         # CAI, MP einig. IRCRA=20–21
    (22,  "IX",    "7c",    "5.12d"),         # CAI, MP, Rockfax einig
    (23,  "IX+",   "7c+",   "5.13a"),         # Alle einig. IRCRA=22
    (24,  "X-",    "8a",    "5.13b"),         # Alle einig. IRCRA=23
    (25,  "X-",    "8a+",   "5.13c"),         # Alle einig
    (26,  "X",     "8b",    "5.13d"),         # Alle einig. IRCRA=25
    (27,  "X+",    "8b+",   "5.14a"),         # Alle einig. IRCRA=26
    (28,  "XI-",   "8c",    "5.14b"),         # Alle einig. IRCRA=27
    (29,  "XI-",   "8c+",   "5.14c"),         # Alle einig
    (30,  "XI",    "9a",    "5.14d"),         # Alle einig. IRCRA=29. Action Directe!
    (31,  "XI+",   "9a+",   "5.15a"),         # Alle einig. IRCRA=30
    (32,  "XII-",  "9b",    "5.15b"),         # Alle einig. IRCRA=31
    (33,  "XII",   "9b+",   "5.15c"),         # Alle einig
    (34,  "XII+",  "9c",    "5.15d"),         # Alle einig. IRCRA≈33. Silence!
]
```

#### Konvertierungstabelle — Boulder

Primärquelle: CAI/Mandelli (2016), kreuzvalidiert mit Rockfax (2022),
Mountain Project (2024). IRCRA-Index nach Draper (2015).
Ab V9/7C: alle Quellen exakt identisch.

```python
BOULDER_TABLE = [
    # (ircra, font,    v_scale)               # Quelle / Anmerkung
    (11,  "3",     "VB"),                     # Draper2015 IRCRA≈10–12
    (12,  "4-",    "V0-"),                    # MP
    (13,  "4",     "V0"),                     # CAI, MP, Rockfax einig
    (14,  "4+",    "V0+"),                    # MP, Rockfax
    (15,  "5",     "V1"),                     # CAI, Draper2015 IRCRA≈15
    (16,  "5+",    "V2"),                     # CAI, MP einig
    (17,  "6A",    "V3"),                     # CAI, MP, Rockfax einig. IRCRA≈17
    (18,  "6A+",   "V3+"),                    # MP
    (19,  "6B",    "V4"),                     # CAI, MP einig. IRCRA≈19
    (20,  "6B+",   "V4+"),                    # MP
    (21,  "6C",    "V5"),                     # CAI, MP einig. IRCRA≈21
    (22,  "6C+",   "V5+"),                    # MP
    (23,  "7A",    "V6"),                     # Alle einig. IRCRA=22
    (24,  "7A+",   "V7"),                     # Alle einig. IRCRA=23
    (25,  "7B",    "V8"),                     # Alle einig. IRCRA=24
    (26,  "7B+",   "V8+"),                    # Alle einig
    (27,  "7C",    "V9"),                     # Alle einig. IRCRA=26. Ab hier exakt!
    (28,  "7C+",   "V10"),                    # Alle einig. IRCRA=27
    (29,  "8A",    "V11"),                    # Alle einig. IRCRA=28
    (30,  "8A+",   "V12"),                    # Alle einig. IRCRA=29
    (31,  "8B",    "V13"),                    # Alle einig. IRCRA=30
    (32,  "8B+",   "V14"),                    # Alle einig. IRCRA=31
    (33,  "8C",    "V15"),                    # Alle einig. IRCRA=32
    (34,  "8C+",   "V16"),                    # Alle einig. IRCRA=33
    (35,  "9A",    "V17"),                    # Alle einig. Burden of Dreams!
]
```

#### Datentypen

```python
import enum
from dataclasses import dataclass


class RouteSystem(enum.Enum):
    UIAA = "UIAA"
    FRENCH = "French"
    YDS = "YDS"


class BoulderSystem(enum.Enum):
    FONT = "Font"
    V_SCALE = "V-Scale"


@dataclass(frozen=True)
class Grade:
    """Immutable Grad-Objekt mit System, Wert und numerischem Index."""
    system: RouteSystem | BoulderSystem
    value: str              # Kanonischer String, z.B. "7a+", "V5", "VIII-"
    difficulty_index: float # Monoton steigender Schwierigkeitswert

    def __lt__(self, other: "Grade") -> bool:
        return self.difficulty_index < other.difficulty_index

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Grade):
            return NotImplemented
        return self.system == other.system and self.value == other.value

    def __hash__(self) -> int:
        return hash((self.system, self.value))

    def __str__(self) -> str:
        return self.value
```

#### Funktionen

```python
def convert(grade: str, from_system: str, to_system: str) -> str:
    """Konvertiert einen Klettergrad zwischen Systemen.

    Args:
        grade: Grad-String, z.B. "7a+", "5.12a", "VIII-", "V5", "7A+"
        from_system: Quellsystem ("UIAA", "French", "YDS", "Font", "V-Scale")
        to_system: Zielsystem (gleiche Werte)

    Returns:
        Konvertierter Grad als String in kanonischer Schreibweise.

    Raises:
        GradeError: Unbekanntes System oder Grad nicht im System enthalten.
        GradeDomainError: Route↔Boulder-Konvertierung versucht
            (z.B. French→Font ist ungültig).

    Example:
        >>> convert("7a+", "French", "YDS")
        '5.12a'
        >>> convert("5.12a", "YDS", "UIAA")
        'VIII+'
        >>> convert("V5", "V-Scale", "Font")
        '6C'

    References:
        Mountain Project (2024), UIAA Scale of Difficulty
    """


def parse(grade: str, system: str | None = None) -> Grade:
    """Parst einen Grad-String zu einem Grade-Objekt.

    Wenn system=None, wird das System automatisch erkannt:
    - Beginnt mit "V" + Zahl → V-Scale
    - Beginnt mit "5." → YDS
    - Enthält römische Ziffern (I–XII) mit +/- → UIAA
    - Uppercase A/B/C (6A, 7B+) → Font
    - Lowercase a/b/c (6a, 7b+) → French

    Args:
        grade: Grad-String
        system: Optional — erzwingt System statt Autodetect

    Returns:
        Grade-Objekt mit system, value, difficulty_index

    Example:
        >>> parse("7a+")
        Grade(system=<RouteSystem.FRENCH>, value='7a+', difficulty_index=15.5)
        >>> parse("V5")
        Grade(system=<BoulderSystem.V_SCALE>, value='V5', difficulty_index=8.0)
    """


def difficulty_index(grade: str, system: str | None = None) -> float:
    """Gibt den numerischen Schwierigkeitsindex eines Grades zurück.

    Nützlich für Berechnungen in strength_analyzer:
    - Interpolation (MVC/BW-Ratio → Index → Grad)
    - Sortierung und Vergleich
    - Durchschnittsbildung

    Example:
        >>> difficulty_index("7a+", "French")
        15.5
        >>> difficulty_index("VIII+", "UIAA")
        15.5
    """


def from_index(index: float, system: str) -> str:
    """Inverse: Numerischer Index → nächstliegender Grad im System.

    Rundet zum nächsten tabellierten Grad (nearest-neighbor).

    Example:
        >>> from_index(15.3, "French")
        '7a'
        >>> from_index(15.7, "UIAA")
        'VIII+'
    """


def all_grades(system: str) -> list[Grade]:
    """Gibt alle Grade eines Systems aufsteigend sortiert zurück.

    Example:
        >>> [g.value for g in all_grades("UIAA")][:5]
        ['I', 'II', 'III', 'IV', 'IV+']
    """
```

#### Exceptions

```python
class GradeError(Exception):
    """Basisklasse für Grad-Fehler."""

class UnknownSystemError(GradeError):
    """Unbekanntes Gradsystem angegeben."""

class UnknownGradeError(GradeError):
    """Grad existiert nicht im angegebenen System."""

class GradeDomainError(GradeError):
    """Konvertierung zwischen Route und Boulder versucht."""
```

#### Tests (`test_grades.py`)

```python
# ============================================================
# ABSCHNITT 1: Konvertierung Route — Quellen-validiert
# ============================================================

# French → YDS (Referenz: CAI/Mandelli 2016, bestätigt durch MP 2024)
assert convert("6a",  "French", "YDS") == "5.10a"   # CAI, MP, Rockfax einig
assert convert("6a+", "French", "YDS") == "5.10b"   # CAI, MP, Rockfax einig
assert convert("7a",  "French", "YDS") == "5.11d"   # CAI, MP, Rockfax einig
assert convert("7a+", "French", "YDS") == "5.12a"   # Alle einig. Konvergenzpunkt.
assert convert("8a",  "French", "YDS") == "5.13b"   # Alle einig
assert convert("9a",  "French", "YDS") == "5.14d"   # Alle einig

# YDS → French (Referenz: CAI 2016, MP 2024)
assert convert("5.10a", "YDS", "French") == "6a"
assert convert("5.10d", "YDS", "French") == "6b+"
assert convert("5.12a", "YDS", "French") == "7a+"   # Konvergenzpunkt
assert convert("5.14a", "YDS", "French") == "8b+"

# French → UIAA (Referenz: CAI 2016 — dies ist die offizielle UIAA-Quelle)
assert convert("6a",  "French", "UIAA") == "VI+"
assert convert("6b+", "French", "UIAA") == "VII+"
assert convert("7a",  "French", "UIAA") == "VIII"
assert convert("7a+", "French", "UIAA") == "VIII+"
assert convert("8a",  "French", "UIAA") == "X-"     # CAI: X-. Manche: IX+.
assert convert("9a",  "French", "UIAA") == "XI"
assert convert("9c",  "French", "UIAA") == "XII+"   # Silence!

# YDS → UIAA (abgeleitet über French als Hub)
assert convert("5.10a", "YDS", "UIAA") == "VI+"
assert convert("5.12a", "YDS", "UIAA") == "VIII+"
assert convert("5.14d", "YDS", "UIAA") == "XI"      # Action Directe

# UIAA → French (Referenz: CAI 2016)
assert convert("VI+",  "UIAA", "French") == "6a"
assert convert("VII+", "UIAA", "French") == "6b+"
assert convert("VIII", "UIAA", "French") == "7a"
assert convert("IX",   "UIAA", "French") == "7c"
assert convert("X",    "UIAA", "French") == "8b"

# ============================================================
# ABSCHNITT 2: Konvertierung Boulder — Quellen-validiert
# ============================================================

# Font → V-Scale (Referenz: CAI 2016, Rockfax 2022, MP 2024)
assert convert("6A",  "Font", "V-Scale") == "V3"
assert convert("7A",  "Font", "V-Scale") == "V6"
assert convert("7C",  "Font", "V-Scale") == "V9"    # Ab hier alle exakt einig
assert convert("7C+", "Font", "V-Scale") == "V10"
assert convert("8A",  "Font", "V-Scale") == "V11"
assert convert("8C",  "Font", "V-Scale") == "V15"

# V-Scale → Font (Referenz: alle Quellen)
assert convert("V5",  "V-Scale", "Font") == "6C"
assert convert("V9",  "V-Scale", "Font") == "7C"
assert convert("V10", "V-Scale", "Font") == "7C+"
assert convert("V14", "V-Scale", "Font") == "8B+"

# ============================================================
# ABSCHNITT 3: Round-Trip-Tests
# ============================================================

# convert(convert(g, A, B), B, A) == g
# Gilt exakt nur wenn die Zuordnung in der Tabelle 1:1 ist.
# Ab VIII+ / 7a+ / 5.12a ist das gegeben (alle Quellen konvergieren).
for grade in ["7a+", "8a", "8b", "8c", "9a", "9b", "9c"]:
    assert convert(convert(grade, "French", "YDS"), "YDS", "French") == grade
    assert convert(convert(grade, "French", "UIAA"), "UIAA", "French") == grade

for grade in ["V6", "V7", "V8", "V9", "V10", "V11", "V14", "V17"]:
    assert convert(convert(grade, "V-Scale", "Font"), "Font", "V-Scale") == grade

# ============================================================
# ABSCHNITT 4: Domain-Trennung
# ============================================================

# Route → Boulder muss GradeDomainError werfen
with pytest.raises(GradeDomainError):
    convert("7a", "French", "Font")      # Sport → Boulder verboten

with pytest.raises(GradeDomainError):
    convert("V5", "V-Scale", "YDS")      # Boulder → Sport verboten

with pytest.raises(GradeDomainError):
    convert("VIII", "UIAA", "V-Scale")   # Route → Boulder verboten

# ============================================================
# ABSCHNITT 5: IRCRA-Index (Draper et al. 2015)
# ============================================================

# Monoton steigend innerhalb jedes Systems
for system in ["UIAA", "French", "YDS", "Font", "V-Scale"]:
    grades = all_grades(system)
    for i in range(len(grades) - 1):
        assert grades[i].difficulty_index < grades[i+1].difficulty_index, \
            f"{system}: {grades[i]} >= {grades[i+1]}"

# Gleicher IRCRA-Index über Route-Systeme
# (Kernaussage von Draper 2015: der Index ist system-übergreifend)
assert difficulty_index("7a+", "French") == difficulty_index("5.12a", "YDS")
assert difficulty_index("7a+", "French") == difficulty_index("VIII+", "UIAA")
assert difficulty_index("9a",  "French") == difficulty_index("5.14d", "YDS")
assert difficulty_index("9a",  "French") == difficulty_index("XI", "UIAA")

# Gleicher IRCRA-Index über Boulder-Systeme
assert difficulty_index("7A",  "Font") == difficulty_index("V6", "V-Scale")
assert difficulty_index("8A",  "Font") == difficulty_index("V11", "V-Scale")
assert difficulty_index("9A",  "Font") == difficulty_index("V17", "V-Scale")

# IRCRA-Werte gegen Draper (2015) Table 1 prüfen
assert difficulty_index("VIII", "UIAA") == 18     # Draper: IRCRA=17–18
assert difficulty_index("VIII+","UIAA") == 19     # Draper: IRCRA=19
assert difficulty_index("XI",  "UIAA") == 30      # Draper: IRCRA=29–30

# ============================================================
# ABSCHNITT 6: from_index (Inverse)
# ============================================================

# Exakte Treffer
assert from_index(19, "French") == "7a+"
assert from_index(19, "YDS") == "5.12a"
assert from_index(19, "UIAA") == "VIII+"

# Interpolation: Index zwischen zwei Graden → nearest
assert from_index(18.4, "French") == "7a"    # näher an 18
assert from_index(18.6, "French") == "7a+"   # näher an 19
assert from_index(29.6, "UIAA") == "XI"      # näher an 30
assert from_index(30.4, "UIAA") == "XI"      # noch bei 30

# ============================================================
# ABSCHNITT 7: Autodetect (parse ohne System-Angabe)
# ============================================================

assert parse("V5").system == BoulderSystem.V_SCALE
assert parse("VB").system == BoulderSystem.V_SCALE
assert parse("5.12a").system == RouteSystem.YDS
assert parse("5.9").system == RouteSystem.YDS
assert parse("VIII+").system == RouteSystem.UIAA
assert parse("XII-").system == RouteSystem.UIAA
assert parse("7a+").system == RouteSystem.FRENCH    # Kleinbuchstabe → French
assert parse("7A+").system == BoulderSystem.FONT    # Großbuchstabe → Font

# ============================================================
# ABSCHNITT 8: Case-insensitive Input
# ============================================================

assert convert("7A+", "French", "YDS") == convert("7a+", "French", "YDS")
assert convert("viii+", "UIAA", "French") == convert("VIII+", "UIAA", "French")
assert convert("v5", "V-Scale", "Font") == convert("V5", "V-Scale", "Font")

# ============================================================
# ABSCHNITT 9: Error Handling
# ============================================================

with pytest.raises(UnknownGradeError):
    convert("13a", "French", "YDS")          # Existiert nicht
with pytest.raises(UnknownGradeError):
    convert("V99", "V-Scale", "Font")        # Existiert nicht
with pytest.raises(UnknownSystemError):
    convert("7a", "Ewbanks", "YDS")          # v1 nicht unterstützt
with pytest.raises(UnknownSystemError):
    convert("7a", "French", "Saxon")         # v1 nicht unterstützt

# Identitäts-Konvertierung (gleiches System)
assert convert("7a+", "French", "French") == "7a+"
assert convert("V5", "V-Scale", "V-Scale") == "V5"
assert convert("VIII+", "UIAA", "UIAA") == "VIII+"

# ============================================================
# ABSCHNITT 10: Historische Referenzpunkte
# (Dient als "Sanity Check" — diese Fakten sind unstrittig)
# ============================================================

# Silence (Ondra 2017): 9c / 5.15d / XII+ — hardest free climb ever
assert convert("9c", "French", "YDS") == "5.15d"
assert convert("9c", "French", "UIAA") == "XII+"

# Action Directe (Güllich 1991): 9a / 5.14d / XI — first 9a
assert convert("9a", "French", "YDS") == "5.14d"
assert convert("9a", "French", "UIAA") == "XI"

# Hubble (Moon 1990): 8c+ / 5.14c — first 8c+
assert convert("8c+", "French", "YDS") == "5.14c"

# Punks in the Gym (1985): 8b+ / 5.14a — first 8b+ (Wikipedia)
assert convert("8b+", "French", "YDS") == "5.14a"

# Burden of Dreams (Nalle 2016): 9A / V17 — hardest boulder ever
assert convert("9A", "Font", "V-Scale") == "V17"

# Midnight Lightning (Kauk 1978): 7B / V8 — iconic boulder
assert convert("7B", "Font", "V-Scale") == "V8"

# ============================================================
# ABSCHNITT 11: Diskrepanz-Dokumentation
# Explizite Tests die dokumentieren, welcher Quelle wir folgen.
# Jeder Test enthält einen Kommentar mit den alternativen Werten.
# ============================================================

# 5.11c: MP sagt 6c+, CAI sagt 6c+/7a. Wir folgen CAI: 6c+
assert convert("5.11b", "YDS", "French") == "6c+"   # CAI: VIII-/6c+

# UIAA VIII- ↔ French: CAI sagt 6c, MP sagt 6c. Einig.
assert convert("VIII-", "UIAA", "French") == "6c"

# 8a ↔ UIAA: CAI sagt X-, manche ältere Quellen sagen IX+.
# Wir folgen CAI (2016).
assert convert("8a", "French", "UIAA") == "X-"      # CAI: X-

# ============================================================
# ABSCHNITT 12: Regression gegen pyclimb v0.2.0
# pyclimb hat nur French↔YDS. Wir prüfen alle 34 Einträge
# und dokumentieren Abweichungen.
# ============================================================

# pyclimb French→YDS Mapping (vollständig):
PYCLIMB_FRENCH_TO_YDS = {
    "5a": "5.8", "5b": "5.9", "5c": "5.10a",
    "6a": "5.10a", "6a+": "5.10b", "6b": "5.10c", "6b+": "5.10d",
    "6c": "5.11b", "6c+": "5.11c",
    "7a": "5.11d", "7a+": "5.12a", "7b": "5.12b", "7b+": "5.12c",
    "7c": "5.12d", "7c+": "5.13a",
    "8a": "5.13b", "8a+": "5.13c", "8b": "5.13d", "8b+": "5.14a",
    "8c": "5.14b", "8c+": "5.14c",
    "9a": "5.14d", "9a+": "5.15a", "9b": "5.15b", "9b+": "5.15c",
    "9c": "5.15d",
}

# Wir erwarten Übereinstimmung ab 7a+ (Konvergenzzone).
# Darunter kann es Abweichungen geben (dokumentiert):
KNOWN_DEVIATIONS = {
    # pyclimb: 5c→5.10a, wir: 5c→5.9 (CAI-Tabelle). ±1 Subgrade.
    "5c": ("5.10a", "5.9"),   # (pyclimb, wir)
    # pyclimb: 6c→5.11b, wir: 6c→5.11a (CAI). ±1 Subgrade.
    "6c": ("5.11b", "5.11a"),
}

for french, expected_yds in PYCLIMB_FRENCH_TO_YDS.items():
    our_result = convert(french, "French", "YDS")
    if french in KNOWN_DEVIATIONS:
        pyclimb_val, our_expected = KNOWN_DEVIATIONS[french]
        assert our_result == our_expected, \
            f"Abweichung bei {french}: erwartet {our_expected} (CAI), got {our_result}"
    else:
        assert our_result == expected_yds, \
            f"Regression vs pyclimb bei {french}: erwartet {expected_yds}, got {our_result}"
```

#### Implementierungshinweise

1. **Intern als Dict-of-Dicts.** Jede Tabelle wird beim Import in
   schnelle Lookup-Dictionaries überführt:
   `_ROUTE_BY_FRENCH["7a+"] → (15.0, "VIII", "7a", "5.11d")`

2. **Zero Dependencies.** Nur stdlib (enum, dataclasses). Kein numpy nötig.

3. **Erweiterbar.** Neue Systeme (Ewbanks, British E-Grade, Sächsisch)
   erfordern nur eine neue Spalte in der Tabelle + neuen Enum-Wert.
   Die Logik bleibt identisch.

4. **Validierung gegen pyclimb.** Alle French↔YDS-Werte aus pyclimb v0.2.0
   als Regressionstest verwenden. Abweichungen dokumentieren und begründen.

5. **Kanonische Schreibweise.** Output ist immer exakt wie in der Tabelle:
   - UIAA: Römische Ziffern + optional "+"/"-" (z.B. "VII+", "IX-")
   - French: Arabisch + Kleinbuchstabe + optional "+" (z.B. "7a+")
   - YDS: "5." + Zahl, ab 5.10 mit Kleinbuchstabe (z.B. "5.10a")
   - Font: Arabisch + Großbuchstabe + optional "+" (z.B. "7A+")
   - V-Scale: "V" + Zahl (z.B. "V5"), Sonderfall "VB" (= V-easy)

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

## Module — Layer 3: I/O Adapters

### Modul 7: `adapters/tindeq.py` — Tindeq Progressor Adapter

**Priorität:** 🟡 Primärer Adapter (für FingerForceTraining iOS-App)

**Schicht:** Adapter — liest Tindeq-spezifisches JSON, erzeugt kanonische ForceSession

**Abhängigkeiten:** Nur `datamodel.py`

```python
def load(path: str) -> ForceSession:
    """Lädt FingerForceTraining JSON → kanonische ForceSession.

    Handles:
    - UInt64 Timestamps (neue Sessions) und UInt32 (legacy)
    - Segments (optional, wenn vorhanden)
    - Metadata-Mapping: testType, holdType, hand → metadata dict
    """

def load_all(directory: str) -> list[ForceSession]:
    """Lädt alle Sessions aus einem Verzeichnis (iCloud-Export)."""
```

### Modul 8: `adapters/manual.py` — Manuelle Eingabe

**Priorität:** 🟡 Für Nutzer ohne Kraftmessgerät

```python
def from_mvc7_test(bodyweight_kg: float, added_kg: float,
                   hang_time_s: float = 7.0,
                   edge_mm: float = 20) -> TestResult:
    """Erzeugt TestResult aus manueller MVC-7 Messung (Stoppuhr + Gewicht)."""

def from_repeater_test(bodyweight_kg: float,
                       mvc7_kg: float,
                       t80_s: float, t60_s: float,
                       t_low_s: float, low_pct: float = 0.45) -> TestResult:
    """Erzeugt TestResult aus manuellem CF-Test (3-Punkt)."""
```

### Modul 9: `adapters/csv_generic.py` — Generischer CSV-Import

```python
def load(path: str, time_col: str = "time_s",
         force_col: str = "force_kg",
         delimiter: str = ",") -> ForceSession:
    """Lädt beliebige CSV mit Zeit/Kraft-Spalten."""
```

---

## Module — Layer 4: Frontends

### Modul 10: `frontends/report.py` — Assessment-Report

**Priorität:** 🟢 End-to-End-Ergebnis

**Schicht:** Frontend — orchestriert Adapter → Models → Output

```python
def generate(session: ForceSession, profile: AthleteProfile,
             edge_mm: float = 20) -> AssessmentReport:
    """Vollständiger Assessment-Report aus Session + Profil.

    Pipeline:
    1. signal.best_n_second_average → MVC-7
    2. strength_analyzer.predict_grade → Grad
    3. hangboard_calc → Trainingsempfehlungen
    4. Optional: critical_force → Endurance
    """

def to_markdown(report: AssessmentReport) -> str:
    """Rendert Report als Markdown (für Jupyter, CLI, Export)."""

def to_dict(report: AssessmentReport) -> dict:
    """Report als dict (für JSON-Export, Web-API)."""
```

### Modul 11: `frontends/notebook.py` — Jupyter Helpers

**Priorität:** 🟢 Nice-to-have, hoher Wow-Faktor

**Abhängigkeiten:** matplotlib (optional), pandas (optional)

```python
def plot_session(session: ForceSession, **kwargs) -> None:
    """Force-Time-Kurve mit automatischer Peak-Markierung."""

def plot_rohmert_curve(models: list[str] | None = None) -> None:
    """Rohmert Fatigue-Kurven für alle Modelle überlagert."""

def plot_protocol_comparison(mvc7_kg: float, bodyweight_kg: float) -> None:
    """Balkendiagramm: Alle Protokolle im Vergleich (TUT, Last, Volumen)."""

def session_to_dataframe(session: ForceSession):
    """Konvertiert ForceSession → pandas DataFrame (für eigene Analyse)."""
```

### Modul 12: `frontends/cli.py` — CLI Runner

**Priorität:** 🟢 Optional

```bash
# Beispiel-Aufrufe:
$ climbing-science analyze --mvc7 105 --bw 65 --edge 20
$ climbing-science plan --mvc7 105 --bw 65 --protocol lopez_maxhangs
$ climbing-science report session.json --bw 65
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

DATENMODELL (datamodel.py — die Brücke)
    ForceSample, ForceSession, AthleteProfile, TestResult

Layer 2 — EXERCISES (Protokoll-Daten + Berechnung)
┌──────────────┐    ┌────────────────────────────┐
│ protocols    │───▶│ hangboard_calc             │
│ (pure data)  │    │ (protocols + rohmert + edge)│
└──────────────┘    └────────────────────────────┘

Layer 3 — ADAPTERS (Format → Datenmodell)
┌──────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────┐
│ tindeq   │ │ climbro │ │ manual  │ │ csv_generic │
└──────────┘ └─────────┘ └─────────┘ └─────────────┘

Layer 4 — FRONTENDS (Anwendungen)
┌──────────┐  ┌──────────┐  ┌──────────┐
│ cli      │  │ report   │  │ notebook │
└──────────┘  └──────────┘  └──────────┘
```

## Implementierungsreihenfolge

**Layer 0 (Fundament):**

0. **`datamodel.py`** — Kanonische Datentypen, alles baut darauf auf

**Layer 1 (bottom-up):**

1. **`models/grades.py`** — Lookup-Tabellen, kein Mathe, schneller Win
2. **`models/rohmert.py`** — Mathematisches Fundament, gut testbar
3. **`models/edge_depth.py`** — Einfach, braucht Rohmert nicht direkt
4. **`models/signal.py`** — Smoothing, Peak Detection, RFD (pure math)
5. **`models/strength_analyzer.py`** — Nutzt Rohmert + Edge + Grades, erstes "Wow"
6. **`models/critical_force.py`** — Eigenständiges Modell, lineare Regression

**Layer 2:**

7. **`exercises/protocols.py`** — Reine Datenklassen, sofort testbar
8. **`exercises/hangboard_calc.py`** — Verbindet Protokolle mit Models

**Layer 3:**

9. **`adapters/tindeq.py`** — JSON-Parsing für FingerForceTraining
10. **`adapters/manual.py`** — Manuelle Eingabe für Nutzer ohne Gerät
11. **`adapters/csv_generic.py`** — Generischer Import

**Layer 4 + Notebooks:**

12. **`frontends/report.py`** — End-to-End Assessment
13. **`frontends/notebook.py`** — Jupyter Helpers (Plots, DataFrame)
14. **`frontends/cli.py`** — Interaktives CLI
15. **Example Notebooks** — Auslieferbare Auswertungen (siehe unten)

---

## Example Notebooks — Interaktive Auswertungen mit Referenzen

Die Notebooks sind das **Hauptprodukt** für Endnutzer. Sie kombinieren:
- Echte Berechnungen mit der Library
- Erklärende Markdown-Zellen mit wissenschaftlichen Referenzen
- Interaktive Plots
- Sofort ausführbar mit eigenen Daten (nur Zahlen oben ändern)

### Dateistruktur

```
notebooks/
├── 01_my_climbing_assessment.ipynb    # Persönliche Gesamtauswertung
├── 02_rohmert_curve_explained.ipynb   # Theorie: Isometrische Fatigue
├── 03_critical_force_analysis.ipynb   # CF-Test auswerten + verstehen
├── 04_protocol_comparison.ipynb       # Welches Protokoll passt zu mir?
├── 05_session_deep_dive.ipynb         # Tindeq-Session analysieren
├── 06_progress_tracker.ipynb          # Fortschritt über Wochen/Monate
└── 07_edge_depth_science.ipynb        # Warum 20mm? Edge-Depth-Korrektur
```

### Notebook 1: `01_my_climbing_assessment.ipynb`

**Titel:** *"Wie stark bin ich wirklich? — Persönliches Climbing Assessment"*

**Zielgruppe:** Jeder Kletterer, der seine Stärken und Schwächen kennenlernen will

```markdown
# 🧗 Mein persönliches Climbing Assessment

## Eingabe — Deine Daten
*(Nur diese Zelle anpassen, dann alle Zellen ausführen)*
```

```python
# === DEINE DATEN ===
BODYWEIGHT_KG = 72
HEIGHT_CM = 178
MVC7_KG = 105          # Gesamtlast (BW + Zusatzgewicht), 7s Hang, 20mm Edge
TEST_EDGE_MM = 20
TRAINING_MODE = 3      # 1=kein HB, 2=Repeaters, 3=MaxHangs, 4=MaxHangs+added

# Optional: Endurance-Daten (für CF-Analyse)
T80_S = 77             # Kumulative Hangzeit bei 80% MVC (7/3 Repeaters)
T60_S = 136            # bei 60% MVC
T45_S = 323            # bei 45% MVC
```

```markdown
## 1. Fingerkraft-Analyse

Dein MVC-7 (Maximum Voluntary Contraction über 7 Sekunden) ist der
wichtigste Einzelindikator für Kletterleistung. Er korreliert stärker
mit dem Klettergrad als jeder andere messbare Parameter
*(Hörst 2016, S. 47; Giles et al. 2019)*.
```

```python
from climbing_science.models import strength_analyzer, grades

result = strength_analyzer.predict_grade(
    mvc7_kg=MVC7_KG, bodyweight_kg=BODYWEIGHT_KG,
    edge_mm=TEST_EDGE_MM, training_mode=TRAINING_MODE
)

print(f"MVC/BW Ratio:       {result.mvc_bw_ratio:.1%}")
print(f"Predicted Boulder:  {result.boulder_uiaa} ({result.boulder_font} / {result.boulder_v})")
print(f"Einordnung:         {result.percentile}")
```

```markdown
### Was bedeutet dein MVC/BW-Ratio?

| Ratio | Einordnung | Boulder (UIAA) | Referenz |
|-------|------------|-----------------|----------|
| < 1.0 | Beginner   | ≤ 6+           | Hörst 2016, Tab. 4.2 |
| 1.0–1.3 | Intermediate | 7- bis 8-   | Lattice (n=436) |
| 1.3–1.6 | Advanced   | 8 bis 9-       | r/climbharder 2017 |
| > 1.6 | Elite      | ≥ 9            | Giles et al. 2019 |

> *"Finger strength explained 14% of variance in climbing performance,
>  while technique and mental factors accounted for 78%."*
> — Meta-Analyse basierend auf Hörst (2016), Lattice Data
```

```python
# Visualisierung: Wo stehst du?
from climbing_science.frontends import notebook
notebook.plot_strength_benchmark(
    mvc_bw_ratio=result.mvc_bw_ratio,
    highlight_grade=result.boulder_uiaa
)
```

```markdown
## 2. Ausdauer-Analyse (Critical Force)

Critical Force (CF) ist das Ausdauer-Äquivalent zum MVC-7.
CF beschreibt die Kraft, die du *theoretisch unendlich* lange halten kannst,
bevor die aerobe Kapazität erschöpft ist *(Monod & Scherrer 1965)*.

Für Kletterer misst man CF über intermittierende 7/3-Repeaters bei
verschiedenen Intensitäten *(Giles et al. 2019)*.
```

```python
from climbing_science.models import critical_force

cf = critical_force.calculate_cf(
    mvc7_kg=MVC7_KG, bodyweight_kg=BODYWEIGHT_KG,
    t80_s=T80_S, t60_s=T60_S, t_low_s=T45_S
)

print(f"Critical Force:     {cf.cf_kg:.1f} kg ({cf.cf_bw_ratio:.1%} BW)")
print(f"W' (Anaerob):       {cf.w_prime_kgs:.0f} kg·s")
print(f"CF/MVC Ratio:       {cf.cf_mvc_ratio:.1%}")
print(f"Predicted Sport:    {cf.predicted_sport_grade}")
print(f"Fit-Qualität (R²):  {cf.r_squared:.3f}")
```

```python
# CF-Regression visualisieren
notebook.plot_critical_force(cf, mvc7_kg=MVC7_KG, bodyweight_kg=BODYWEIGHT_KG)
```

```markdown
### CF/MVC Ratio — Kraft vs. Ausdauer Profil

| CF/MVC Ratio | Profil | Typisch für |
|-------------|--------|-------------|
| < 0.35 | Reiner Boulderer | Starke Finger, wenig Ausdauer |
| 0.35–0.45 | Balanced | Gute Basis für beides |
| > 0.45 | Endurance-dominant | Starke Ausdauer, rel. wenig Maximalkraft |

> *"The relationship between CF and sport climbing grade was r = 0.82."*
> — Giles D. et al. (2019), Int J Sports Physiol Perform
```

```markdown
## 3. Schwächen-Analyse & Trainingsempfehlung
```

```python
from climbing_science.exercises import hangboard_calc

# Wo ist der größte Hebel?
weaknesses = []
if result.mvc_bw_ratio < 1.3:
    weaknesses.append("🔴 Fingerkraft ist der limitierende Faktor")
if cf.cf_mvc_ratio < 0.38:
    weaknesses.append("🔴 Aerobe Ausdauer deutlich unter Durchschnitt")
if cf.cf_mvc_ratio > 0.50 and result.mvc_bw_ratio < 1.3:
    weaknesses.append("🟡 Gute Ausdauer, aber Kraft hält nicht mit")

for w in weaknesses:
    print(w)

# Passende Protokolle empfehlen
plan = hangboard_calc.calculate_training_load(
    mvc7_kg=MVC7_KG, bodyweight_kg=BODYWEIGHT_KG,
    protocol="lopez_maxhangs"
)
print(f"\n📋 López MaxHangs @90%: {plan.added_load_kg:+.1f} kg auf {TEST_EDGE_MM}mm")
```

```markdown
## Referenzen

1. Rohmert W. (1960). Ermittlung von Erholungspausen für statische Arbeit
   des Menschen. *Int Z Angew Physiol*, 18, 123–164.
2. Monod H., Scherrer J. (1965). The work capacity of a synergic muscular
   group. *Ergonomics*, 8(3), 329–338.
3. Giles D. et al. (2019). The Determination of Finger-Flexor Critical
   Force in Rock Climbers. *Int J Sports Physiol Perform*, 1–8.
4. Hörst E. (2016). *Training for Climbing.* 3rd ed., Falcon Guides.
5. Lattice Training Assessment Benchmarks (n=436). latticetraining.com.
6. r/climbharder Survey 2017 (n=555).
```

---

### Notebook 2: `02_rohmert_curve_explained.ipynb`

**Titel:** *"Die Physik hinter dem Hangboard — Rohmerts Ermüdungskurve"*

**Inhalt:**

- Originalpaper Rohmert (1960) erklärt — was wurde gemessen, warum
- Mathematische Herleitung der Kurve (Sjøgaard 1986, Frey-Law & Avin 2010)
- Interaktiver Plot: %MVC vs. Time-to-Failure für 3 Modelle
- Warum "Expert" länger hält als "Beginner" — physiologische Erklärung
- Praktische Anwendung: "Ich halte 23s bei +20kg — was ist mein MVC-7?"
- Vergleich mit SC-Hangboard-Calculator-Ergebnissen

```python
# Interaktiv: Rohmert-Kurve plotten
from climbing_science.models import rohmert
from climbing_science.frontends import notebook

notebook.plot_rohmert_curve(models=["beginner", "intermediate", "expert"])

# Eigenen Datenpunkt einzeichnen:
my_ratio = 0.80  # 80% MVC
my_time = rohmert.time_to_failure(my_ratio, model="intermediate")
print(f"Bei {my_ratio:.0%} MVC hältst du ca. {my_time:.0f} Sekunden (Intermediate)")
```

---

### Notebook 3: `03_critical_force_analysis.ipynb`

**Titel:** *"Critical Force — Deine aerobe Kletterkapazität messen und verstehen"*

**Inhalt:**

- Was ist Critical Force? (Monod & Scherrer 1965 → Klettern)
- Das 3-Punkt-Testprotokoll Schritt für Schritt
- Lineare Regression visualisiert (Work vs. Time, CF = Steigung)
- W' erklärt: Dein "anaerober Tank" in kg·s
- CF/BW-Benchmarks pro Grad (Giles et al. 2019, Lattice)
- Was trainiert CF? Endurance Repeaters, Density Hangs
- SC-Calculator Vergleich (Demo-Datensatz)

---

### Notebook 4: `04_protocol_comparison.ipynb`

**Titel:** *"Welches Hangboard-Protokoll passt zu mir?"*

**Inhalt:**

- Alle 9 Protokolle im Überblick (Autor, Intensität, Energiesystem)
- Interaktiver Vergleich: eigene MVC-7 eingeben → Lasten für jedes Protokoll
- TUT-Vergleich: Welches Protokoll liefert wie viel Volumen?
- Entscheidungsbaum: Schwäche → empfohlenes Protokoll
- Referenzen pro Protokoll (López 2012, Hörst 2016, Nelson, Bechtel)

```python
from climbing_science.exercises import hangboard_calc
notebook.plot_protocol_comparison(mvc7_kg=105, bodyweight_kg=72)
```

---

### Notebook 5: `05_session_deep_dive.ipynb`

**Titel:** *"Tindeq-Session analysieren — Force-Curve unter der Lupe"*

**Inhalt:**

- Session laden (Tindeq JSON, Climbro CSV oder generisch)
- Force-Time-Kurve plotten mit Segment-Markierungen
- Peak Detection: Automatische MVC-7-Extraktion
- RFD-Analyse: Wie schnell baust du Kraft auf?
- Vergleich: Session A vs. Session B (Progression)
- Signal-Qualität: Rauschen, Artefakte erkennen

---

### Notebook 6: `06_progress_tracker.ipynb`

**Titel:** *"Fortschritt tracken — Wochen und Monate im Überblick"*

**Inhalt:**

- Alle Sessions aus einem Verzeichnis laden
- MVC-7 Progression über Zeit plotten
- Trend-Analyse: Linearer Fit + Projektion
- CF Progression (wenn CF-Tests vorhanden)
- Trainingsvolumen (TUT) pro Woche
- Warnung bei Stagnation oder Übertraining

---

### Notebook 7: `07_edge_depth_science.ipynb`

**Titel:** *"Warum 20mm? — Die Wissenschaft der Edge-Depth-Korrektur"*

**Inhalt:**

- Amca et al. (2012): Was wurde gemessen?
- Das 2.5%/mm Modell erklärt und hergeleitet
- Interaktiv: Kraft auf 15mm → was wäre das auf 20mm?
- Grenzen des Modells: Wo wird die lineare Korrektur ungenau?
- Empfehlung: Wann welche Edge-Tiefe zum Testen nutzen

---

### Design-Prinzipien für Notebooks

1. **Eingabe oben, Ergebnis darunter** — Nutzer ändert nur eine Zelle
2. **Jede Berechnung erklärt** — Markdown-Zelle vor jeder Code-Zelle
3. **Referenzen inline** — Jede Behauptung mit (Autor Jahr) belegt
4. **Referenzliste am Ende** — Vollständige Bibliographie
5. **Plots statt Tabellen** — Visuell wo möglich
6. **Benchmark-Kontext** — "Wo stehst du?" immer mit Vergleichsdaten
7. **Keine Magic Numbers** — Jede Konstante mit Quelle dokumentiert
8. **Copy-Paste-fähig** — Notebooks funktionieren standalone ohne Installation-Pain

### Dependencies für Notebooks

```toml
# In pyproject.toml unter [project.optional-dependencies]
notebooks = [
    "jupyter>=1.0",
    "matplotlib>=3.8",
    "pandas>=2.0",
    "ipywidgets>=8.0",    # Optional: Slider für interaktive Eingabe
]
```

---

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
