#!/usr/bin/env python3
"""
Auswertung aller ns-3-Datacenter-Experimente.

Das Skript:
1. sucht alle Ergebnisdateien mit dem Muster ``results_*.csv``,
2. erkennt Routingstrategie und Szenario aus dem Dateinamen,
3. prüft die Vollständigkeit der Versuchsmatrix,
4. berechnet zusammengefasste Kennzahlen pro Versuch,
5. schreibt eine gemeinsame CSV-Zusammenfassung,
6. erzeugt Vergleichsdiagramme als PNG- und PDF-Dateien.

Ausführung aus dem ns-3-Hauptverzeichnis:

    python3 python/evaluate_results.py

Benötigte Python-Pakete:

    pip install pandas matplotlib
"""

from __future__ import annotations

import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# =========================================================
# Allgemeine Konfiguration
# =========================================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
RESULT_DIR = PROJECT_DIR / "results"
RESULT_PATTERN = "results_*.csv"

OUTPUT_DIR = PROJECT_DIR / "evaluation"
SUMMARY_FILE = OUTPUT_DIR / "experiment_summary.csv"

EXPECTED_STRATEGIES = ["STANDARD", "ECMP", "STATIC"]
EXPECTED_SCENARIOS = [1, 2, 3, 4]

SCENARIO_LABELS = {
    1: "Baseline",
    2: "Mittlere Last",
    3: "Hohe Last",
    4: "Überlast",
}

STRATEGY_LABELS = {
    "STANDARD": "Standard",
    "ECMP": "ECMP",
    "STATIC": "Statisch",
}

REQUIRED_COLUMNS = {
    "flow_id",
    "tx_packets",
    "rx_packets",
    "lost_packets",
    "tx_bytes",
    "rx_bytes",
    "packet_loss_percent",
    "throughput_mbit_s",
    "mean_delay_ms",
    "mean_jitter_ms",
}


# =========================================================
# Dateinamen und Eingabedaten
# =========================================================

def parse_filename(path: Path) -> tuple[str, int]:
    """
    Liest Routingstrategie und Szenarionummer aus dem Dateinamen.

    Erwartetes Muster:
        results_<strategie>_szenario_<nummer>_*.csv

    Beispiel:
        results_ecmp_szenario_3__hohe_last.csv

    Rückgabe:
        ("ECMP", 3)
    """

    match = re.match(
        r"results_(standard|ecmp|static)_szenario_(\d+)",
        path.name.lower(),
    )

    if match is None:
        raise ValueError(
            "Dateiname entspricht nicht dem erwarteten Muster: "
            f"{path.name}"
        )

    strategy = match.group(1).upper()
    scenario = int(match.group(2))

    if strategy not in EXPECTED_STRATEGIES:
        raise ValueError(
            f"Unbekannte Routingstrategie in {path.name}: {strategy}"
        )

    if scenario not in EXPECTED_SCENARIOS:
        raise ValueError(
            f"Unbekanntes Szenario in {path.name}: {scenario}"
        )

    return strategy, scenario


def validate_columns(data: pd.DataFrame, path: Path) -> None:
    """Prüft, ob eine Ergebnisdatei alle erwarteten Spalten enthält."""

    missing_columns = REQUIRED_COLUMNS.difference(data.columns)

    if missing_columns:
        raise ValueError(
            f"{path.name} enthält nicht alle erwarteten Spalten. "
            f"Fehlend: {sorted(missing_columns)}"
        )


def weighted_mean(values: pd.Series, weights: pd.Series) -> float:
    """
    Berechnet einen gewichteten Mittelwert.

    Falls die Summe der Gewichte null ist, wird 0.0 zurückgegeben.
    """

    total_weight = float(weights.sum())

    if total_weight <= 0.0:
        return 0.0

    return float((values * weights).sum() / total_weight)


def load_experiment(path: Path) -> dict[str, object]:
    """
    Liest eine einzelne Ergebnisdatei ein und berechnet
    zusammengefasste Kennzahlen für den gesamten Versuch.
    """

    strategy, scenario = parse_filename(path)
    data = pd.read_csv(path)

    validate_columns(data, path)

    if data.empty:
        raise ValueError(f"{path.name} enthält keine Flow-Daten.")

    total_tx_packets = int(data["tx_packets"].sum())
    total_rx_packets = int(data["rx_packets"].sum())
    total_lost_packets = int(data["lost_packets"].sum())

    total_throughput = float(data["throughput_mbit_s"].sum())
    mean_throughput = float(data["throughput_mbit_s"].mean())

    # Gewichtung nach der Zahl empfangener Pakete.
    mean_delay = weighted_mean(
        data["mean_delay_ms"],
        data["rx_packets"],
    )

    # FlowMonitor berechnet Jitter über aufeinanderfolgende Pakete.
    jitter_weights = (data["rx_packets"] - 1).clip(lower=0)
    mean_jitter = weighted_mean(
        data["mean_jitter_ms"],
        jitter_weights,
    )

    total_loss_percent = (
        total_lost_packets / total_tx_packets * 100.0
        if total_tx_packets > 0
        else 0.0
    )

    return {
        "strategy": strategy,
        "strategy_label": STRATEGY_LABELS[strategy],
        "scenario": scenario,
        "scenario_label": SCENARIO_LABELS[scenario],
        "flow_count": int(len(data)),
        "total_tx_packets": total_tx_packets,
        "total_rx_packets": total_rx_packets,
        "total_lost_packets": total_lost_packets,
        "total_packet_loss_percent": total_loss_percent,
        "total_throughput_mbit_s": total_throughput,
        "mean_throughput_mbit_s": mean_throughput,
        "mean_delay_ms": mean_delay,
        "mean_jitter_ms": mean_jitter,
        "source_file": path.name,
    }


# =========================================================
# Vollständigkeits- und Plausibilitätsprüfungen
# =========================================================

def check_duplicate_experiments(summary: pd.DataFrame) -> None:
    """
    Prüft, ob mehrere Dateien dieselbe Kombination aus
    Routingstrategie und Szenario repräsentieren.
    """

    duplicates = summary.duplicated(
        subset=["strategy", "scenario"],
        keep=False,
    )

    if not duplicates.any():
        return

    duplicate_rows = summary.loc[
        duplicates,
        ["strategy", "scenario", "source_file"],
    ]

    raise ValueError(
        "Mehrere Ergebnisdateien für dieselbe "
        "Strategie-Szenario-Kombination gefunden:\n"
        f"{duplicate_rows.to_string(index=False)}"
    )


def check_experiment_matrix(summary: pd.DataFrame) -> None:
    """
    Prüft, ob alle erwarteten Kombinationen aus
    Routingstrategie und Szenario vorhanden sind.
    """

    found = {
        (row.strategy, int(row.scenario))
        for row in summary.itertuples()
    }

    expected = {
        (strategy, scenario)
        for strategy in EXPECTED_STRATEGIES
        for scenario in EXPECTED_SCENARIOS
    }

    missing = sorted(expected.difference(found))
    unexpected = sorted(found.difference(expected))

    if missing:
        print("\nWARNUNG: Folgende Versuche fehlen:")
        for strategy, scenario in missing:
            print(f"  {strategy}, Szenario {scenario}")

    if unexpected:
        print("\nHinweis: Zusätzliche Versuche gefunden:")
        for strategy, scenario in unexpected:
            print(f"  {strategy}, Szenario {scenario}")

    if not missing:
        print("\nAlle 12 erwarteten Versuche wurden gefunden.")


# =========================================================
# Tabellen- und Diagrammausgabe
# =========================================================

def print_summary(summary: pd.DataFrame) -> None:
    """
    Gibt die zusammengefassten Versuchsergebnisse als
    formatierte Tabelle auf der Konsole aus.
    """

    display_columns = [
        "strategy_label",
        "scenario",
        "flow_count",
        "total_throughput_mbit_s",
        "mean_delay_ms",
        "total_packet_loss_percent",
        "mean_jitter_ms",
    ]

    terminal_table = summary[display_columns].copy()
    terminal_table = terminal_table.rename(
        columns={
            "strategy_label": "Strategie",
            "scenario": "Szenario",
            "flow_count": "Flows",
            "total_throughput_mbit_s": "Gesamtdurchsatz_Mbit_s",
            "mean_delay_ms": "Mittlere_Latenz_ms",
            "total_packet_loss_percent": "Paketverlust_Prozent",
            "mean_jitter_ms": "Mittlerer_Jitter_ms",
        }
    )

    print("\n==========================================")
    print("Gesamtauswertung")
    print("==========================================\n")

    print(
        terminal_table.to_string(
            index=False,
            float_format=lambda value: f"{value:.3f}",
        )
    )


def create_grouped_bar_chart(
    summary: pd.DataFrame,
    value_column: str,
    ylabel: str,
    title: str,
    output_file: Path,
) -> None:
    """
    Erstellt ein gruppiertes Balkendiagramm.

    Die Szenarien werden auf der x-Achse dargestellt.
    Für jede Routingstrategie wird eine eigene Balkengruppe erzeugt.
    Das Diagramm wird als PNG und PDF gespeichert.
    """

    pivot = summary.pivot(
        index="scenario",
        columns="strategy",
        values=value_column,
    )

    pivot = pivot.reindex(
        index=EXPECTED_SCENARIOS,
        columns=EXPECTED_STRATEGIES,
    )

    pivot = pivot.rename(
        index=SCENARIO_LABELS,
        columns=STRATEGY_LABELS,
    )

    axis = pivot.plot(
        kind="bar",
        figsize=(10, 6),
    )

    axis.set_title(title)
    axis.set_xlabel("Traffic-Szenario")
    axis.set_ylabel(ylabel)
    axis.tick_params(axis="x", rotation=0)
    axis.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    plt.savefig(
        output_file,
        dpi=200,
        bbox_inches="tight",
    )

    plt.savefig(
        output_file.with_suffix(".pdf"),
        bbox_inches="tight",
    )

    plt.close()


def create_all_charts(summary: pd.DataFrame) -> None:
    """Erzeugt alle vorgesehenen Vergleichsdiagramme."""

    create_grouped_bar_chart(
        summary,
        "total_throughput_mbit_s",
        "Gesamtdurchsatz (Mbit/s)",
        "Gesamtdurchsatz nach Strategie und Szenario",
        OUTPUT_DIR / "throughput_comparison.png",
    )

    create_grouped_bar_chart(
        summary,
        "mean_delay_ms",
        "Mittlere Latenz (ms)",
        "Mittlere Latenz nach Strategie und Szenario",
        OUTPUT_DIR / "delay_comparison.png",
    )

    create_grouped_bar_chart(
        summary,
        "total_packet_loss_percent",
        "Paketverlust (%)",
        "Paketverlust nach Strategie und Szenario",
        OUTPUT_DIR / "packet_loss_comparison.png",
    )

    create_grouped_bar_chart(
        summary,
        "mean_jitter_ms",
        "Mittlerer Jitter (ms)",
        "Mittlerer Jitter nach Strategie und Szenario",
        OUTPUT_DIR / "jitter_comparison.png",
    )


def print_output_files() -> None:
    """Gibt alle erzeugten Auswertungsdateien auf der Konsole aus."""

    print("\n==========================================")
    print("Erzeugte Auswertungsdateien")
    print("==========================================")

    print(f"CSV              : {SUMMARY_FILE}")
    print(f"Durchsatz PNG    : {OUTPUT_DIR / 'throughput_comparison.png'}")
    print(f"Durchsatz PDF    : {OUTPUT_DIR / 'throughput_comparison.pdf'}")
    print(f"Latenz PNG       : {OUTPUT_DIR / 'delay_comparison.png'}")
    print(f"Latenz PDF       : {OUTPUT_DIR / 'delay_comparison.pdf'}")
    print(f"Paketverlust PNG : {OUTPUT_DIR / 'packet_loss_comparison.png'}")
    print(f"Paketverlust PDF : {OUTPUT_DIR / 'packet_loss_comparison.pdf'}")
    print(f"Jitter PNG       : {OUTPUT_DIR / 'jitter_comparison.png'}")
    print(f"Jitter PDF       : {OUTPUT_DIR / 'jitter_comparison.pdf'}")


# =========================================================
# Hauptprogramm
# =========================================================

def main() -> None:
    """Führt die vollständige Auswertung aller Experimente aus."""

    result_files = sorted(RESULT_DIR.glob(RESULT_PATTERN))

    if not result_files:
        raise FileNotFoundError(
            f"Keine Dateien mit dem Muster '{RESULT_PATTERN}' "
            f"in {PROJECT_DIR} gefunden."
        )

    print("\n==========================================")
    print("Ergebnisdateien einlesen")
    print("==========================================")
    print(f"{len(result_files)} Ergebnisdateien gefunden.")

    rows: list[dict[str, object]] = []

    for result_file in result_files:
        print(f"Lese {result_file.name}")
        rows.append(load_experiment(result_file))

    summary = pd.DataFrame(rows)

    check_duplicate_experiments(summary)
    check_experiment_matrix(summary)

    strategy_order = {
        strategy: index
        for index, strategy in enumerate(EXPECTED_STRATEGIES)
    }

    summary["strategy_order"] = summary["strategy"].map(
        strategy_order
    )

    summary = summary.sort_values(
        by=["scenario", "strategy_order"],
    ).drop(columns=["strategy_order"])

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary.to_csv(
        SUMMARY_FILE,
        index=False,
        encoding="utf-8",
    )

    print_summary(summary)
    create_all_charts(summary)
    print_output_files()


if __name__ == "__main__":
    main()