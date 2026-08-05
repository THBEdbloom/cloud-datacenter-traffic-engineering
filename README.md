# Cloud Datacenter Traffic Engineering

Simulation und Analyse verschiedener Traffic-Engineering-Strategien in einem Spine-Leaf-Rechenzentrum mit **ns-3** und **Python**.

Dieses Projekt entstand im Rahmen einer Bachelorarbeit und untersucht den Einfluss verschiedener Routingstrategien auf die Netzwerkperformance eines Cloud-Rechenzentrums.

---

# Projektziel

Ziel dieses Projekts ist die Analyse und Bewertung verschiedener
Traffic-Engineering-Strategien hinsichtlich ihrer Auswirkungen auf

- Durchsatz
- Ende-zu-Ende-Latenz
- Paketverlust
- Jitter

Hierzu wird eine Spine-Leaf-Topologie in ns-3 modelliert und unter
verschiedenen Lastbedingungen simuliert.

---

# Forschungsfrage

> Welchen Einfluss haben verschiedene Traffic-Engineering-Strategien
> auf die Leistungsfähigkeit eines Cloud-Rechenzentrums hinsichtlich
> Latenz, Durchsatz, Jitter und Paketverlust?

---

# Verwendete Technologien

- ns-3
- Python
- pandas
- matplotlib
- FlowMonitor
- CSV-Auswertung

---

# Topologie

Die Simulation bildet ein vereinfachtes Spine-Leaf-Rechenzentrum nach.

```
               Spine 0
              /       \
             /         \
         Leaf 0 ----- Leaf 1
          /   \       /   \
      Host0 Host1 Host2 Host3
```

Eigenschaften

- 2 Spine-Switches
- 2 Leaf-Switches
- 4 Hosts
- vollständige Spine-Leaf-Vernetzung
- 10 Gbit/s Punkt-zu-Punkt-Verbindungen
- 2 ms Linkverzögerung

---

# Implementierte Routingstrategien

## 1. Standard Routing

Verwendung des Standard-Routings von ns-3.

Dient als Referenz (Baseline) für alle weiteren Strategien.

---

## 2. Equal Cost Multi Path (ECMP)

Verteilung von Datenströmen auf mehrere gleichwertige Pfade.

Ziel:

- bessere Lastverteilung
- höhere Ausfallsicherheit
- Vermeidung einzelner Engpässe

---

## 3. Static Routing

Feste Zuordnung einzelner Datenströme auf definierte Spine-Switches.

Dadurch lässt sich untersuchen, welchen Einfluss eine gezielte
Pfadwahl auf die Netzwerkleistung besitzt.

---

# Lastszenarien

## Szenario 1 – Baseline

Ein einzelner Datenstrom

```
Host0  --->  Host3
```

100 Mbit/s

---

## Szenario 2 – Mittlere Last

Vier gleichzeitige Datenströme

```
Host0 ---> Host3
Host1 ---> Host2
Host2 ---> Host1
Host3 ---> Host0
```

je 100 Mbit/s

---

## Szenario 3 – Hohe Last

Vier gleichzeitige Datenströme

je 2 Gbit/s

---

## Szenario 4 – Überlast

Vier gleichzeitige Datenströme

je 12 Gbit/s

Dadurch werden einzelne Netzwerkverbindungen gezielt überlastet.

---

# Gemessene Kennzahlen

Für jeden Datenstrom werden folgende Messgrößen bestimmt:

- gesendete Pakete
- empfangene Pakete
- verlorene Pakete
- Paketverlust
- Gesamtdurchsatz
- mittlere Ende-zu-Ende-Latenz
- mittlerer Jitter

---

# Projektstruktur

```
cloud-datacenter-traffic-engineering
│
├── simulation
│   └── datacenter.py
│
├── scripts
│   ├── run_experiments.py
│   └── evaluate_results.py
│
├── results
│   ├── results_standard_...
│   ├── results_ecmp_...
│   └── results_static_...
│
├── evaluation
│   ├── experiment_summary.csv
│   ├── throughput_comparison.png
│   ├── delay_comparison.png
│   ├── packet_loss_comparison.png
│   └── jitter_comparison.png
│
├── README.md
├── requirements.txt
└── .gitignore
```

---

# Voraussetzungen

Benötigt werden

- Linux oder WSL
- ns-3 mit aktivierten Python-Bindings
- Python 3
- pandas
- matplotlib

Python-Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

---

# Einzelne Simulation starten

Wechsel in das ns-3-Verzeichnis

```bash
cd ~/ns-3-dev
```

Simulation starten

```bash
./ns3 run "/home/edbloom/cloud-datacenter-traffic-engineering/simulation/datacenter.py STANDARD 1"
```

---

## Routingstrategien

```
STANDARD
ECMP
STATIC
```

---

## Szenarien

```
1 = Baseline

2 = Mittlere Last

3 = Hohe Last

4 = Überlast
```

---

# Alle Experimente automatisch ausführen

Im Projektverzeichnis

```bash
cd ~/cloud-datacenter-traffic-engineering
```

Anschließend

```bash
python3 scripts/run_experiments.py
```

Es werden automatisch alle Kombinationen aus

- Routingstrategie
- Lastszenario

durchgeführt.

Insgesamt entstehen

```
3 Routingstrategien

×

4 Szenarien

=

12 Simulationen
```

---

# Ergebnisse auswerten

```bash
python3 scripts/evaluate_results.py
```

Das Skript

- liest alle CSV-Dateien ein
- prüft die Vollständigkeit der Experimente
- erstellt eine Gesamtauswertung
- erzeugt Vergleichsdiagramme

---

# Erzeugte Dateien

## Ergebnisse

```
results/
```

Enthält alle Messergebnisse jeder Simulation.

---

## Auswertung

```
evaluation/
```

Enthält

- experiment_summary.csv
- throughput_comparison.png
- delay_comparison.png
- packet_loss_comparison.png
- jitter_comparison.png

---

# Aktueller Entwicklungsstand

Bereits umgesetzt

- ✔ Spine-Leaf-Topologie
- ✔ IPv4-Adressierung
- ✔ Standard Routing
- ✔ ECMP
- ✔ Static Routing
- ✔ vier Lastszenarien
- ✔ automatisierte Versuchsdurchführung
- ✔ CSV-Ausgabe
- ✔ automatische Auswertung
- ✔ Diagrammerzeugung

Geplante Erweiterungen

- Adaptive Routing
- Ausfallszenarien
- größere Topologien
- Integration weiterer Traffic-Engineering-Verfahren

---

# Autor

Laurin Krüger

Projekt 3
