# Cloud Datacenter Traffic Engineering

Simulation und Auswertung verschiedener Traffic-Engineering-Strategien
in einer Spine-Leaf-Topologie mit ns-3 und Python.

## Forschungsfrage

Welchen Einfluss haben verschiedene Traffic-Engineering-Strategien auf
die Leistungsfähigkeit eines Cloud-Rechenzentrums hinsichtlich Latenz,
Durchsatz und Paketverlust?

## Topologie

- 2 Spine-Knoten
- 2 Leaf-Knoten
- 4 Hosts
- vollständige Spine-Leaf-Verbindung
- 10-Gbit/s-Links
- 2-ms-Linkverzögerung

## Routingstrategien

- Standard Routing
- ECMP
- statisches Flow-Pinning

## Lastszenarien

1. Baseline: ein Flow mit 100 Mbit/s
2. Mittlere Last: vier Flows mit jeweils 100 Mbit/s
3. Hohe Last: vier Flows mit jeweils 2 Gbit/s
4. Überlast: vier Flows mit jeweils 12 Gbit/s

## Messgrößen

- Durchsatz
- Ende-zu-Ende-Latenz
- Paketverlust
- Jitter
- gesendete und empfangene Pakete

## Projektstruktur

```text
simulation/
    datacenter.py

scripts/
    run_experiments.py
    evaluate_results.py

results/
    einzelne CSV-Ergebnisdateien

evaluation/
    Zusammenfassung und Diagramme
Voraussetzungen
Linux oder WSL
ns-3 mit aktivierten Python-Bindings
Python
cppyy
pandas
matplotlib
Einzelne Simulation starten
cd ~/ns-3-dev
./ns3 run "/home/edbloom/cloud-datacenter-traffic-engineering/simulation/datacenter.py STANDARD 1"

Mögliche Strategien:

STANDARD
ECMP
STATIC

Mögliche Szenarien:

1
2
3
4
Alle Experimente ausführen
cd ~/cloud-datacenter-traffic-engineering
python3 scripts/run_experiments.py
Ergebnisse auswerten
cd ~/cloud-datacenter-traffic-engineering
python3 scripts/evaluate_results.py

# Schritt 10: Git initialisieren

```bash
git init
git branch -M main

Falls Git noch keinen Namen und keine E-Mail kennt:

git config --global user.name "Laurin Krüger"
git config --global user.email "DEINE-GITHUB-EMAIL"