#!/usr/bin/env python3

import subprocess
import sys
import time
from pathlib import Path


# =========================================================
# Experimentkonfiguration
# =========================================================

STRATEGIES = [
    "STANDARD",
    "ECMP",
    "STATIC",
    "ADAPTIVE",
]

SCENARIOS = range(1, 9)

SEED = 1

# Szenarien 1-4:
# grundlegende Referenz- und Lastszenarien mit einem Lauf.
#
# Szenarien 5-8:
# komplexere Hotspot-, asymmetrische, dynamische und
# Ausfallszenarien mit drei Wiederholungen.
RUNS_BY_SCENARIO = {
    1: [1],
    2: [1],
    3: [1],
    4: [1],
    5: [1, 2, 3],
    6: [1, 2, 3],
    7: [1, 2, 3],
    8: [1, 2, 3],
}


# =========================================================
# Verzeichnisse
# =========================================================

NS3_DIR = Path.home() / "ns-3-dev"

LOG_DIR = NS3_DIR / "experiment_logs"
LOG_DIR.mkdir(exist_ok=True)


# =========================================================
# Experimentübersicht
# =========================================================

experiments = [
    (strategy, scenario, run)
    for scenario in SCENARIOS
    for strategy in STRATEGIES
    for run in RUNS_BY_SCENARIO[scenario]
]

total = len(experiments)

print("=" * 60)
print("Datacenter Routing - Experimentserie")
print("=" * 60)
print(f"Strategien : {len(STRATEGIES)}")
print(f"Szenarien  : {len(list(SCENARIOS))}")
print("Runs       : S1-S4 = [1], S5-S8 = [1, 2, 3]")
print(f"Seed       : {SEED}")
print(f"Gesamt     : {total} Simulationen")
print("=" * 60)


# =========================================================
# Simulationen durchführen
# =========================================================

successful = 0
failed = 0

start_all = time.time()

for index, (strategy, scenario, run) in enumerate(
    experiments,
    start=1,
):
    print()
    print("=" * 60)
    print(
        f"[{index}/{total}] "
        f"{strategy} | Szenario {scenario} | Run {run}"
    )
    print("=" * 60)

    command = [
        "./ns3",
        "run",
        (
            f"python/datacenter.py "
            f"{strategy} {scenario} {SEED} {run}"
        ),
    ]

    log_file = LOG_DIR / (
        f"{strategy.lower()}_"
        f"szenario_{scenario}_"
        f"seed_{SEED}_run_{run}.log"
    )

    start = time.time()

    with open(
        log_file,
        "w",
        encoding="utf-8",
    ) as output:
        result = subprocess.run(
            command,
            cwd=NS3_DIR,
            stdout=output,
            stderr=subprocess.STDOUT,
        )

    duration = time.time() - start

    if result.returncode == 0:
        successful += 1
        print(f"OK nach {duration:.1f} Sekunden")

    else:
        failed += 1
        print(f"FEHLER nach {duration:.1f} Sekunden")
        print(f"Logdatei: {log_file}")


# =========================================================
# Abschluss
# =========================================================

duration_all = time.time() - start_all

print()
print("=" * 60)
print("Experimentserie abgeschlossen")
print("=" * 60)
print(f"Erfolgreich : {successful}")
print(f"Fehler      : {failed}")
print(f"Gesamt      : {total}")
print(f"Laufzeit    : {duration_all / 60.0:.1f} Minuten")

if failed > 0:
    sys.exit(1)