#!/usr/bin/env python3
"""
Führt alle definierten Simulationen automatisch aus.

Für jede Kombination aus

- Routingstrategie
- Traffic-Szenario

wird die Datacenter-Simulation gestartet.

Aktuell werden folgende Routingstrategien getestet:

- STANDARD
- ECMP
- STATIC

Für jede Strategie werden vier Lastszenarien ausgeführt.

Ausführung:

    python3 python/run_experiments.py
"""

from __future__ import annotations

import subprocess

from pathlib import Path

# Pfad zum ns-3-Verzeichnis
NS3_DIR = Path.home() / "ns-3-dev"

# Pfad zur Simulation
SIMULATION_FILE = (
    Path.home()
    / "cloud-datacenter-traffic-engineering"
    / "simulation"
    / "datacenter.py"
)


# =========================================================
# Konfiguration
# =========================================================

ROUTING_STRATEGIES = [
    "STANDARD",
    "ECMP",
    "STATIC",
]

SCENARIOS = [
    1,
    2,
    3,
    4,
]


# =========================================================
# Hilfsfunktion
# =========================================================

def run_simulation(
    routing_strategy: str,
    scenario: int,
) -> None:
    """
    Startet eine einzelne Simulation.
    """

    print("\n============================================================")
    print(f"Routingstrategie : {routing_strategy}")
    print(f"Traffic-Szenario : {scenario}")
    print("============================================================")

    subprocess.run(
        [
            "./ns3",
            "run",
            f"{SIMULATION_FILE} {routing_strategy} {scenario}",
        ],
        cwd=NS3_DIR,
        check=True,
    )


# =========================================================
# Hauptprogramm
# =========================================================

def main() -> None:
    """
    Führt alle Kombinationen aus Routingstrategie
    und Traffic-Szenario aus.
    """

    total_runs = (
        len(ROUTING_STRATEGIES)
        * len(SCENARIOS)
    )

    print("==========================================")
    print("Automatisierte Versuchsdurchführung")
    print("==========================================")

    print(f"Routingstrategien : {len(ROUTING_STRATEGIES)}")
    print(f"Szenarien         : {len(SCENARIOS)}")
    print(f"Simulationen      : {total_runs}")

    run_number = 1

    for routing_strategy in ROUTING_STRATEGIES:

        for scenario in SCENARIOS:

            print(
                f"\n--- Versuch "
                f"{run_number}/{total_runs} ---"
            )

            run_simulation(
                routing_strategy,
                scenario,
            )

            run_number += 1

    print("\n==========================================")
    print("Alle Simulationen wurden erfolgreich abgeschlossen.")
    print("==========================================")


if __name__ == "__main__":
    main()