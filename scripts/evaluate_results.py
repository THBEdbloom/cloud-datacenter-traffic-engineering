#!/usr/bin/env python3
"""
Statistische Auswertung der ns-3-Datacenter-Experimente.

Das Skript verarbeitet die von datacenter.py erzeugten
Summary-Dateien mehrerer Routingstrategien, Szenarien und Runs.

Ausgewertet werden:

- Gesamtdurchsatz
- Paketverlust
- gewichtete mittlere Latenz
- gewichteter Jitter
- Jain's Fairness Index

Für jede Strategie-Szenario-Kombination werden berechnet:

- Anzahl der Runs
- Mittelwert
- Standardabweichung
- Minimum
- Maximum
- 95-%-Konfidenzintervall

Zusätzlich werden relative Verbesserungen gegenüber
STANDARD berechnet und Vergleichsdiagramme erzeugt.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


# =========================================================
# Konfiguration
# =========================================================

PROJECT_DIR = Path.cwd()

SUMMARY_PATTERN = "summary_*_seed_*_run_*.csv"

OUTPUT_DIR = PROJECT_DIR / "evaluation"

ALL_RUNS_FILE = (
    OUTPUT_DIR / "all_experiment_results.csv"
)

STATISTICS_FILE = (
    OUTPUT_DIR / "experiment_statistics.csv"
)

IMPROVEMENT_FILE = (
    OUTPUT_DIR / "relative_improvement_vs_standard.csv"
)


EXPECTED_STRATEGIES = [
    "STANDARD",
    "ECMP",
    "STATIC",
    "ADAPTIVE",
]

EXPECTED_SCENARIOS = [
    1,
    2,
    3,
    4,
    5,
    6,
    7,
]


SCENARIO_LABELS = {
    1: "Baseline",
    2: "Mittlere Last",
    3: "Hohe Last",
    4: "Überlast",
    5: "Hotspot",
    6: "Asymmetrische Last",
    7: "Dynamischer Hotspot",
}


STRATEGY_LABELS = {
    "STANDARD": "Standard",
    "ECMP": "ECMP",
    "STATIC": "Statisch",
    "ADAPTIVE": "Adaptiv",
}


# Szenarien werden für die Diagramme bewusst getrennt.
#
# S1-S4:
# klassische Lastskalierung
#
# S5-S7:
# Traffic-Engineering-spezifische Belastungen

SCENARIO_GROUPS = {
    "basis": {
        "scenarios": [1, 2, 3, 4],
        "title": "Basis- und Lastszenarien",
    },
    "traffic_engineering": {
        "scenarios": [5, 6, 7],
        "title": "Traffic-Engineering-Szenarien",
    },
}


REQUIRED_COLUMNS = {
    "routing_strategy",
    "scenario",
    "scenario_name",
    "seed",
    "run_number",
    "number_of_flows",
    "total_tx_packets",
    "total_rx_packets",
    "total_lost_packets",
    "packet_loss_percent",
    "total_throughput_mbit_s",
    "weighted_mean_delay_ms",
    "weighted_mean_jitter_ms",
    "jain_fairness_index",
}


METRICS = {
    "total_throughput_mbit_s": {
        "label": "Gesamtdurchsatz (Mbit/s)",
        "title": "Gesamtdurchsatz",
        "higher_is_better": True,
        "filename": "throughput",
    },
    "packet_loss_percent": {
        "label": "Paketverlust (%)",
        "title": "Paketverlust",
        "higher_is_better": False,
        "filename": "packet_loss",
    },
    "weighted_mean_delay_ms": {
        "label": "Gewichtete mittlere Latenz (ms)",
        "title": "Mittlere Latenz",
        "higher_is_better": False,
        "filename": "delay",
    },
    "weighted_mean_jitter_ms": {
        "label": "Gewichteter Jitter (ms)",
        "title": "Jitter",
        "higher_is_better": False,
        "filename": "jitter",
    },
    "jain_fairness_index": {
        "label": "Jain Fairness Index",
        "title": "Fairness",
        "higher_is_better": True,
        "filename": "fairness",
    },
}


# =========================================================
# Dateien einlesen
# =========================================================

def validate_columns(
    data: pd.DataFrame,
    path: Path,
) -> None:
    """
    Prüft, ob eine Summary-Datei alle erforderlichen
    Spalten enthält.
    """

    missing = REQUIRED_COLUMNS.difference(
        data.columns
    )

    if missing:
        raise ValueError(
            f"{path.name} enthält nicht alle "
            f"erwarteten Spalten. "
            f"Fehlend: {sorted(missing)}"
        )


def load_summary_file(
    path: Path,
) -> pd.DataFrame:
    """
    Liest eine Summary-Datei ein.
    """

    data = pd.read_csv(path)

    validate_columns(
        data,
        path,
    )

    if len(data) != 1:
        raise ValueError(
            f"{path.name} muss genau eine "
            "Ergebniszeile enthalten."
        )

    data = data.copy()

    data["source_file"] = path.name

    return data


def load_all_results() -> pd.DataFrame:
    """
    Lädt alle Summary-Dateien der Versuchsserie.
    """

    files = sorted(
        PROJECT_DIR.glob(
            SUMMARY_PATTERN
        )
    )

    if not files:
        raise FileNotFoundError(
            "Keine Summary-Dateien mit dem Muster "
            f"'{SUMMARY_PATTERN}' in "
            f"{PROJECT_DIR} gefunden."
        )

    print()
    print("=" * 60)
    print("Summary-Dateien einlesen")
    print("=" * 60)

    print(
        f"{len(files)} Dateien gefunden."
    )

    frames = []

    for path in files:
        print(
            f"Lese {path.name}"
        )

        frames.append(
            load_summary_file(path)
        )

    results = pd.concat(
        frames,
        ignore_index=True,
    )

    return results


# =========================================================
# Plausibilitätsprüfungen
# =========================================================

def validate_values(
    results: pd.DataFrame,
) -> None:
    """
    Prüft Strategien und Szenarien.
    """

    unknown_strategies = sorted(
        set(
            results[
                "routing_strategy"
            ]
        ).difference(
            EXPECTED_STRATEGIES
        )
    )

    if unknown_strategies:
        raise ValueError(
            "Unbekannte Routingstrategien: "
            f"{unknown_strategies}"
        )

    unknown_scenarios = sorted(
        set(
            results["scenario"]
        ).difference(
            EXPECTED_SCENARIOS
        )
    )

    if unknown_scenarios:
        raise ValueError(
            "Unbekannte Szenarien: "
            f"{unknown_scenarios}"
        )


def check_duplicates(
    results: pd.DataFrame,
) -> None:
    """
    Prüft doppelte Strategie-Szenario-Seed-Run-
    Kombinationen.
    """

    duplicate_mask = results.duplicated(
        subset=[
            "routing_strategy",
            "scenario",
            "seed",
            "run_number",
        ],
        keep=False,
    )

    if not duplicate_mask.any():
        return

    duplicate_rows = results.loc[
        duplicate_mask,
        [
            "routing_strategy",
            "scenario",
            "seed",
            "run_number",
            "source_file",
        ],
    ]

    raise ValueError(
        "Doppelte Experimente gefunden:\n"
        f"{duplicate_rows.to_string(index=False)}"
    )


def check_experiment_matrix(
    results: pd.DataFrame,
) -> None:
    """
    Prüft die Vollständigkeit der vorgesehenen Versuchsmatrix.

    Versuchsdesign:
        Szenario 1-4: Run 1
        Szenario 5-7: Runs 1, 2 und 3

    Für alle Experimente wird Seed 1 verwendet.
    """

    expected_runs = {
        1: [1],
        2: [1],
        3: [1],
        4: [1],
        5: [1, 2, 3],
        6: [1, 2, 3],
        7: [1, 2, 3],
    }

    expected_seeds = [1]

    found = {
        (
            row.routing_strategy,
            int(row.scenario),
            int(row.seed),
            int(row.run_number),
        )
        for row in results.itertuples()
    }

    expected = {
        (
            strategy,
            scenario,
            seed,
            run,
        )
        for strategy in EXPECTED_STRATEGIES
        for scenario in EXPECTED_SCENARIOS
        for seed in expected_seeds
        for run in expected_runs[scenario]
    }

    missing = sorted(
        expected.difference(found)
    )

    unexpected = sorted(
        found.difference(expected)
    )

    print()
    print("=" * 60)
    print("Versuchsmatrix")
    print("=" * 60)

    print(
        f"Strategien : "
        f"{len(EXPECTED_STRATEGIES)}"
    )

    print(
        f"Szenarien  : "
        f"{len(EXPECTED_SCENARIOS)}"
    )

    print(
        f"Seeds      : {expected_seeds}"
    )

    print(
        "Runs       : "
        "S1-S4 = [1], S5-S7 = [1, 2, 3]"
    )

    print(
        f"Gefunden   : {len(found)}"
    )

    print(
        f"Erwartet   : {len(expected)}"
    )

    if missing:
        print()
        print(
            "WARNUNG: Folgende Experimente fehlen:"
        )

        for strategy, scenario, seed, run in missing:
            print(
                f"  {strategy}, Szenario {scenario}, "
                f"Seed {seed}, Run {run}"
            )

    if unexpected:
        print()
        print(
            "WARNUNG: Nicht vorgesehene Experimente gefunden:"
        )

        for strategy, scenario, seed, run in unexpected:
            print(
                f"  {strategy}, Szenario {scenario}, "
                f"Seed {seed}, Run {run}"
            )

    if not missing and not unexpected:
        print(
            "Versuchsmatrix vollständig."
        )


def calculate_statistics(
    results: pd.DataFrame,
) -> pd.DataFrame:
    """
    Berechnet statistische Kennzahlen über alle Runs
    derselben Strategie-Szenario-Kombination.
    """

    rows = []

    grouped = results.groupby(
        [
            "routing_strategy",
            "scenario",
            "scenario_name",
        ],
        sort=False,
    )

    for (
        strategy,
        scenario,
        scenario_name,
    ), group in grouped:

        row = {
            "routing_strategy": strategy,
            "strategy_label": (
                STRATEGY_LABELS[strategy]
            ),
            "scenario": int(scenario),
            "scenario_label": (
                SCENARIO_LABELS[
                    int(scenario)
                ]
            ),
            "scenario_name": scenario_name,
            "number_of_runs": int(
                len(group)
            ),
            "number_of_flows": float(
                group[
                    "number_of_flows"
                ].mean()
            ),
        }

        for metric in METRICS:

            values = (
                group[metric]
                .astype(float)
            )

            n = len(values)

            mean_value = float(
                values.mean()
            )

            min_value = float(
                values.min()
            )

            max_value = float(
                values.max()
            )

            # Die Experimente verwenden einen deterministischen
            # Verkehrsaufbau. Unterschiedliche Run-Nummern dienen
            # daher primär der Prüfung der Reproduzierbarkeit und
            # werden nicht als unabhängige Zufallsstichproben
            # interpretiert.
            #
            # Die Standardabweichung wird weiterhin deskriptiv
            # angegeben. Ein inferenzstatistisches
            # Konfidenzintervall wird bewusst nicht berechnet.

            if n > 1:
                std_value = float(
                    values.std(
                        ddof=1
                    )
                )
            else:
                std_value = 0.0

            ci95 = float("nan")

            # Prüfung auf praktische Reproduzierbarkeit.
            #
            # Sehr kleine numerische Abweichungen können durch
            # interne Simulations- bzw. Rundungseffekte entstehen
            # und werden nicht als relevante Run-Variation gewertet.
            tolerance = max(
                abs(mean_value) * 1e-6,
                1e-9,
            )

            runs_identical = bool(
                (values - mean_value)
                .abs()
                .max()
                <= tolerance
            )

            row[
                f"{metric}_mean"
            ] = mean_value

            row[
                f"{metric}_std"
            ] = std_value

            row[
                f"{metric}_min"
            ] = min_value

            row[
                f"{metric}_max"
            ] = max_value

            row[
                f"{metric}_ci95"
            ] = ci95

            row[
                f"{metric}_runs_identical"
            ] = runs_identical

        rows.append(row)

    statistics = pd.DataFrame(
        rows
    )

    strategy_order = {
        strategy: index
        for index, strategy
        in enumerate(
            EXPECTED_STRATEGIES
        )
    }

    statistics[
        "strategy_order"
    ] = statistics[
        "routing_strategy"
    ].map(
        strategy_order
    )

    statistics = (
        statistics
        .sort_values(
            by=[
                "scenario",
                "strategy_order",
            ]
        )
        .drop(
            columns=[
                "strategy_order"
            ]
        )
        .reset_index(
            drop=True
        )
    )

    return statistics


# =========================================================
# Relative Verbesserung gegenüber STANDARD
# =========================================================

def calculate_relative_improvements(
    statistics: pd.DataFrame,
) -> pd.DataFrame:
    """
    Berechnet die relative Verbesserung jeder Strategie
    gegenüber STANDARD.

    Positive Werte bedeuten eine Verbesserung.

    Bei Durchsatz und Fairness ist ein höherer Wert besser.
    Bei Verlust, Latenz und Jitter ist ein niedrigerer Wert
    besser.
    """

    rows = []

    for scenario in EXPECTED_SCENARIOS:

        scenario_data = statistics[
            statistics["scenario"]
            == scenario
        ]

        standard_rows = scenario_data[
            scenario_data[
                "routing_strategy"
            ]
            == "STANDARD"
        ]

        if standard_rows.empty:
            continue

        standard = (
            standard_rows.iloc[0]
        )

        for _, row in (
            scenario_data.iterrows()
        ):

            if (
                row[
                    "routing_strategy"
                ]
                == "STANDARD"
            ):
                continue

            result = {
                "scenario": scenario,
                "scenario_label": (
                    SCENARIO_LABELS[
                        scenario
                    ]
                ),
                "routing_strategy": (
                    row[
                        "routing_strategy"
                    ]
                ),
                "strategy_label": (
                    row[
                        "strategy_label"
                    ]
                ),
            }

            for metric, config in (
                METRICS.items()
            ):

                standard_value = float(
                    standard[
                        f"{metric}_mean"
                    ]
                )

                strategy_value = float(
                    row[
                        f"{metric}_mean"
                    ]
                )

                if (
                    abs(
                        standard_value
                    )
                    < 1e-12
                ):
                    improvement = float(
                        "nan"
                    )

                elif config[
                    "higher_is_better"
                ]:

                    improvement = (
                        (
                            strategy_value
                            - standard_value
                        )
                        / standard_value
                        * 100.0
                    )

                else:

                    improvement = (
                        (
                            standard_value
                            - strategy_value
                        )
                        / standard_value
                        * 100.0
                    )

                result[
                    f"{metric}_improvement_percent"
                ] = improvement

            rows.append(result)

    return pd.DataFrame(rows)


# =========================================================
# Konsolenausgabe
# =========================================================

def print_statistics(
    statistics: pd.DataFrame,
) -> None:
    """
    Gibt die wichtigsten Mittelwerte kompakt aus.
    """

    table = statistics[
        [
            "strategy_label",
            "scenario",
            "number_of_runs",
            "total_throughput_mbit_s_mean",
            "packet_loss_percent_mean",
            "weighted_mean_delay_ms_mean",
            "weighted_mean_jitter_ms_mean",
            "jain_fairness_index_mean",
        ]
    ].copy()

    table = table.rename(
        columns={
            "strategy_label": (
                "Strategie"
            ),
            "scenario": (
                "Szenario"
            ),
            "number_of_runs": (
                "Runs"
            ),
            "total_throughput_mbit_s_mean": (
                "Durchsatz_Mbit_s"
            ),
            "packet_loss_percent_mean": (
                "Paketverlust_%"
            ),
            "weighted_mean_delay_ms_mean": (
                "Latenz_ms"
            ),
            "weighted_mean_jitter_ms_mean": (
                "Jitter_ms"
            ),
            "jain_fairness_index_mean": (
                "Fairness"
            ),
        }
    )

    print()
    print("=" * 60)
    print("Statistische Gesamtauswertung")
    print("=" * 60)
    print()

    print(
        table.to_string(
            index=False,
            float_format=(
                lambda value:
                f"{value:.4f}"
            ),
        )
    )


# =========================================================
# Diagramme
# =========================================================

def create_metric_chart(
    statistics: pd.DataFrame,
    metric: str,
    scenarios: list[int],
    group_title: str,
    output_name: str,
) -> None:
    """
    Erstellt gruppierte Balkendiagramme mit
    95-%-Konfidenzintervallen.
    """

    config = METRICS[metric]

    figure, axis = plt.subplots(
        figsize=(11, 6)
    )

    number_of_strategies = len(
        EXPECTED_STRATEGIES
    )

    width = 0.18

    x_positions = list(
        range(len(scenarios))
    )

    for strategy_index, strategy in enumerate(
        EXPECTED_STRATEGIES
    ):

        means = []
        errors = []

        for scenario in scenarios:

            row = statistics[
                (
                    statistics[
                        "routing_strategy"
                    ]
                    == strategy
                )
                &
                (
                    statistics[
                        "scenario"
                    ]
                    == scenario
                )
            ]

            if row.empty:
                means.append(0.0)
                errors.append(0.0)
            else:
                values = row.iloc[0]

                means.append(
                    float(
                        values[
                            f"{metric}_mean"
                        ]
                    )
                )

                errors.append(
                    float(
                        values[
                            f"{metric}_ci95"
                        ]
                    )
                )

        offset = (
            strategy_index
            - (
                number_of_strategies
                - 1
            )
            / 2
        ) * width

        positions = [
            value + offset
            for value in x_positions
        ]

        axis.bar(
            positions,
            means,
            width=width,
            yerr=errors,
            capsize=3,
            label=(
                STRATEGY_LABELS[
                    strategy
                ]
            ),
        )

    axis.set_title(
        f"{config['title']} – "
        f"{group_title}"
    )

    axis.set_xlabel(
        "Traffic-Szenario"
    )

    axis.set_ylabel(
        config["label"]
    )

    axis.set_xticks(
        x_positions
    )

    axis.set_xticklabels(
        [
            SCENARIO_LABELS[
                scenario
            ]
            for scenario
            in scenarios
        ],
        rotation=0,
    )

    axis.grid(
        axis="y",
        alpha=0.3,
    )

    axis.legend()

    figure.tight_layout()

    png_file = (
        OUTPUT_DIR
        / f"{output_name}.png"
    )

    pdf_file = (
        OUTPUT_DIR
        / f"{output_name}.pdf"
    )

    figure.savefig(
        png_file,
        dpi=200,
        bbox_inches="tight",
    )

    figure.savefig(
        pdf_file,
        bbox_inches="tight",
    )

    plt.close(
        figure
    )


def create_all_charts(
    statistics: pd.DataFrame,
) -> None:
    """
    Erzeugt Diagramme für alle Messgrößen und
    beide Szenariogruppen.
    """

    for group_name, group in (
        SCENARIO_GROUPS.items()
    ):

        scenarios = group[
            "scenarios"
        ]

        title = group[
            "title"
        ]

        for metric, config in (
            METRICS.items()
        ):

            output_name = (
                f"{config['filename']}_"
                f"{group_name}"
            )

            create_metric_chart(
                statistics,
                metric,
                scenarios,
                title,
                output_name,
            )


# =========================================================
# Dateien ausgeben
# =========================================================

def print_output_files() -> None:
    """
    Zeigt die wichtigsten erzeugten Dateien.
    """

    print()
    print("=" * 60)
    print("Erzeugte Auswertungsdateien")
    print("=" * 60)

    print(
        f"Alle Runs        : "
        f"{ALL_RUNS_FILE}"
    )

    print(
        f"Statistik        : "
        f"{STATISTICS_FILE}"
    )

    print(
        f"Verbesserungen   : "
        f"{IMPROVEMENT_FILE}"
    )

    print()
    print(
        f"Diagramme        : "
        f"{OUTPUT_DIR}"
    )


# =========================================================
# Hauptprogramm
# =========================================================

def main() -> None:
    """
    Führt die vollständige statistische Auswertung aus.
    """

    results = load_all_results()

    validate_values(
        results
    )

    check_duplicates(
        results
    )

    check_experiment_matrix(
        results
    )

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    # Alle einzelnen Runs speichern.
    results = results.sort_values(
        by=[
            "scenario",
            "routing_strategy",
            "seed",
            "run_number",
        ]
    )

    results.to_csv(
        ALL_RUNS_FILE,
        index=False,
        encoding="utf-8",
    )

    # Statistische Kennzahlen berechnen.
    statistics = calculate_statistics(
        results
    )

    statistics.to_csv(
        STATISTICS_FILE,
        index=False,
        encoding="utf-8",
    )

    # Relative Verbesserungen berechnen.
    improvements = (
        calculate_relative_improvements(
            statistics
        )
    )

    improvements.to_csv(
        IMPROVEMENT_FILE,
        index=False,
        encoding="utf-8",
    )

    print_statistics(
        statistics
    )

    create_all_charts(
        statistics
    )

    print_output_files()


if __name__ == "__main__":
    main()