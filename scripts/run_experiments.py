#!/usr/bin/env python3
"""
Führt alle definierten ns-3-Datacenter-Simulationen automatisch aus.

Für jede Kombination aus

- Routingstrategie
- Traffic-Szenario

wird die Datacenter-Simulation einmal gestartet.

Untersuchte Routingstrategien:

- STANDARD
- ECMP
- STATIC
- ADAPTIVE

Für jede Routingstrategie werden vier Lastszenarien ausgeführt:

1. Baseline
2. Mittlere Last
3. Hohe Last
4. Überlast

Damit werden insgesamt 4 x 4 = 16 Simulationen durchgeführt.

Ausführung aus dem ns-3-Hauptverzeichnis:

    python3 python/run_experiments.py
"""

from __future__ import annotations

import subprocess


# =========================================================
# Experimentkonfiguration
# =========================================================

ROUTING_STRATEGIES = [
    "STANDARD",
    "ECMP",
    "STATIC",
    "ADAPTIVE",
]

SCENARIOS = [
    1,
    2,
    3,
    4,
]


# =========================================================
# Einzelne Simulation ausführen
# =========================================================

def run_simulation(
    routing_strategy: str,
    scenario: int,
) -> None:
    """
    Startet eine einzelne Datacenter-Simulation.

    Die Routingstrategie und das Traffic-Szenario werden
    als Kommandozeilenargumente an datacenter.py übergeben.

    Bei einem Fehler beendet subprocess.run() das Skript
    aufgrund von check=True mit einer Fehlermeldung.
    """

    print("\n" + "=" * 60)
    print(f"Routingstrategie : {routing_strategy}")
    print(f"Traffic-Szenario : {scenario}")
    print("=" * 60)

    subprocess.run(
        [
            "./ns3",
            "run",
            f"python/datacenter.py {routing_strategy} {scenario}",
        ],
        check=True,
    )


# =========================================================
# Hauptprogramm
# =========================================================

def main() -> None:
    """
    Führt alle Kombinationen aus Routingstrategie und
    Traffic-Szenario nacheinander aus.
    """

    total_runs = (
        len(ROUTING_STRATEGIES)
        * len(SCENARIOS)
    )

    print("\n==========================================")
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
    print(
        f"Alle {total_runs} Simulationen wurden "
        f"erfolgreich abgeschlossen."
    )
    print("==========================================")


if __name__ == "__main__":
    main()