# Cloud Datacenter Traffic Engineering

Simulation und Auswertung verschiedener Traffic-Engineering-Strategien in einer Spine-Leaf-Topologie mit **ns-3** und **Python**.

Das Projekt untersucht verschiedene Routingstrategien unter mehreren Lastszenarien und vergleicht deren Auswirkungen auf Durchsatz, Latenz, Paketverlust und Jitter.

## Forschungsfrage

**Welchen Einfluss haben verschiedene Traffic-Engineering-Strategien auf die Leistungsfähigkeit eines Cloud-Rechenzentrums hinsichtlich Latenz, Durchsatz und Paketverlust?**

## Datacenter-Topologie

Für die Simulation wird eine Spine-Leaf-Topologie verwendet.

Die aktuelle Topologie besteht aus:

- 4 Spine-Knoten
- 4 Leaf-Knoten
- 16 Hosts
- 4 Hosts pro Leaf
- vollständiger Verbindung zwischen allen Spines und Leaves
- 16 Spine-Leaf-Links
- 16 Leaf-Host-Links
- 10-Gbit/s-Links
- 2-ms-Linkverzögerung

Jeder Leaf-Switch ist mit jedem der vier Spine-Switches verbunden. Dadurch existieren zwischen unterschiedlichen Leaves mehrere gleichwertige Pfade.

Die gegenüber der ursprünglichen kleinen Testtopologie erweiterte Struktur ermöglicht eine realistischere Untersuchung verschiedener Traffic-Engineering-Strategien.

## Routingstrategien

Es werden vier Routingstrategien untersucht.

### 1. Standard Routing

Das Standard-Routing verwendet die von ns-3 erzeugten globalen IPv4-Routingtabellen.

Die ECMP-Zufallsauswahl ist für diese Strategie deaktiviert.

Auf diese Weise dient die Strategie als Referenz für die weiteren Routingverfahren.

### 2. ECMP

ECMP steht für **Equal-Cost Multi-Path Routing**.

Existieren mehrere gleichwertige Pfade zwischen Quelle und Ziel, kann ns-3 unterschiedliche Pfade über die verfügbaren Spine-Knoten auswählen.

Für diese Strategie wird die ns-3-Eigenschaft `RandomEcmpRouting` aktiviert.

### 3. Statisches Flow-Pinning

Beim statischen Flow-Pinning wird jedem Datenstrom vor Beginn der Simulation ein fester Spine-Pfad zugewiesen.

Für die vier Hauptdatenströme werden unterschiedliche Spines verwendet:

- Host 0 → Host 15 über Spine 0
- Host 4 → Host 11 über Spine 1
- Host 8 → Host 3 über Spine 2
- Host 12 → Host 7 über Spine 3

Dadurch wird eine deterministische Verteilung der Datenströme auf die verfügbaren Pfade erreicht.

### 4. Lastabhängiges Routing

Zusätzlich wurde eine lastabhängige Routingstrategie implementiert.

Bei der Pfadzuweisung wird für jeden Datenstrom die bereits zugewiesene angebotene Last der verfügbaren Spine-Pfade betrachtet.

Der neue Datenstrom wird dem Spine mit der aktuell geringsten zugewiesenen Last zugeordnet.

Dadurch entsteht eine einfache lastorientierte Verteilung der Flows auf die vorhandenen Spine-Pfade.

Wichtig ist die Abgrenzung zu vollständig dynamischem Routing: Die Pfadentscheidung erfolgt in der aktuellen Implementierung bei der Konfiguration der Datenströme vor der eigentlichen Verkehrsübertragung. Bereits laufende Flows werden während der Simulation nicht kontinuierlich auf andere Pfade verschoben.

## Lastszenarien

Für jede Routingstrategie werden vier Lastszenarien untersucht.

### Szenario 1 – Baseline

Ein einzelner Datenstrom:

- Host 0 → Host 15
- 100 Mbit/s

### Szenario 2 – Mittlere Last

Vier Datenströme:

- Host 0 → Host 15
- Host 4 → Host 11
- Host 8 → Host 3
- Host 12 → Host 7

Jeder Flow erzeugt:

- 100 Mbit/s

Gesamte angebotene Last:

- 400 Mbit/s

### Szenario 3 – Hohe Last

Die gleichen vier Datenströme werden verwendet.

Jeder Flow erzeugt:

- 2 Gbit/s

Gesamte angebotene Last:

- 8 Gbit/s

### Szenario 4 – Überlast

Die gleichen vier Datenströme werden verwendet.

Jeder Flow erzeugt:

- 12 Gbit/s

Gesamte angebotene Last:

- 48 Gbit/s

Dieses Szenario erzeugt gezielt eine Überlastsituation, da die angebotene Datenrate eines einzelnen Flows bereits über der konfigurierten Link-Datenrate von 10 Gbit/s liegt.

## Experimentaufbau

Es werden alle Kombinationen aus Routingstrategie und Lastszenario untersucht.

| Routingstrategie | Szenario 1 | Szenario 2 | Szenario 3 | Szenario 4 |
|---|---:|---:|---:|---:|
| Standard | ✓ | ✓ | ✓ | ✓ |
| ECMP | ✓ | ✓ | ✓ | ✓ |
| Statisches Flow-Pinning | ✓ | ✓ | ✓ | ✓ |
| Lastabhängig | ✓ | ✓ | ✓ | ✓ |

Damit werden insgesamt

**4 Routingstrategien × 4 Lastszenarien = 16 Simulationen**

durchgeführt.

## Simulationszeiten

Für alle Routingstrategien und Szenarien werden identische Simulationszeiten verwendet:

- Start der Server: 0,5 s
- Start der Clients: 1,0 s
- Ende des Datenverkehrs: 3,0 s
- Ende der Simulation: 4,0 s

Der eigentliche Datenverkehr läuft damit für zwei Sekunden.

Die vergleichsweise kurze Simulationsdauer reduziert insbesondere bei Datenraten im Gbit/s-Bereich die Anzahl der von ns-3 zu verarbeitenden Pakete und damit die Rechenzeit.

Da für alle untersuchten Routingstrategien und Lastszenarien identische Zeitparameter verwendet werden, bleiben die Versuche untereinander vergleichbar.

## Messgrößen

Für jeden Datenstrom werden unter anderem folgende Größen mit dem ns-3 FlowMonitor erfasst:

- gesendete Pakete
- empfangene Pakete
- verlorene Pakete
- Paketverlust in Prozent
- Durchsatz in Mbit/s
- mittlere Ende-zu-Ende-Latenz in ms
- mittlerer Jitter in ms

Die Einzelwerte werden nach jeder Simulation in einer CSV-Datei gespeichert.

## Aktuelle Ergebnisse

Die 16 Simulationen wurden für alle Kombinationen aus Routingstrategie und Lastszenario durchgeführt.

In den Szenarien 1 bis 3 tritt bei der aktuellen Konfiguration kein Paketverlust auf.

Im Überlastszenario wird die Kapazitätsgrenze sichtbar. Bei einer angebotenen Last von 12 Gbit/s pro Flow wird ein Durchsatz von ungefähr 9,94 Gbit/s pro Flow erreicht. Gleichzeitig steigen Paketverlust und Latenz deutlich an.

Die vier Routingstrategien liefern in den aktuell verwendeten symmetrischen Verkehrsszenarien sehr ähnliche beziehungsweise identische Leistungswerte. Dies ist bei der Interpretation zu berücksichtigen: Die Topologie und die Hauptdatenströme sind symmetrisch aufgebaut, sodass die verschiedenen Strategien in diesen Szenarien zu einer gleichmäßigen Pfadnutzung führen können.

Die Implementierungen unterscheiden sich dennoch in der Art ihrer Pfadauswahl und können deshalb separat untersucht und erweitert werden.

## Automatische Auswertung

Das Skript `evaluate_results.py` liest die erzeugten CSV-Dateien ein und erstellt eine Zusammenfassung aller Experimente.

Dabei werden unter anderem folgende aggregierte Größen berechnet:

- Gesamtdurchsatz
- mittlere Latenz
- Paketverlust
- mittlerer Jitter
- Anzahl der Flows

Die Auswertung prüft außerdem, ob alle erwarteten 16 Strategie-Szenario-Kombinationen vorhanden sind.

## Erzeugte Diagramme

Die Auswertung erzeugt Vergleichsdiagramme für:

- Durchsatz
- Latenz
- Paketverlust
- Jitter

Die Diagramme werden sowohl als **PNG** als auch als **PDF** gespeichert.

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
│   ├── results_standard_*.csv
│   ├── results_ecmp_*.csv
│   ├── results_static_*.csv
│   └── results_adaptive_*.csv
│
└── evaluation/
    ├── experiment_summary.csv
    ├── throughput_comparison.png
    ├── throughput_comparison.pdf
    ├── delay_comparison.png
    ├── delay_comparison.pdf
    ├── packet_loss_comparison.png
    ├── packet_loss_comparison.pdf
    ├── jitter_comparison.png
    └── jitter_comparison.pdf
```

## Voraussetzungen

Für die Durchführung der Simulationen werden benötigt:

- Linux oder WSL
- ns-3
- Python 3
- aktivierte ns-3-Python-Bindings
- cppyy
- pandas
- matplotlib

Die benötigten Python-Abhängigkeiten sind zusätzlich in `requirements.txt` dokumentiert.

## Installation

Repository klonen:

```bash
git clone <URL-DES-REPOSITORIES>
cd cloud-datacenter-traffic-engineering
```

Python-Abhängigkeiten können anschließend installiert werden:

```bash
pip install -r requirements.txt
```

Für die eigentliche Simulation wird zusätzlich eine funktionierende ns-3-Installation mit Python-Unterstützung benötigt.

## Verwendung mit ns-3

Die Simulation wurde während der Entwicklung innerhalb des ns-3-Projektverzeichnisses ausgeführt.

Dazu können die Python-Dateien beispielsweise in den Python-Arbeitsbereich der lokalen ns-3-Installation kopiert werden.

Beispiel:

```bash
cp simulation/datacenter.py ~/ns-3-dev/python/datacenter.py
cp scripts/run_experiments.py ~/ns-3-dev/python/run_experiments.py
cp scripts/evaluate_results.py ~/ns-3-dev/python/evaluate_results.py
```

Anschließend in das ns-3-Verzeichnis wechseln:

```bash
cd ~/ns-3-dev
```

## Einzelne Simulation starten

Das allgemeine Schema lautet:

```bash
./ns3 run "python/datacenter.py ROUTING SZENARIO"
```

Beispiel für Standard-Routing und Szenario 1:

```bash
./ns3 run "python/datacenter.py STANDARD 1"
```

Beispiel für ECMP und Szenario 3:

```bash
./ns3 run "python/datacenter.py ECMP 3"
```

Beispiel für statisches Flow-Pinning und Szenario 2:

```bash
./ns3 run "python/datacenter.py STATIC 2"
```

Beispiel für lastabhängiges Routing und Szenario 4:

```bash
./ns3 run "python/datacenter.py ADAPTIVE 4"
```

### Verfügbare Routingstrategien

```text
STANDARD
ECMP
STATIC
ADAPTIVE
```

### Verfügbare Szenarien

```text
1 = Baseline
2 = Mittlere Last
3 = Hohe Last
4 = Überlast
```

## Alle Experimente ausführen

Aus dem ns-3-Hauptverzeichnis:

```bash
cd ~/ns-3-dev
python3 python/run_experiments.py
```

Das Skript führt automatisch alle 16 Kombinationen aus Routingstrategie und Lastszenario nacheinander aus.

## Ergebnisse auswerten

Nachdem alle Simulationen abgeschlossen wurden:

```bash
cd ~/ns-3-dev
python3 python/evaluate_results.py
```

Die Auswertung kontrolliert die vorhandenen Ergebnisdateien und erzeugt anschließend die zusammengefasste CSV-Datei sowie die Vergleichsdiagramme.

## Reproduzierbarkeit

Für einen fairen Vergleich werden alle Routingstrategien mit derselben:

- Topologie
- Link-Datenrate
- Link-Verzögerung
- Paketgröße
- Simulationsdauer
- Verkehrskonfiguration
- Messmethodik

untersucht.

Lediglich die Routingstrategie wird zwischen den jeweiligen Vergleichsläufen verändert.

Dadurch können Unterschiede in den Messergebnissen gezielt auf die untersuchte Routingkonfiguration zurückgeführt werden.

## Hinweise zur Interpretation

Die aktuellen Hauptszenarien verwenden eine symmetrische Topologie und weitgehend symmetrische Datenströme.

Daher können verschiedene Routingstrategien trotz unterschiedlicher Pfadauswahl sehr ähnliche Messergebnisse erzeugen.

Insbesondere ist das implementierte lastabhängige Routing als einfache lastorientierte Flow-Zuweisung zu verstehen. Es handelt sich nicht um ein kontinuierliches dynamisches Re-Routing bereits laufender Datenströme.

Die Ergebnisse sollten daher immer im Zusammenhang mit der verwendeten Topologie, den angebotenen Lasten und der konkreten Routingimplementierung interpretiert werden.