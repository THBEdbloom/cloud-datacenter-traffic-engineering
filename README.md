# Cloud Datacenter Traffic Engineering

Simulation und Auswertung verschiedener Traffic-Engineering-Strategien in einer Spine-Leaf-Datacenter-Topologie mit ns-3 und Python.

## Forschungsfrage

**Welchen Einfluss haben verschiedene Traffic-Engineering-Strategien auf die Leistungsfähigkeit eines Cloud-Rechenzentrums hinsichtlich Latenz, Durchsatz und Paketverlust?**

Untersucht werden insbesondere Situationen, in denen mehrere gleichwertige Pfade zwischen Leaf-Switches existieren und sich unterschiedliche Verfahren zur Pfadauswahl auf die Verteilung der Netzwerklast auswirken können.

## Datacenter-Topologie

Die simulierte Spine-Leaf-Topologie besteht aus:

- 4 Spine-Knoten
- 4 Leaf-Knoten
- 16 Hosts
- 4 Hosts pro Leaf
- vollständiger Verbindung zwischen allen Spines und Leaves
- 16 Spine-Leaf-Links
- 16 Leaf-Host-Links
- 10-Gbit/s-Links
- 2-ms-Linkverzögerung

Jeder Leaf-Switch ist mit allen vier Spine-Switches verbunden. Zwischen Hosts an unterschiedlichen Leaves existieren dadurch mehrere gleichwertige Pfade.

## Routingstrategien

Vier Routingstrategien werden miteinander verglichen.

### STANDARD

Standardmäßiges globales IPv4-Routing von ns-3. Die ECMP-Zufallsauswahl ist deaktiviert. Diese Variante dient als Referenz.

### ECMP

Equal-Cost Multi-Path Routing. Für gleichwertige Routen wird die ns-3-Eigenschaft `RandomEcmpRouting` verwendet, sodass unterschiedliche Datenströme auf verschiedene gleichwertige Pfade verteilt werden können.

### STATIC

Statisches Flow-Pinning. Datenströme werden explizit bestimmten Spine-Pfaden zugeordnet. Die Pfadwahl bleibt während des jeweiligen Flows unverändert.

### ADAPTIVE

Lastabhängige Pfadauswahl. Bei der Zuordnung eines Flows wird die bereits zugewiesene angebotene Last der verfügbaren Spine-Pfade berücksichtigt und ein möglichst wenig belasteter Pfad ausgewählt.

Für das dynamische Hotspot-Szenario enthält die Implementierung zusätzlich eine zeitabhängige Anpassung der Pfadzuordnung. Die Strategie ist dennoch als experimenteller Ansatz zu verstehen und nicht mit einem vollständigen produktiven dynamischen Traffic-Engineering-System gleichzusetzen.

## Traffic-Szenarien

Es werden acht Szenarien untersucht.

### Szenario 1 – Baseline

Ein einzelner Flow mit 100 Mbit/s dient als Referenzfall bei sehr geringer Netzlast.

### Szenario 2 – Mittlere Last

Vier Datenströme mit jeweils 100 Mbit/s erzeugen insgesamt 400 Mbit/s angebotene Last.

### Szenario 3 – Hohe Last

Vier Datenströme mit jeweils 2 Gbit/s erzeugen insgesamt 8 Gbit/s angebotene Last.

### Szenario 4 – Überlast

Vier Datenströme mit jeweils 12 Gbit/s erzeugen eine gezielte Überlastsituation. Die angebotene Rate eines einzelnen Flows liegt bereits über der Linkkapazität von 10 Gbit/s.

### Szenario 5 – Hotspot

Mehrere Datenströme erzeugen eine konzentrierte Belastung bestimmter Pfade. Dieses Szenario macht Unterschiede zwischen einfacher Pfadwahl und Lastverteilung deutlich sichtbar.

### Szenario 6 – Asymmetrische Last

Datenströme mit unterschiedlicher angebotener Last erzeugen eine ungleichmäßige Verkehrssituation. Dadurch können neben Durchsatz, Paketverlust und Latenz auch Unterschiede in der Fairness sichtbar werden.

### Szenario 7 – Dynamischer Hotspot

Das Hotspot-Muster wird zeitabhängig verändert. Dieses Szenario untersucht insbesondere das Verhalten der Routingstrategien bei einer dynamischen Lastsituation.

### Szenario 8 – Linkausfall

Während der laufenden Simulation fällt gezielt ein Spine-Leaf-Link aus. Das Szenario untersucht, wie die Routingstrategien auf eine während des Datenverkehrs auftretende Pfadunterbrechung reagieren und in welchem Umfang Durchsatz, Paketverlust und Latenz beeinflusst werden.

## Experimentaufbau

Für alle acht Szenarien werden die vier Routingstrategien untersucht.

Die Szenarien 1 bis 4 dienen hauptsächlich als Basis-, Last- und Überlastreferenzen und werden jeweils einmal ausgeführt.

Für die Szenarien 5 bis 8 werden jeweils drei Runs durchgeführt.

Damit umfasst der gespeicherte finale Datensatz:

- Szenarien 1–4: 4 Strategien × 4 Szenarien × 1 Run = 16 Experimente
- Szenarien 5–8: 4 Strategien × 4 Szenarien × 3 Runs = 48 Experimente
- insgesamt: **64 Experimente**

Der Seed bleibt für die Versuchsserie auf `1`. Die Run-Nummer wird über den ns-3-Zufallszahlengenerator konfiguriert.

## Hinweis zu den Wiederholungen

Die aktuelle Simulation ist weitgehend deterministisch. Daher liefern die Wiederholungen in den Szenarien 5 bis 8 identische oder nahezu identische Messergebnisse.

Die Runs dienen damit vor allem der Überprüfung der Reproduzierbarkeit. Sie stellen bei identischen Ergebnissen keine unabhängigen statistischen Stichproben dar.

Aus diesem Grund werden Mittelwert, Standardabweichung, Minimum und Maximum dokumentiert, aber aus identischen deterministischen Wiederholungen keine inferenzstatistischen Konfidenzintervalle abgeleitet.

## Simulationszeiten

Für die Versuche werden einheitliche grundlegende Simulationsparameter verwendet. Der eigentliche Datenverkehr läuft innerhalb eines begrenzten Simulationszeitraums, um auch Gbit/s-Szenarien mit vertretbarer Rechenzeit untersuchen zu können.

Die konkreten Start- und Stopzeiten der einzelnen Flows sind in `simulation/datacenter.py` definiert und Bestandteil der jeweiligen Szenariokonfiguration.

## Messgrößen

Der ns-3 FlowMonitor erfasst für die Datenströme unter anderem:

- gesendete Pakete
- empfangene Pakete
- verlorene Pakete
- Paketverlust in Prozent
- Durchsatz in Mbit/s
- mittlere Ende-zu-Ende-Latenz in ms
- mittleren Jitter in ms

Zusätzlich werden für jeden Versuch aggregierte Kennzahlen berechnet:

- Gesamtdurchsatz
- Gesamtpaketverlust
- gewichtete mittlere Latenz
- gewichteter mittlerer Jitter
- Jain Fairness Index

## Auswertung

`scripts/evaluate_results.py` verarbeitet die erzeugten Summary-Dateien und prüft zunächst die erwartete Versuchsmatrix.

Anschließend werden die Ergebnisse nach Routingstrategie und Szenario zusammengefasst.

Die Auswertung erzeugt insbesondere:

- `all_experiment_results.csv` – alle eingelesenen Versuchsergebnisse
- `experiment_statistics.csv` – aggregierte Statistik je Strategie und Szenario
- `relative_improvement_vs_standard.csv` – relative Veränderungen gegenüber STANDARD

Für wiederholte Experimente werden Mittelwert, Standardabweichung, Minimum und Maximum ausgegeben.

## Diagramme

Die Ergebnisse der Basisszenarien und der Traffic-Engineering-Szenarien werden getrennt visualisiert.

Für folgende Kennzahlen werden Diagramme erzeugt:

- Durchsatz
- Paketverlust
- Latenz
- Jitter
- Jain Fairness Index

Dabei entstehen jeweils getrennte Darstellungen für:

- Basisszenarien 1–4
- Traffic-Engineering-Szenarien 5–7
- Ausfallszenario 8

Die Diagramme werden als PNG und PDF gespeichert.

## Zentrale Beobachtungen

Die Ergebnisse zeigen drei unterschiedliche Bereiche.

In den Szenarien 1 bis 3 ist die Netzlast niedrig genug, sodass alle Routingstrategien praktisch identische Ergebnisse erzielen.

Szenario 4 erzeugt eine Überlast, die bereits durch die angebotene Datenrate der einzelnen Flows verursacht wird. Entsprechend können die verschiedenen Pfadstrategien diese grundlegende Kapazitätsüberschreitung nicht verhindern.

Die Szenarien 5 bis 7 sind für den Vergleich der Traffic-Engineering-Verfahren besonders aussagekräftig. Bei Hotspot-, asymmetrischen und dynamischen Verkehrsmustern zeigen sich deutliche Unterschiede zwischen STANDARD beziehungsweise statischem Routing und den Verfahren, die mehrere Pfade besser ausnutzen.

Szenario 8 ergänzt die Untersuchung um einen Linkausfall während der laufenden Simulation. Dadurch kann zusätzlich bewertet werden, wie robust die verschiedenen Routingstrategien auf eine Pfadunterbrechung reagieren.

Die Resultate müssen immer im Zusammenhang mit der konkreten Topologie, der Verkehrsmatrix und der implementierten Routinglogik interpretiert werden.

## Projektstruktur

```text
cloud-datacenter-traffic-engineering/
│
├── README.md
├── requirements.txt
│
├── simulation/
│   └── datacenter.py
│
├── scripts/
│   ├── run_experiments.py
│   └── evaluate_results.py
│
├── results/
│   ├── results_*_seed_*_run_*.csv
│   └── summary_*_seed_*_run_*.csv
│
└── evaluation/
    ├── all_experiment_results.csv
    ├── experiment_statistics.csv
    ├── relative_improvement_vs_standard.csv
    ├── throughput_basis.{png,pdf}
    ├── throughput_traffic_engineering.{png,pdf}
    ├── delay_basis.{png,pdf}
    ├── delay_traffic_engineering.{png,pdf}
    ├── packet_loss_basis.{png,pdf}
    ├── packet_loss_traffic_engineering.{png,pdf}
    ├── jitter_basis.{png,pdf}
    ├── jitter_traffic_engineering.{png,pdf}
    ├── fairness_basis.{png,pdf}
    ├── fairness_traffic_engineering.{png,pdf}
    ├── throughput_failure.{png,pdf}
    ├── delay_failure.{png,pdf}
    ├── packet_loss_failure.{png,pdf}
    ├── jitter_failure.{png,pdf}
    └── fairness_failure.{png,pdf}
```

FlowMonitor-XML-Dateien, Routingtabellen und Logdateien werden nicht im Repository versioniert, da sie automatisch erzeugt werden können und für die zentrale Ergebnisanalyse nicht erforderlich sind.

## Voraussetzungen

Benötigt werden:

- Linux oder WSL
- ns-3 mit Python-Unterstützung
- Python 3
- cppyy
- pandas
- matplotlib

Die Python-Abhängigkeiten der Auswertung sind in `requirements.txt` aufgeführt.

## Verwendung mit ns-3

Die Simulationsskripte werden während der Entwicklung im ns-3-Projektverzeichnis ausgeführt.

Beispiel:

```bash
cp simulation/datacenter.py ~/ns-3-dev/python/datacenter.py
cp scripts/run_experiments.py ~/ns-3-dev/python/run_experiments.py
cp scripts/evaluate_results.py ~/ns-3-dev/python/evaluate_results.py
cd ~/ns-3-dev
```

### Einzelnes Experiment

Allgemeines Schema:

```bash
./ns3 run "python/datacenter.py STRATEGY SCENARIO [SEED] [RUN]"
```

Beispiel:

```bash
./ns3 run "python/datacenter.py ECMP 5 1 1"
```

Verfügbare Strategien:

```text
STANDARD
ECMP
STATIC
ADAPTIVE
```

Verfügbare Szenarien:

```text
1 = Baseline
2 = Mittlere Last
3 = Hohe Last
4 = Überlast
5 = Hotspot
6 = Asymmetrische Last
7 = Dynamischer Hotspot
8 = Linkausfall
```

### Experimentserie

Die gewünschte Versuchsmatrix wird in `run_experiments.py` konfiguriert.

Ausführung:

```bash
cd ~/ns-3-dev
python3 python/run_experiments.py
```

### Ergebnisse auswerten

```bash
cd ~/ns-3-dev
python3 python/evaluate_results.py
```

## Reproduzierbarkeit

Für die Vergleichsläufe werden Topologie, Linkparameter, Paketgröße, Simulationskonfiguration und Messmethodik konstant gehalten. Die Routingstrategie bildet die zentrale experimentelle Variable.

Seed und Run-Nummer werden in den Ergebnisdateien gespeichert. Dadurch lässt sich die jeweilige Simulationskonfiguration eindeutig nachvollziehen.

Die gespeicherten CSV-Dateien ermöglichen außerdem eine erneute Auswertung, ohne sämtliche ns-3-Simulationen erneut durchführen zu müssen.

## Wissenschaftliche Einordnung

Die Simulation bildet ein kontrolliertes Modell einer Spine-Leaf-Datacenter-Topologie ab. Die Ergebnisse sind daher als Vergleich der implementierten Routingstrategien innerhalb dieser Modellannahmen zu interpretieren und nicht als allgemeiner Leistungsnachweis für reale Produktionsnetzwerke.

Insbesondere die Ergebnisse der Hotspot-, asymmetrischen und dynamischen Lastszenarien dienen dazu, die Auswirkungen unterschiedlicher Pfadwahlverfahren unter gezielt erzeugten Engpasssituationen zu untersuchen.