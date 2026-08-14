"""
Analyse von Traffic-Engineering-Strategien
in einem Spine-Leaf-Rechenzentrum mit ns-3.

Projekt 3

Autor:
Laurin Krüger

Diese Simulation dient zur Untersuchung verschiedener
Traffic-Engineering-Strategien unter unterschiedlichen
Netzwerklast-Szenarien.

Implementierte Routingstrategien:
- Standard Routing
- ECMP
- Static Routing

Implementierte Szenarien:
1 Baseline
2 Mittlere Last
3 Hohe Last
4 Überlast
"""

from ns import ns
import csv
import sys

# =========================================================
# Datacenter-Topologie
#
# Die Simulation verwendet eine Spine-Leaf-Architektur.
#
# 4 Spine-Switches
# 4 Leaf-Switches
# 16 Hosts
#
# Jeder Leaf ist mit jedem Spine verbunden.
# An jedem Leaf befinden sich vier Hosts.
# =========================================================

NUM_SPINES = 4
NUM_LEAVES = 4
NUM_HOSTS = 16

LINK_RATE = "10Gbps"
LINK_DELAY = "2ms"

SERVER_HOST_INDEX = 3
CLIENT_HOST_INDEX = 0
SERVER_PORT = 9000
FIRST_SPINE_INTERFACE = 1

# Größe eines UDP-Pakets
PACKET_SIZE_BYTES = 1024

# OnOff-Zeiten:
# Der Sender bleibt während des gesamten Versuchs eingeschaltet.
ON_TIME_SECONDS = 1.0
OFF_TIME_SECONDS = 0.0

# =========================================================
# Simulationszeiten
#
# Der eigentliche Datenverkehr läuft für zwei Sekunden.
# Für alle Routingstrategien und Lastszenarien werden
# identische Start-, Mess- und Endzeiten verwendet.
#
# Die verkürzte Simulationsdauer reduziert insbesondere
# bei hohen Datenraten die Anzahl der zu verarbeitenden
# Pakete erheblich, ohne die angebotene Last zu verändern.
# =========================================================

SERVER_START = 0.5
CLIENT_START = 1.0
CLIENT_STOP = 3.0
SIMULATION_END = 4.0


# =========================================================
# Dynamisches lastabhängiges Routing
#
# Das adaptive Routing überprüft während der Simulation
# regelmäßig die Auslastung der Spine-Leaf-Pfade.
#
# Ein Pfadwechsel erfolgt nur, wenn der alternative Pfad
# ausreichend geringer belastet ist. Dadurch werden
# unnötige häufige Routingwechsel vermieden.
# =========================================================

ADAPTIVE_INTERVAL = 0.1       # Messintervall in Sekunden
ADAPTIVE_HYSTERESIS = 0.15    # mindestens 15 % Verbesserung

# Ein lastbedingter Pfadwechsel wird nur durchgeführt,
# wenn die Queue-Belegung des alternativen Pfades
# zusätzlich mindestens 4 KiB geringer ist.
#
# Diese absolute Schwelle verhindert Routing-Oszillationen
# aufgrund sehr kleiner Queue-Unterschiede.
# Ein nicht mehr verfügbarer Pfad ist davon ausgenommen:
# Bei einem Linkausfall darf weiterhin sofort auf einen
# verfügbaren alternativen Pfad gewechselt werden.
ADAPTIVE_MIN_QUEUE_IMPROVEMENT_BYTES = 4096


# =========================================================
# SIMULATIONSKONFIGURATION
#
# Für eine Simulation müssen normalerweise nur zwei
# Parameter angepasst werden:
#
#   ROUTING_STRATEGY
#   SCENARIO
#
# Alternativ können beide Werte auch über die
# Kommandozeile übergeben werden:
#
#   ./ns3 run "python/datacenter.py ECMP 3"
#
# Dies startet:
#   - Routingstrategie: ECMP
#   - Szenario 3 (Hohe Last)
# =========================================================


# =========================================================
# Routingstrategie
#
# STANDARD  -> Standard Routing (Referenz)
# ECMP      -> Equal Cost Multi Path
# STATIC    -> Statisches Flow-Pinning
# ADAPTIVE  -> Lastabhängiges Routing (geplant)
# =========================================================

ROUTING_STRATEGY = "STANDARD"


# =========================================================
# Szenario
#
# 1 -> Baseline
# 2 -> Mittlere Last
# 3 -> Hohe Last
# 4 -> Überlast
# =========================================================

SCENARIO = 1


# =========================================================
# Zufallssteuerung
#
# SEED bestimmt den grundlegenden Zufallszahlengenerator.
# RUN_NUMBER erzeugt reproduzierbare unabhängige
# Wiederholungen eines Experiments.
#
# Für Versuchsreihen bleibt SEED normalerweise konstant,
# während RUN_NUMBER variiert wird.
# =========================================================

SEED = 1
RUN_NUMBER = 1


# =========================================================
# Optionale Steuerung über Kommandozeilenparameter
#
# Beispiel:
#
#   ./ns3 run "python/datacenter.py STATIC 2"
#
# Dadurch werden die Standardwerte überschrieben.
# =========================================================

# Strategie und Szenario
if len(sys.argv) >= 3:
    ROUTING_STRATEGY = sys.argv[1].upper()
    SCENARIO = int(sys.argv[2])

# Optionaler Seed
if len(sys.argv) >= 4:
    SEED = int(sys.argv[3])

# Optionale Run-Nummer
if len(sys.argv) >= 5:
    RUN_NUMBER = int(sys.argv[4])

# Zu viele Parameter abfangen
if len(sys.argv) > 5:
    raise ValueError(
        "Verwendung: datacenter.py "
        "<STRATEGY> <SCENARIO> [SEED] [RUN]"
    )


# =========================================================
# Definition aller Szenarien
#
# Diese Werte müssen normalerweise NICHT geändert werden.
# =========================================================

SCENARIOS = {

    # =====================================================
    # Szenario 1 - Baseline
    #
    # Einfacher Referenzfall ohne relevante Netzwerklast.
    # =====================================================

    1: {
        "name": "Szenario 1 - Baseline",

        "flows": [
            {
                "source": 0,
                "destination": 15,
                "rate": "100Mbps",
                "start": 1.0,
                "stop": 3.0,
            },
        ],
    },

    # =====================================================
    # Szenario 2 - Mittlere Last
    #
    # Symmetrischer Datenverkehr mit geringer Last.
    # =====================================================

    2: {
        "name": "Szenario 2 - Mittlere Last",

        "flows": [
            {
                "source": 0,
                "destination": 15,
                "rate": "100Mbps",
                "start": 1.0,
                "stop": 3.0,
            },
            {
                "source": 4,
                "destination": 11,
                "rate": "100Mbps",
                "start": 1.0,
                "stop": 3.0,
            },
            {
                "source": 8,
                "destination": 3,
                "rate": "100Mbps",
                "start": 1.0,
                "stop": 3.0,
            },
            {
                "source": 12,
                "destination": 7,
                "rate": "100Mbps",
                "start": 1.0,
                "stop": 3.0,
            },
        ],
    },

    # =====================================================
    # Szenario 3 - Hohe Last
    #
    # Gleiches Kommunikationsmuster wie Szenario 2,
    # aber deutlich höhere angebotene Last.
    # =====================================================

    3: {
        "name": "Szenario 3 - Hohe Last",

        "flows": [
            {
                "source": 0,
                "destination": 15,
                "rate": "2Gbps",
                "start": 1.0,
                "stop": 3.0,
            },
            {
                "source": 4,
                "destination": 11,
                "rate": "2Gbps",
                "start": 1.0,
                "stop": 3.0,
            },
            {
                "source": 8,
                "destination": 3,
                "rate": "2Gbps",
                "start": 1.0,
                "stop": 3.0,
            },
            {
                "source": 12,
                "destination": 7,
                "rate": "2Gbps",
                "start": 1.0,
                "stop": 3.0,
            },
        ],
    },

    # =====================================================
    # Szenario 4 - Überlast
    #
    # Symmetrische Überlast als Belastungsgrenze.
    # Jeder angebotene Flow liegt oberhalb der
    # Kapazität eines einzelnen 10-Gbit/s-Pfades.
    # =====================================================

    4: {
        "name": "Szenario 4 - Überlast",

        "flows": [
            {
                "source": 0,
                "destination": 15,
                "rate": "12Gbps",
                "start": 1.0,
                "stop": 3.0,
            },
            {
                "source": 4,
                "destination": 11,
                "rate": "12Gbps",
                "start": 1.0,
                "stop": 3.0,
            },
            {
                "source": 8,
                "destination": 3,
                "rate": "12Gbps",
                "start": 1.0,
                "stop": 3.0,
            },
            {
                "source": 12,
                "destination": 7,
                "rate": "12Gbps",
                "start": 1.0,
                "stop": 3.0,
            },
        ],
    },

    # =====================================================
    # Szenario 5 - Hotspot
    #
    # Mehrere Sender kommunizieren gleichzeitig mit Hosts
    # am selben Ziel-Leaf.
    #
    # Dadurch entsteht eine konzentrierte Belastung in
    # Richtung Leaf 3. Das Szenario untersucht, wie gut
    # die Routingstrategien parallele Pfade nutzen können.
    # =====================================================

    5: {
        "name": "Szenario 5 - Hotspot",

        "flows": [
            {
                "source": 0,
                "destination": 12,
                "rate": "4Gbps",
                "start": 1.0,
                "stop": 3.0,
            },
            {
                "source": 4,
                "destination": 13,
                "rate": "4Gbps",
                "start": 1.0,
                "stop": 3.0,
            },
            {
                "source": 8,
                "destination": 14,
                "rate": "4Gbps",
                "start": 1.0,
                "stop": 3.0,
            },
            {
                "source": 1,
                "destination": 15,
                "rate": "4Gbps",
                "start": 1.0,
                "stop": 3.0,
            },
        ],
    },

    # =====================================================
    # Szenario 6 - Asymmetrische Last
    #
    # Vier unterschiedlich große Flows laufen gleichzeitig
    # in Richtung Leaf 3.
    #
    # Die ungleichen Datenraten prüfen, ob eine Strategie
    # nicht nur die Anzahl der Flows, sondern auch deren
    # angebotene Last sinnvoll verteilen kann.
    # =====================================================

    6: {
        "name": "Szenario 6 - Asymmetrische Last",

        "flows": [
            {
                "source": 2,
                "destination": 12,
                "rate": "8Gbps",
                "start": 1.0,
                "stop": 3.0,
            },
            {
                "source": 5,
                "destination": 13,
                "rate": "6Gbps",
                "start": 1.0,
                "stop": 3.0,
            },
            {
                "source": 9,
                "destination": 14,
                "rate": "3Gbps",
                "start": 1.0,
                "stop": 3.0,
            },
            {
                "source": 3,
                "destination": 15,
                "rate": "1Gbps",
                "start": 1.0,
                "stop": 3.0,
            },
        ],
    },

    # =====================================================
    # Szenario 7 - Dynamischer Hotspot
    #
    # Zunächst starten mehrere Datenströme mit moderater
    # Last. Während der laufenden Simulation kommen weitere
    # Datenströme hinzu.
    #
    # Dadurch verändert sich die Netzwerklast nach der
    # ursprünglichen Pfadwahl. Das Szenario untersucht,
    # ob eine adaptive Routingstrategie auf eine während
    # des Betriebs entstandene Lastverschiebung reagieren
    # kann.
    # =====================================================

    7: {
        "name": "Szenario 7 - Dynamischer Hotspot",

        "flows": [
            {
                "source": 0,
                "destination": 12,
                "rate": "4Gbps",
                "start": 1.0,
                "stop": 3.0,
            },
            {
                "source": 4,
                "destination": 13,
                "rate": "4Gbps",
                "start": 1.0,
                "stop": 3.0,
            },

            # Zusätzliche Last entsteht erst während
            # der laufenden Simulation.
            {
                "source": 8,
                "destination": 14,
                "rate": "4Gbps",
                "start": 1.3,
                "stop": 3.0,
            },
            {
                "source": 1,
                "destination": 15,
                "rate": "4Gbps",
                "start": 1.3,
                "stop": 3.0,
            },
        ],
    },

    # =====================================================
    # Szenario 8 - Linkausfall
    #
    # Mehrere Cross-Leaf-Flows laufen zunächst unter
    # normalen Bedingungen.
    #
    # Während der Simulation fällt die Verbindung
    # Spine0 <-> Leaf0 aus.
    #
    # Dadurch wird untersucht, wie die Routingstrategien
    # auf einen während des Betriebs auftretenden
    # Infrastrukturfehler reagieren.
    # =====================================================

    8: {
        "name": "Szenario 8 - Linkausfall",

        "flows": [
            {
                "source": 0,
                "destination": 15,
                "rate": "4Gbps",
                "start": 1.0,
                "stop": 4.0,
            },
            {
                "source": 1,
                "destination": 14,
                "rate": "4Gbps",
                "start": 1.0,
                "stop": 4.0,
            },
            {
                "source": 4,
                "destination": 13,
                "rate": "4Gbps",
                "start": 1.0,
                "stop": 4.0,
            },
            {
                "source": 8,
                "destination": 12,
                "rate": "4Gbps",
                "start": 1.0,
                "stop": 4.0,
            },
        ],

        "failure": {
            "spine": 0,
            "leaf": 0,
            "time": 2.0,
        },
    },
}


# =========================================================
# Statische Pfadzuordnung
#
# Diese Konfiguration wird ausschließlich von der
# Routingstrategie STATIC verwendet.
#
# Jedem Cross-Leaf-Datenstrom wird ein bestimmter
# Spine-Switch zugeordnet. Dadurch kann die Pfadwahl
# kontrolliert und reproduzierbar vorgegeben werden.
#
# Host-Verteilung:
#
# Leaf 0 -> Host 0  bis Host 3
# Leaf 1 -> Host 4  bis Host 7
# Leaf 2 -> Host 8  bis Host 11
# Leaf 3 -> Host 12 bis Host 15
#
# Format:
#
# (Quellhost, Zielhost): Spine-Index
#
# Spine 0 = erster Spine
# Spine 1 = zweiter Spine
# Spine 2 = dritter Spine
# Spine 3 = vierter Spine
# =========================================================

STATIC_FLOW_SPINES = {

    # Szenarien 1-4
    (0, 15): 0,
    (4, 11): 0,
    (8, 3): 1,
    (12, 7): 1,

    # Szenario 5 - Hotspot
    #
    # Bewusst feste und reproduzierbare Verteilung
    # der vier Hotspot-Flows auf alle vier Spines.
    (0, 12): 0,
    (4, 13): 1,
    (8, 14): 2,
    (1, 15): 3,

    # Szenario 6 - Asymmetrische Last
    #
    # Feste Pfade ohne Kenntnis der aktuellen Flow-Raten.
    # Dadurch können sich bei veränderter Last ungünstige
    # Konzentrationen auf einzelnen Pfaden ergeben.
    (2, 12): 0,
    (5, 13): 0,
    (9, 14): 1,
    (3, 15): 1,

    # Szenario 7 - Dynamischer Hotspot
    (0, 12): 0,
    (4, 13): 0,
    (8, 14): 0,
    (1, 15): 0,

    # Szenario 8 - Linkausfall
    #
    # Zwei Flows von Leaf0 werden bewusst über Spine0 geführt,
    # damit der konfigurierte Linkausfall diese statisch
    # gepinnten Pfade direkt betrifft.
    (1, 14): 0,
    (4, 13): 1,
    (8, 12): 2,
}


# =========================================================
# Aktives Szenario laden
#
# Ab hier muss normalerweise nichts mehr geändert werden.
# =========================================================

ACTIVE_SCENARIO = SCENARIOS[SCENARIO]

SCENARIO_NAME = ACTIVE_SCENARIO["name"]

TRAFFIC_FLOWS = ACTIVE_SCENARIO["flows"]

def validate_configuration() -> None:
    if NUM_SPINES < 1:
        raise ValueError("NUM_SPINES muss mindestens 1 sein.")
    if NUM_LEAVES < 1:
        raise ValueError("NUM_LEAVES muss mindestens 1 sein.")
    if NUM_HOSTS < NUM_LEAVES:
        raise ValueError("NUM_HOSTS muss mindestens so groß wie NUM_LEAVES sein.")
    if NUM_HOSTS % NUM_LEAVES != 0:
        raise ValueError("NUM_HOSTS muss ohne Rest durch NUM_LEAVES teilbar sein.")
    if not 0 <= CLIENT_HOST_INDEX < NUM_HOSTS:
        raise ValueError("CLIENT_HOST_INDEX liegt außerhalb des Host-Bereichs.")
    if not 0 <= SERVER_HOST_INDEX < NUM_HOSTS:
        raise ValueError("SERVER_HOST_INDEX liegt außerhalb des Host-Bereichs.")
    if CLIENT_HOST_INDEX == SERVER_HOST_INDEX:
        raise ValueError("Client und Server müssen unterschiedliche Hosts sein.")
    if CLIENT_STOP > SIMULATION_END:
        raise ValueError("CLIENT_STOP darf nicht nach SIMULATION_END liegen.")


def create_link(p2p: ns.PointToPointHelper, node_a, node_b):
    """
    Erstellt eine Punkt-zu-Punkt-Verbindung
    zwischen zwei Knoten.
    """
    return p2p.Install(node_a, node_b)


def assign_subnet(address_helper: ns.Ipv4AddressHelper, devices, subnet_number: int):
    """
    Vergibt ein eigenes /30-Subnetz
    für eine Punkt-zu-Punkt-Verbindung.
    """
    second_octet = subnet_number // 256
    third_octet = subnet_number % 256

    if second_octet > 255:
        raise ValueError("Zu viele Subnetze für den Adressbereich 10.0.0.0/8.")

    network = f"10.{second_octet}.{third_octet}.0"
    address_helper.SetBase(
        ns.Ipv4Address(network),
        ns.Ipv4Mask("255.255.255.252"),
    )
    return address_helper.Assign(devices)

def data_rate_to_bps(data_rate: str) -> float:
    """
    Wandelt eine Datenrate aus der Szenariokonfiguration in Bit/s um.

    Unterstützte Einheiten:
    - Kbps
    - Mbps
    - Gbps

    Die Umrechnung wird für die lastabhängige Pfadauswahl benötigt.
    """

    rate = data_rate.strip()

    if rate.endswith("Gbps"):
        return float(rate[:-4]) * 1_000_000_000.0

    if rate.endswith("Mbps"):
        return float(rate[:-4]) * 1_000_000.0

    if rate.endswith("Kbps"):
        return float(rate[:-4]) * 1_000.0

    raise ValueError(
        f"Nicht unterstützte Datenrate: {data_rate}"
    )

def configure_static_routes(
    leaves,
    spine_leaf_interfaces,
    leaf_host_interfaces,
) -> None:
    """
    Legt für jeden aktiven Datenstrom einen festen Spine-Pfad fest.

    Die Route wird auf dem Quell-Leaf eingetragen. Dadurch entscheidet
    nicht mehr das automatische Routing, welcher Spine verwendet wird.
    """

    static_helper = ns.Ipv4StaticRoutingHelper()

    hosts_per_leaf = NUM_HOSTS // NUM_LEAVES

    print("\nStatische Pfadzuordnung:")

    # Für jeden definierten Datenstrom wird ein
    # Sender und ein Empfänger erzeugt.
    for flow in TRAFFIC_FLOWS:
        source_host = flow["source"]
        destination_host = flow["destination"]

        # Bestimmen, an welchem Leaf Quelle und Ziel angeschlossen sind.
        source_leaf_index = source_host // hosts_per_leaf
        destination_leaf_index = destination_host // hosts_per_leaf

        # Hosts am gleichen Leaf benötigen keinen Spine-Pfad.
        if source_leaf_index == destination_leaf_index:
            print(
                f"Host {source_host} -> Host {destination_host}: "
                f"direkt über Leaf {source_leaf_index}"
            )
            continue

        flow_key = (source_host, destination_host)

        if flow_key not in STATIC_FLOW_SPINES:
            raise ValueError(
                "Für den Flow "
                f"Host {source_host} -> Host {destination_host} "
                "wurde kein statischer Spine festgelegt."
            )

        spine_index = STATIC_FLOW_SPINES[flow_key]

        if not 0 <= spine_index < NUM_SPINES:
            raise ValueError(
                f"Ungültiger Spine {spine_index} für Flow {flow_key}."
            )

        # Index des Spine-Leaf-Links.
        #
        # Die Links wurden in dieser Reihenfolge erstellt:
        #
        # Index 0: Spine0 -> Leaf0
        # Index 1: Spine0 -> Leaf1
        # Index 2: Spine1 -> Leaf0
        # Index 3: Spine1 -> Leaf1
        link_index = (
            spine_index * NUM_LEAVES
            + source_leaf_index
        )

        # Adresse 0 des InterfaceContainers gehört dem Spine.
        # Diese Adresse ist der nächste Gateway für den Quell-Leaf.
        gateway_address = spine_leaf_interfaces[
            link_index
        ].GetAddress(0)

        # Adresse 1 gehört jeweils dem Zielhost.
        destination_address = leaf_host_interfaces[
            destination_host
        ].GetAddress(1)

        # IPv4-Objekt des Quell-Leafs abrufen.
        source_leaf_ipv4 = leaves.Get(
            source_leaf_index
        ).GetObject[ns.Ipv4]()

        # Statisches Routingobjekt dieses Leafs abrufen.
        static_routing = static_helper.GetStaticRouting(
            source_leaf_ipv4
        )

        # Auf jedem Leaf ist:
        #
        # Interface 1 -> Verbindung zu Spine0
        # Interface 2 -> Verbindung zu Spine1
        output_interface = FIRST_SPINE_INTERFACE + spine_index

        # Host-spezifische Route eintragen.
        static_routing.AddHostRouteTo(
            destination_address,
            gateway_address,
            output_interface,
        )

        print(
            f"Host {source_host} -> Host {destination_host} "
            f"über Spine{spine_index} "
            f"(Gateway {gateway_address}, "
            f"Interface {output_interface})"
        )

# =========================================================
# Messdaten für dynamisches Routing
# =========================================================

ADAPTIVE_LINK_BYTES = {}
ADAPTIVE_PREVIOUS_BYTES = {}


def adaptive_phy_tx_end(link_index, packet):
    """
    Zählt die tatsächlich übertragenen Bytes eines
    Spine-Leaf-Links.
    """
    packet_size = int(packet.GetSize())

    ADAPTIVE_LINK_BYTES[link_index] = (
        ADAPTIVE_LINK_BYTES.get(link_index, 0)
        + packet_size
    )

def calculate_adaptive_link_loads(
    spine_leaf_links,
) -> dict:
    """
    Bestimmt die aktuelle Queue-Belegung aller
    Spine-Leaf-Links.

    Für jeden Link werden beide Übertragungsrichtungen
    betrachtet. Als Lastwert wird die größere aktuelle
    Queue-Belegung in Bytes verwendet.
    """

    link_loads = {}

    for link_index, devices in enumerate(spine_leaf_links):

        spine_device = devices.Get(0)
        leaf_device = devices.Get(1)

        spine_queue = spine_device.GetQueue()
        leaf_queue = leaf_device.GetQueue()

        spine_queue_bytes = int(
            spine_queue.GetNBytes()
        )

        leaf_queue_bytes = int(
            leaf_queue.GetNBytes()
        )

        link_loads[link_index] = max(
            spine_queue_bytes,
            leaf_queue_bytes,
        )

    return link_loads

def get_adaptive_path_load(
    spine_index: int,
    source_leaf_index: int,
    destination_leaf_index: int,
    link_loads: dict,
) -> float:
    """
    Bestimmt die Last eines möglichen Spine-Pfades.

    Für einen Pfad Leaf A -> Spine X -> Leaf B wird
    die höhere Last der beiden beteiligten
    Spine-Leaf-Links verwendet.
    """

    source_link_index = (
        spine_index * NUM_LEAVES
        + source_leaf_index
    )

    destination_link_index = (
        spine_index * NUM_LEAVES
        + destination_leaf_index
    )

    source_load = link_loads.get(
        source_link_index,
        0.0,
    )

    destination_load = link_loads.get(
        destination_link_index,
        0.0,
    )

    return max(
        source_load,
        destination_load,
    )

def is_adaptive_path_available(
    spine_index,
    source_leaf_index,
    destination_leaf_index,
    leaves,
    spines,
    spine_leaf_links,
) -> bool:
    """
    Prüft, ob ein Spine-Pfad zwischen Quell- und Ziel-Leaf
    vollständig verfügbar ist.

    Ein Pfad gilt nur dann als verfügbar, wenn sowohl der
    Spine-Leaf-Link auf der Quellseite als auch der Link
    auf der Zielseite aktiv sind.
    """

    for leaf_index in (
        source_leaf_index,
        destination_leaf_index,
    ):
        link_index = (
            spine_index * NUM_LEAVES
            + leaf_index
        )

        devices = spine_leaf_links[link_index]

        spine_device = devices.Get(0)
        leaf_device = devices.Get(1)

        spine_ipv4 = spines.Get(
            spine_index
        ).GetObject[ns.Ipv4]()

        leaf_ipv4 = leaves.Get(
            leaf_index
        ).GetObject[ns.Ipv4]()

        spine_interface = (
            spine_ipv4.GetInterfaceForDevice(
                spine_device
            )
        )

        leaf_interface = (
            leaf_ipv4.GetInterfaceForDevice(
                leaf_device
            )
        )

        if (
            not spine_ipv4.IsUp(spine_interface)
            or not leaf_ipv4.IsUp(leaf_interface)
        ):
            return False

    return True

def update_adaptive_routes(
    spines,
    leaves,
    spine_leaf_interfaces,
    leaf_host_interfaces,
    spine_leaf_links,
    flow_spines,
) -> None:
    """
    Überprüft während der Simulation die aktuelle
    Queue-Belegung der Spine-Leaf-Pfade und passt
    bei Bedarf die Flow-Routen an.

    Es werden nur Datenströme berücksichtigt, die
    zum aktuellen Simulationszeitpunkt aktiv sind.

    Innerhalb einer Adaptionsrunde wird ein Spine,
    auf den bereits ein Flow verschoben wurde, für
    weitere Verschiebungen zunächst nicht erneut
    verwendet. Dadurch wird verhindert, dass mehrere
    Flows gleichzeitig auf denselben scheinbar freien
    Spine wechseln.
    """

    # Aktuelle Queue-Belegung aller Spine-Leaf-Links messen.
    link_loads = calculate_adaptive_link_loads(
        spine_leaf_links
    )

    static_helper = ns.Ipv4StaticRoutingHelper()
    hosts_per_leaf = NUM_HOSTS // NUM_LEAVES

    current_time = ns.Simulator.Now().GetSeconds()

    # Merkt sich, welche Spines während dieser
    # Adaptionsrunde bereits Ziel einer Verschiebung waren.
    used_spines_this_round = set()

    for flow in TRAFFIC_FLOWS:
        source_host = flow["source"]
        destination_host = flow["destination"]
        flow_start = flow["start"]
        flow_stop = flow["stop"]

        # Nur momentan tatsächlich aktive Flows betrachten.
        if not flow_start <= current_time < flow_stop:
            continue

        source_leaf_index = (
            source_host // hosts_per_leaf
        )

        destination_leaf_index = (
            destination_host // hosts_per_leaf
        )

        # Intra-Leaf-Verkehr benötigt keinen Spine.
        if source_leaf_index == destination_leaf_index:
            continue

        flow_key = (
            source_host,
            destination_host,
        )

        current_spine = flow_spines[flow_key]

        # Aktuelle Queue-Last aller möglichen Pfade bestimmen.
        path_loads = {}

        for spine_index in range(NUM_SPINES):
            path_loads[spine_index] = get_adaptive_path_load(
                spine_index,
                source_leaf_index,
                destination_leaf_index,
                link_loads,
            )

        available_spines = [
            spine_index
            for spine_index in range(NUM_SPINES)
            if is_adaptive_path_available(
                spine_index,
                source_leaf_index,
                destination_leaf_index,
                leaves,
                spines,
                spine_leaf_links,
            )
        ]

        if not available_spines:
            print(
                f"[ADAPTIVE {current_time:.3f}s] "
                f"Host {source_host} -> Host {destination_host}: "
                f"kein verfügbarer Spine-Pfad"
            )
            continue

        candidate_spines = [
            spine_index
            for spine_index in available_spines
            if spine_index not in used_spines_this_round
        ]

        if not candidate_spines:
            candidate_spines = available_spines

        # Falls bereits alle Spines verwendet wurden,
        # stehen wieder alle Pfade zur Auswahl.
        if not candidate_spines:
            candidate_spines = list(
                range(NUM_SPINES)
            )

        best_spine = min(
            candidate_spines,
            key=lambda index: path_loads[index],
        )

        current_load = path_loads[current_spine]
        best_load = path_loads[best_spine]

        current_path_available = (
            current_spine in available_spines
        )

        if (
            current_path_available
            and best_spine == current_spine
        ):
            continue

        # =====================================================
        # Stabilitätsprüfung für normale lastbedingte Wechsel
        # =====================================================
        #
        # Ist der aktuelle Pfad ausgefallen, werden diese
        # Prüfungen bewusst übersprungen. Dadurch kann das
        # adaptive Routing beim Linkausfall unmittelbar auf
        # einen noch verfügbaren Spine wechseln.
        #
        # Bei einem weiterhin verfügbaren Pfad muss ein
        # alternativer Spine dagegen sowohl relativ als auch
        # absolut ausreichend besser sein. Dies verhindert
        # Route-Flapping aufgrund sehr kleiner Queue-Differenzen.

        if current_path_available:

            # Alternative muss tatsächlich geringer belastet sein.
            if best_load >= current_load:
                continue

            queue_improvement = (
                current_load - best_load
            )

            # Absolute Mindestverbesserung.
            if (
                queue_improvement
                < ADAPTIVE_MIN_QUEUE_IMPROVEMENT_BYTES
            ):
                continue

            # Relative Mindestverbesserung durch Hysterese.
            required_improvement = (
                current_load * ADAPTIVE_HYSTERESIS
            )

            if (
                current_load > 0.0
                and queue_improvement
                < required_improvement
            ):
                continue

        # =================================================
        # Route auf den neuen Spine umstellen
        # =================================================

        link_index = (
            best_spine * NUM_LEAVES
            + source_leaf_index
        )

        gateway_address = spine_leaf_interfaces[
            link_index
        ].GetAddress(0)

        destination_address = leaf_host_interfaces[
            destination_host
        ].GetAddress(1)

        source_leaf_ipv4 = leaves.Get(
            source_leaf_index
        ).GetObject[ns.Ipv4]()

        static_routing = static_helper.GetStaticRouting(
            source_leaf_ipv4
        )

        output_interface = (
            FIRST_SPINE_INTERFACE
            + best_spine
        )

        # Vorhandene host-spezifische Route zum Ziel entfernen.
        for route_index in reversed(
            range(static_routing.GetNRoutes())
        ):
            route = static_routing.GetRoute(
                route_index
            )

            if (
                route.IsHost()
                and route.GetDest()
                == destination_address
            ):
                static_routing.RemoveRoute(
                    route_index
                )

        # Neue Route über den ausgewählten Spine eintragen.
        static_routing.AddHostRouteTo(
            destination_address,
            gateway_address,
            output_interface,
        )

        # Neue Zuordnung speichern.
        flow_spines[flow_key] = best_spine

        # Diesen Spine innerhalb dieser Adaptionsrunde
        # für weitere Verschiebungen sperren.
        used_spines_this_round.add(
            best_spine
        )

        print(
            f"[ADAPTIVE "
            f"{ns.Simulator.Now().GetSeconds():.3f}s] "
            f"Host {source_host} -> Host {destination_host}: "
            f"Spine{current_spine} -> Spine{best_spine} "
            f"(Queue: {current_load / 1024.0:.1f} -> "
            f"{best_load / 1024.0:.1f} KiB)"
        )

# =========================================================
# Linkausfall
# =========================================================

def fail_spine_leaf_link(
    spines,
    leaves,
    spine_leaf_links,
    spine_index: int,
    leaf_index: int,
) -> None:
    """
    Deaktiviert einen Spine-Leaf-Link während der Simulation.

    Beide IPv4-Interfaces der Punkt-zu-Punkt-Verbindung
    werden heruntergefahren.

    Für STANDARD und ECMP werden anschließend die globalen
    Routingtabellen neu berechnet, damit alternative Pfade
    verwendet werden können.
    """

    link_index = (
        spine_index * NUM_LEAVES
        + leaf_index
    )

    devices = spine_leaf_links[link_index]

    spine_device = devices.Get(0)
    leaf_device = devices.Get(1)

    spine_ipv4 = spines.Get(
        spine_index
    ).GetObject[ns.Ipv4]()

    leaf_ipv4 = leaves.Get(
        leaf_index
    ).GetObject[ns.Ipv4]()

    spine_interface = (
        spine_ipv4.GetInterfaceForDevice(
            spine_device
        )
    )

    leaf_interface = (
        leaf_ipv4.GetInterfaceForDevice(
            leaf_device
        )
    )

    print()
    print(
        f"[FAILURE "
        f"{ns.Simulator.Now().GetSeconds():.3f}s] "
        f"Spine{spine_index} <-> Leaf{leaf_index} "
        f"wird deaktiviert."
    )

    spine_ipv4.SetDown(spine_interface)
    leaf_ipv4.SetDown(leaf_interface)

    if ROUTING_STRATEGY in {
        "STANDARD",
        "ECMP",
    }:
        ns.Ipv4GlobalRoutingHelper.RecomputeRoutingTables()

        print(
            f"[FAILURE "
            f"{ns.Simulator.Now().GetSeconds():.3f}s] "
            "Globale Routingtabellen wurden neu berechnet."
        )

class LinkFailureEvent(ns.EventImpl):
    """
    ns-3-Ereignis zum Auslösen eines Spine-Leaf-Linkausfalls.
    """

    def __init__(
        self,
        spines,
        leaves,
        spine_leaf_links,
        spine_index: int,
        leaf_index: int,
    ):
        super().__init__()

        self.spines = spines
        self.leaves = leaves
        self.spine_leaf_links = spine_leaf_links
        self.spine_index = spine_index
        self.leaf_index = leaf_index

    def Notify(self):
        fail_spine_leaf_link(
            self.spines,
            self.leaves,
            self.spine_leaf_links,
            self.spine_index,
            self.leaf_index,
        )

class AdaptiveRoutingEvent(ns.EventImpl):
    """
    ns-3-Ereignis zur dynamischen Aktualisierung
    der adaptiven Routen während der Simulation.
    """

    def __init__(
        self,
        spines,
        leaves,
        spine_leaf_interfaces,
        leaf_host_interfaces,
        spine_leaf_links,
        flow_spines,
    ):
        super().__init__()

        self.spines = spines
        self.leaves = leaves
        self.spine_leaf_interfaces = spine_leaf_interfaces
        self.leaf_host_interfaces = leaf_host_interfaces
        self.spine_leaf_links = spine_leaf_links
        self.flow_spines = flow_spines

    def Notify(self):
        update_adaptive_routes(
            self.spines,
            self.leaves,
            self.spine_leaf_interfaces,
            self.leaf_host_interfaces,
            self.spine_leaf_links,
            self.flow_spines,
        )

def configure_adaptive_routes(
    leaves,
    spine_leaf_interfaces,
    leaf_host_interfaces,
) -> dict:
    """
    Konfiguriert eine lastabhängige Pfadzuweisung.

    Für jeden aktiven Cross-Leaf-Datenstrom wird der Spine mit der
    aktuell geringsten bereits zugewiesenen angebotenen Last gewählt.

    Nach der Auswahl wird die Datenrate des Flows der Last dieses
    Spines zugerechnet. Dadurch werden nachfolgende Flows bevorzugt
    auf weniger belastete Spine-Pfade verteilt.

    Die Entscheidung erfolgt vor Simulationsbeginn anhand der
    angebotenen Flow-Datenraten. Bereits laufende Flows werden
    während der Simulation nicht dynamisch umgeleitet.
    """

    static_helper = ns.Ipv4StaticRoutingHelper()

    hosts_per_leaf = NUM_HOSTS // NUM_LEAVES

    # Bereits zugewiesene angebotene Last jedes Spines in Bit/s.
    spine_loads = [0.0 for _ in range(NUM_SPINES)]

    flow_spines = {}

    print("\nLastabhängige Pfadzuordnung:")

    for flow in TRAFFIC_FLOWS:
        source_host = flow["source"]
        destination_host = flow["destination"]
        data_rate = flow["rate"]
        flow_start = flow["start"]

        # Zugehörige Leaves von Quelle und Ziel bestimmen.
        source_leaf_index = source_host // hosts_per_leaf
        destination_leaf_index = destination_host // hosts_per_leaf

        # Kommunikation innerhalb desselben Leafs benötigt keinen Spine.
        if source_leaf_index == destination_leaf_index:
            print(
                f"Host {source_host} -> Host {destination_host}: "
                f"direkt über Leaf {source_leaf_index}"
            )
            continue

        # Flows, die bereits zum regulären Client-Start aktiv sind,
        # werden lastabhängig initial verteilt.
        #
        # Später startende Flows erhalten zunächst einen
        # deterministischen Standardpfad. Ihre zukünftige Last
        # wird bei der initialen Lastberechnung nicht berücksichtigt.
        if flow_start <= CLIENT_START:
            spine_index = min(
                range(NUM_SPINES),
                key=lambda index: spine_loads[index],
            )
        else:
            spine_index = 0

        flow_rate_bps = data_rate_to_bps(data_rate)

        load_before = spine_loads[spine_index]

        # Index des Links zwischen gewähltem Spine und Quell-Leaf.
        link_index = (
            spine_index * NUM_LEAVES
            + source_leaf_index
        )

        # Gateway auf dem gewählten Spine bestimmen.
        gateway_address = spine_leaf_interfaces[
            link_index
        ].GetAddress(0)

        # IP-Adresse des Zielhosts bestimmen.
        destination_address = leaf_host_interfaces[
            destination_host
        ].GetAddress(1)

        # IPv4-Objekt des Quell-Leafs abrufen.
        source_leaf_ipv4 = leaves.Get(
            source_leaf_index
        ).GetObject[ns.Ipv4]()

        # Statisches Routingobjekt des Quell-Leafs abrufen.
        static_routing = static_helper.GetStaticRouting(
            source_leaf_ipv4
        )

        # Passendes Ausgangsinterface zum gewählten Spine.
        output_interface = (
            FIRST_SPINE_INTERFACE
            + spine_index
        )

        # Host-spezifische Route über den ausgewählten Spine eintragen.
        static_routing.AddHostRouteTo(
            destination_address,
            gateway_address,
            output_interface,
        )

        # Die angebotene Datenrate dieses Flows anschließend
        # der Last des ausgewählten Spines zurechnen.
        if flow_start <= CLIENT_START:
            spine_loads[spine_index] += flow_rate_bps

        flow_spines[
            (source_host, destination_host)
        ] = spine_index

        print(
            f"Host {source_host} -> Host {destination_host} "
            f"über Spine{spine_index} "
            f"(Flow: {data_rate}, "
            f"Last vorher: {load_before / 1_000_000_000.0:.3f} Gbit/s, "
            f"Last danach: "
            f"{spine_loads[spine_index] / 1_000_000_000.0:.3f} Gbit/s)"
        )

    print("\nZugewiesene Last pro Spine:")

    for spine_index, load_bps in enumerate(spine_loads):
        print(
            f"Spine {spine_index}: "
            f"{load_bps / 1_000_000_000.0:.3f} Gbit/s"
        )

    return flow_spines

def calculate_flow_metrics(stats) -> dict:
    tx_packets = int(stats.txPackets)
    rx_packets = int(stats.rxPackets)

    # End-to-End-Paketverlust:
    # Als verloren gelten alle gesendeten Pakete,
    # die den Empfänger nicht erreicht haben.
    lost_packets = max(
        tx_packets - rx_packets,
        0,
    )

    tx_bytes = int(stats.txBytes)
    rx_bytes = int(stats.rxBytes)

    packet_loss_percent = (
        (lost_packets / tx_packets) * 100.0
        if tx_packets > 0
        else 0.0
    )

    duration_seconds = (
        stats.timeLastRxPacket.GetSeconds()
        - stats.timeFirstTxPacket.GetSeconds()
    )

    throughput_mbit_s = (
        rx_bytes * 8.0 / duration_seconds / 1_000_000.0
        if rx_packets > 0 and duration_seconds > 0
        else 0.0
    )

    mean_delay_ms = (
        stats.delaySum.GetSeconds() / rx_packets * 1000.0
        if rx_packets > 0
        else 0.0
    )

    mean_jitter_ms = (
        stats.jitterSum.GetSeconds() / (rx_packets - 1) * 1000.0
        if rx_packets > 1
        else 0.0
    )

    return {
        "tx_packets": tx_packets,
        "rx_packets": rx_packets,
        "lost_packets": lost_packets,
        "tx_bytes": tx_bytes,
        "rx_bytes": rx_bytes,
        "packet_loss_percent": packet_loss_percent,
        "throughput_mbit_s": throughput_mbit_s,
        "mean_delay_ms": mean_delay_ms,
        "mean_jitter_ms": mean_jitter_ms,
    }


def write_flow_results(flow_stats, filename: str) -> None:
    """
    Schreibt die Ergebnisse aller einzelnen Flows in eine CSV-Datei
    und berechnet zusätzlich aggregierte Kennzahlen des gesamten
    Experiments.
    """

    total_tx_packets = 0
    total_rx_packets = 0
    total_lost_packets = 0
    total_tx_bytes = 0
    total_rx_bytes = 0

    total_delay_seconds = 0.0
    total_jitter_seconds = 0.0
    total_jitter_samples = 0

    flow_throughputs = []

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:

        writer = csv.writer(csv_file)

        writer.writerow([
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
        ])

        for flow_id, stats in flow_stats:

            metrics = calculate_flow_metrics(stats)

            writer.writerow([
                int(flow_id),
                metrics["tx_packets"],
                metrics["rx_packets"],
                metrics["lost_packets"],
                metrics["tx_bytes"],
                metrics["rx_bytes"],
                f'{metrics["packet_loss_percent"]:.6f}',
                f'{metrics["throughput_mbit_s"]:.6f}',
                f'{metrics["mean_delay_ms"]:.6f}',
                f'{metrics["mean_jitter_ms"]:.6f}',
            ])

            # =================================================
            # Aggregierte Messwerte sammeln
            # =================================================

            total_tx_packets += metrics["tx_packets"]
            total_rx_packets += metrics["rx_packets"]
            total_lost_packets += metrics["lost_packets"]

            total_tx_bytes += metrics["tx_bytes"]
            total_rx_bytes += metrics["rx_bytes"]

            total_delay_seconds += (
                stats.delaySum.GetSeconds()
            )

            total_jitter_seconds += (
                stats.jitterSum.GetSeconds()
            )

            if metrics["rx_packets"] > 1:
                total_jitter_samples += (
                    metrics["rx_packets"] - 1
                )

            flow_throughputs.append(
                metrics["throughput_mbit_s"]
            )

            print(f"\nFlow {int(flow_id)}")
            print(
                f'  Gesendete Pakete : '
                f'{metrics["tx_packets"]}'
            )
            print(
                f'  Empfangene Pakete: '
                f'{metrics["rx_packets"]}'
            )
            print(
                f'  Verlorene Pakete : '
                f'{metrics["lost_packets"]}'
            )
            print(
                f'  Paketverlust      : '
                f'{metrics["packet_loss_percent"]:.2f} %'
            )
            print(
                f'  Durchsatz         : '
                f'{metrics["throughput_mbit_s"]:.3f} Mbit/s'
            )
            print(
                f'  Mittlere Laufzeit : '
                f'{metrics["mean_delay_ms"]:.3f} ms'
            )
            print(
                f'  Mittlerer Jitter  : '
                f'{metrics["mean_jitter_ms"]:.3f} ms'
            )

    # =========================================================
    # Gesamtergebnis des Experiments
    # =========================================================

    total_throughput_mbit_s = sum(
        flow_throughputs
    )

    total_packet_loss_percent = (
        (
            (total_tx_packets - total_rx_packets)
            / total_tx_packets
        )
        * 100.0
        if total_tx_packets > 0
        else 0.0
    )

    weighted_mean_delay_ms = (
        total_delay_seconds
        / total_rx_packets
        * 1000.0
        if total_rx_packets > 0
        else 0.0
    )

    weighted_mean_jitter_ms = (
        total_jitter_seconds
        / total_jitter_samples
        * 1000.0
        if total_jitter_samples > 0
        else 0.0
    )

    # Jain's Fairness Index
    #
    # 1.0 bedeutet perfekte Gleichverteilung
    # des gemessenen Flow-Durchsatzes.
    if flow_throughputs:
        throughput_sum = sum(
            flow_throughputs
        )

        throughput_square_sum = sum(
            throughput ** 2
            for throughput in flow_throughputs
        )

        fairness_index = (
            throughput_sum ** 2
            / (
                len(flow_throughputs)
                * throughput_square_sum
            )
            if throughput_square_sum > 0.0
            else 0.0
        )
    else:
        fairness_index = 0.0

    print("\n==========================================")
    print("Aggregierte Messergebnisse")
    print("==========================================")

    print(
        f"Gesamtdurchsatz     : "
        f"{total_throughput_mbit_s:.3f} Mbit/s"
    )

    print(
        f"Gesamtpaketverlust  : "
        f"{total_packet_loss_percent:.3f} %"
    )

    print(
        f"Gewichtete Latenz   : "
        f"{weighted_mean_delay_ms:.3f} ms"
    )

    print(
        f"Gewichteter Jitter  : "
        f"{weighted_mean_jitter_ms:.6f} ms"
    )

    print(
        f"Jain Fairness Index : "
        f"{fairness_index:.6f}"
    )

    print(
        f"Gesendete Pakete    : "
        f"{total_tx_packets}"
    )

    print(
        f"Empfangene Pakete   : "
        f"{total_rx_packets}"
    )

    print(
        f"Verlorene Pakete    : "
        f"{total_lost_packets}"
    )

def write_summary_results(
    flow_stats,
    filename: str,
) -> None:
    """
    Schreibt die aggregierten Kennzahlen einer Simulation
    in eine separate CSV-Datei.

    Diese Datei dient später zur automatisierten Auswertung
    mehrerer Strategien, Szenarien und Wiederholungen.
    """

    total_tx_packets = 0
    total_rx_packets = 0
    total_lost_packets = 0

    total_delay_seconds = 0.0
    total_jitter_seconds = 0.0
    total_jitter_samples = 0

    flow_throughputs = []

    for flow_id, stats in flow_stats:

        metrics = calculate_flow_metrics(stats)

        total_tx_packets += metrics["tx_packets"]
        total_rx_packets += metrics["rx_packets"]
        total_lost_packets += metrics["lost_packets"]

        total_delay_seconds += (
            stats.delaySum.GetSeconds()
        )

        total_jitter_seconds += (
            stats.jitterSum.GetSeconds()
        )

        if metrics["rx_packets"] > 1:
            total_jitter_samples += (
                metrics["rx_packets"] - 1
            )

        flow_throughputs.append(
            metrics["throughput_mbit_s"]
        )

    # =====================================================
    # Aggregierte Kennzahlen
    # =====================================================

    total_throughput_mbit_s = sum(
        flow_throughputs
    )

    total_packet_loss_percent = (
        (
            (total_tx_packets - total_rx_packets)
            / total_tx_packets
        )
        * 100.0
        if total_tx_packets > 0
        else 0.0
    )

    weighted_mean_delay_ms = (
        total_delay_seconds
        / total_rx_packets
        * 1000.0
        if total_rx_packets > 0
        else 0.0
    )

    weighted_mean_jitter_ms = (
        total_jitter_seconds
        / total_jitter_samples
        * 1000.0
        if total_jitter_samples > 0
        else 0.0
    )

    if flow_throughputs:

        throughput_sum = sum(
            flow_throughputs
        )

        throughput_square_sum = sum(
            throughput ** 2
            for throughput in flow_throughputs
        )

        fairness_index = (
            throughput_sum ** 2
            / (
                len(flow_throughputs)
                * throughput_square_sum
            )
            if throughput_square_sum > 0.0
            else 0.0
        )

    else:
        fairness_index = 0.0

    # =====================================================
    # Summary-CSV schreiben
    # =====================================================

    with open(
        filename,
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:

        writer = csv.writer(csv_file)

        writer.writerow([
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
        ])

        writer.writerow([
            ROUTING_STRATEGY,
            SCENARIO,
            SCENARIO_NAME,
            SEED,
            RUN_NUMBER,
            len(flow_throughputs),
            total_tx_packets,
            total_rx_packets,
            total_lost_packets,
            f"{total_packet_loss_percent:.6f}",
            f"{total_throughput_mbit_s:.6f}",
            f"{weighted_mean_delay_ms:.6f}",
            f"{weighted_mean_jitter_ms:.6f}",
            f"{fairness_index:.6f}",
        ]) 

def create_file_label() -> str:
    """
    Erzeugt einen Dateinamen aus Routingstrategie und Szenario.

    Beispiel:
        STANDARD + Szenario 1 - Baseline

    wird zu

        standard_szenario_1__baseline
    """

    return (
        f"{ROUTING_STRATEGY.lower()}_"
        f"{SCENARIO_NAME.lower()}"
        .replace(" ", "_")
        .replace("-", "_")
    )

def configure_routing_strategy(
    leaves,
    spine_leaf_interfaces,
    leaf_host_interfaces,
) -> dict:
    """
    Konfiguriert die gewählte Routingstrategie.
    """

    if ROUTING_STRATEGY == "STANDARD":

        ns.Ipv4GlobalRoutingHelper.PopulateRoutingTables()

        print("Routingstrategie : Standard Routing")

    elif ROUTING_STRATEGY == "ECMP":

        ns.Ipv4GlobalRoutingHelper.PopulateRoutingTables()

        print("Routingstrategie : Equal Cost Multi Path (ECMP)")

    elif ROUTING_STRATEGY == "STATIC":

        ns.Ipv4GlobalRoutingHelper.PopulateRoutingTables()

        configure_static_routes(
            leaves,
            spine_leaf_interfaces,
            leaf_host_interfaces,
        )

        print("Routingstrategie : Statisches Flow-Pinning")

    elif ROUTING_STRATEGY == "ADAPTIVE":

        ns.Ipv4GlobalRoutingHelper.PopulateRoutingTables()

        flow_spines = configure_adaptive_routes(
            leaves,
            spine_leaf_interfaces,
            leaf_host_interfaces,
        )

        print("Routingstrategie : Lastabhängiges Routing")

    else:

        raise ValueError(
            f"Unbekannte Routingstrategie: {ROUTING_STRATEGY}"
        )

    if ROUTING_STRATEGY == "ADAPTIVE":
        return flow_spines

    return {}

def create_traffic(
    hosts,
    leaf_host_interfaces,
) -> None:
    """
    Erstellt alle Datenströme des aktiven Traffic-Szenarios.
    """

    print()
    print("Aktive Datenströme:")

    for flow in TRAFFIC_FLOWS:
        source_host = flow["source"]
        destination_host = flow["destination"]
        data_rate = flow["rate"]
        flow_start = flow["start"]
        flow_stop = flow["stop"]

        # Zieladresse bestimmen
        destination_address = (
            leaf_host_interfaces[destination_host]
            .GetAddress(1)
        )

        # =================================================
        # Packet Sink (Empfänger)
        # =================================================

        local = ns.InetSocketAddress(
            ns.Ipv4Address.GetAny(),
            SERVER_PORT,
        )

        sink = ns.PacketSinkHelper(
            "ns3::UdpSocketFactory",
            local.ConvertTo(),
        )

        sink_app = sink.Install(
            hosts.Get(destination_host)
        )

        sink_app.Start(ns.Seconds(flow_start))
        sink_app.Stop(ns.Seconds(flow_stop))

        # =================================================
        # OnOff Sender
        # =================================================

        remote = ns.InetSocketAddress(
            destination_address,
            SERVER_PORT,
        )

        onoff = ns.OnOffHelper(
            "ns3::UdpSocketFactory",
            remote.ConvertTo(),
        )

        onoff.SetAttribute(
            "DataRate",
            ns.DataRateValue(
                ns.DataRate(data_rate)
            ),
        )

        onoff.SetAttribute(
            "PacketSize",
            ns.UintegerValue(PACKET_SIZE_BYTES),
        )

        onoff.SetAttribute(
            "OnTime",
            ns.StringValue(
                "ns3::ConstantRandomVariable[Constant=1]"
            ),
        )

        onoff.SetAttribute(
            "OffTime",
            ns.StringValue(
                "ns3::ConstantRandomVariable[Constant=0]"
            ),
        )

        app = onoff.Install(
            hosts.Get(source_host)
        )

        app.Start(ns.Seconds(CLIENT_START))
        app.Stop(ns.Seconds(CLIENT_STOP))

        print(
            f"Host {source_host}"
            f"  --->  "
            f"Host {destination_host}"
            f"    ({data_rate})"
        )

def main() -> None:
    """
    Überprüft die Plausibilität der
    Simulationskonfiguration.
    """
    validate_configuration()

    # =====================================================
    # Reproduzierbare Zufallssteuerung
    # =====================================================

    ns.RngSeedManager.SetSeed(SEED)
    ns.RngSeedManager.SetRun(RUN_NUMBER)

    print("\n==========================================")
    print("Netzwerkaufbau")
    print("==========================================")

    spines = ns.NodeContainer()
    spines.Create(NUM_SPINES)

    leaves = ns.NodeContainer()
    leaves.Create(NUM_LEAVES)

    hosts = ns.NodeContainer()
    hosts.Create(NUM_HOSTS)

    print("Nodes wurden erstellt.")

    p2p = ns.PointToPointHelper()
    p2p.SetDeviceAttribute("DataRate", ns.StringValue(LINK_RATE))
    p2p.SetChannelAttribute("Delay", ns.StringValue(LINK_DELAY))

    spine_leaf_links = []
    for spine_index in range(NUM_SPINES):
        for leaf_index in range(NUM_LEAVES):
            spine_leaf_links.append(
                create_link(
                    p2p,
                    spines.Get(spine_index),
                    leaves.Get(leaf_index),
                )
            )


    leaf_host_links = []
    hosts_per_leaf = NUM_HOSTS // NUM_LEAVES

    for leaf_index in range(NUM_LEAVES):
        for local_host_index in range(hosts_per_leaf):
            host_index = leaf_index * hosts_per_leaf + local_host_index
            leaf_host_links.append(
                create_link(
                    p2p,
                    leaves.Get(leaf_index),
                    hosts.Get(host_index),
                )
            )

    print("Point-to-Point-Links wurden erstellt.")

    # =====================================================
    # ECMP-Eigenschaft vor Installation des Internet-Stacks
    # setzen
    # =====================================================

    if ROUTING_STRATEGY == "ECMP":
        ns.Config.SetDefault(
            "ns3::Ipv4GlobalRouting::RandomEcmpRouting",
            ns.BooleanValue(True),
        )
    else:
        ns.Config.SetDefault(
            "ns3::Ipv4GlobalRouting::RandomEcmpRouting",
            ns.BooleanValue(False),
        )

    internet = ns.InternetStackHelper()
    internet.Install(spines)
    internet.Install(leaves)
    internet.Install(hosts)

    print("Internet Stack wurde installiert.")

    address = ns.Ipv4AddressHelper()
    subnet_number = 1

    spine_leaf_interfaces = []
    for devices in spine_leaf_links:
        spine_leaf_interfaces.append(
            assign_subnet(address, devices, subnet_number)
        )
        subnet_number += 1

    leaf_host_interfaces = []
    for devices in leaf_host_links:
        leaf_host_interfaces.append(
            assign_subnet(address, devices, subnet_number)
        )
        subnet_number += 1

    print("IPv4-Adressen wurden vergeben.")

    # =====================================================
    # Routing konfigurieren
    # =====================================================
    flow_spines = configure_routing_strategy(
        leaves,
        spine_leaf_interfaces,
        leaf_host_interfaces,
    )

    # Für Dateinamen Leerzeichen und Sonderzeichen ersetzen.
    FILE_LABEL = (
        f"{create_file_label()}_seed_{SEED}_run_{RUN_NUMBER}"
    )

    CSV_FILENAME = f"results_{FILE_LABEL}.csv"
    XML_FILENAME = f"flowmonitor_{FILE_LABEL}.xml"
    ROUTING_TABLE_FILENAME = f"routing_{FILE_LABEL}.txt"

    # =====================================================
    # Routingtabellen zur Kontrolle speichern
    # =====================================================

    ascii_helper = ns.AsciiTraceHelper()

    routing_stream = ascii_helper.CreateFileStream(
        ROUTING_TABLE_FILENAME
    )

    ns.Ipv4GlobalRoutingHelper.PrintRoutingTableAllAt(
        ns.Seconds(0.1),
        routing_stream,
    )

    print("\n==========================================")
    print("Routing")
    print("==========================================")

    print(f"Routingstrategie : {ROUTING_STRATEGY}")
    print(
        f"Routingtabellen werden in "
        f"{ROUTING_TABLE_FILENAME} gespeichert."
    )

    print("\n==========================================")
    print("Simulation")
    print("==========================================")

    print(f"Traffic-Szenario : {SCENARIO_NAME}")
    print(f"Seed             : {SEED}")
    print(f"Run              : {RUN_NUMBER}")

    create_traffic(
        hosts,
        leaf_host_interfaces,
    )

    flow_monitor_helper = ns.FlowMonitorHelper()
    flow_monitor = flow_monitor_helper.InstallAll()

    if ROUTING_STRATEGY == "ADAPTIVE":

        # Für jeden Adaptionszeitpunkt wird ein eigenes
        # ns-3-Event erzeugt.
        #
        # Die Referenzen werden in einer Liste gehalten,
        # damit die Python-Eventobjekte bis zur Ausführung
        # nicht vom Garbage Collector freigegeben werden.
        adaptive_events = []

        adaptive_time = 1.5

        while adaptive_time < SIMULATION_END:

            adaptive_event = AdaptiveRoutingEvent(
                spines,
                leaves,
                spine_leaf_interfaces,
                leaf_host_interfaces,
                spine_leaf_links,
                flow_spines,
            )

            adaptive_events.append(
                adaptive_event
            )

            ns.Simulator.Schedule(
                ns.Seconds(adaptive_time),
                adaptive_event,
            )

            adaptive_time += ADAPTIVE_INTERVAL

    ns.Simulator.Stop(ns.Seconds(SIMULATION_END))

    # =====================================================
    # Optionaler Linkausfall des aktiven Szenarios
    # =====================================================

    failure = ACTIVE_SCENARIO.get("failure")

    if failure is not None:
        failure_spine = int(failure["spine"])
        failure_leaf = int(failure["leaf"])
        failure_time = float(failure["time"])

        print(
            f"Linkausfall       : "
            f"Spine{failure_spine} <-> Leaf{failure_leaf} "
            f"bei {failure_time:.3f} s"
        )

        failure_event = LinkFailureEvent(
            spines,
            leaves,
            spine_leaf_links,
            failure_spine,
            failure_leaf,
        )

        ns.Simulator.Schedule(
            ns.Seconds(failure_time),
            failure_event,
        )

    print("\nSimulation wird gestartet ...")

    ns.Simulator.Run()

    print("Simulation wurde beendet.")

    flow_monitor.CheckForLostPackets()
    flow_stats = flow_monitor.GetFlowStats()

    print("\n==========================================")
    print("Simulationsergebnisse")
    print("==========================================")
    """
    Schreibt alle Messergebnisse in eine CSV-Datei
    und gibt sie auf der Konsole aus.
    """
    write_flow_results(flow_stats, CSV_FILENAME)

    summary_filename = (
        f"summary_{FILE_LABEL}.csv"
    )

    write_summary_results(
        flow_stats,
        summary_filename,
    )

    flow_monitor.SerializeToXmlFile(XML_FILENAME, True, True)

    print("\n==========================================")
    print("Datacenter-Topologie")
    print("==========================================")
    print(f"Spines            : {spines.GetN()}")
    print(f"Leaves            : {leaves.GetN()}")
    print(f"Hosts             : {hosts.GetN()}")
    print(f"Spine-Leaf-Links  : {len(spine_leaf_links)}")
    print(f"Leaf-Host-Links   : {len(leaf_host_links)}")
    print(f"Link-Datenrate    : {LINK_RATE}")
    print(f"Link-Verzögerung  : {LINK_DELAY}")

    print("\n==========================================")
    print("Erzeugte Dateien")
    print("==========================================")

    print(f"CSV           : {CSV_FILENAME}")
    print(f"Summary CSV   : {summary_filename}")
    print(f"FlowMonitor   : {XML_FILENAME}")
    print(f"Routing       : {ROUTING_TABLE_FILENAME}")

    ns.Simulator.Destroy()


if __name__ == "__main__":
    main()