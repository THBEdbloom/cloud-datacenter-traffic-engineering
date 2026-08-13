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
# Optionale Steuerung über Kommandozeilenparameter
#
# Beispiel:
#
#   ./ns3 run "python/datacenter.py STATIC 2"
#
# Dadurch werden die Standardwerte überschrieben.
# =========================================================

if len(sys.argv) == 3:
    ROUTING_STRATEGY = sys.argv[1].upper()
    SCENARIO = int(sys.argv[2])


# =========================================================
# Definition aller Szenarien
#
# Diese Werte müssen normalerweise NICHT geändert werden.
# =========================================================

SCENARIOS = {

    # =====================================================
    # Szenario 1 - Baseline
    #
    # Ein einzelner Cross-Leaf-Datenstrom.
    # Der Datenverkehr läuft von Leaf 0 zu Leaf 3.
    # =====================================================

    1: {
        "name": "Szenario 1 - Baseline",
        "flow_rate": "100Mbps",

        "flows": [
            (0, 15),
        ],
    },


    # =====================================================
    # Szenario 2 - Mittlere Last
    #
    # Vier parallele Cross-Leaf-Datenströme.
    # Alle vier Leaves sind am Datenverkehr beteiligt.
    # =====================================================

    2: {
        "name": "Szenario 2 - Mittlere Last",
        "flow_rate": "100Mbps",

        "flows": [
            (0, 15),   # Leaf 0 -> Leaf 3
            (4, 11),   # Leaf 1 -> Leaf 2
            (8, 3),    # Leaf 2 -> Leaf 0
            (12, 7),   # Leaf 3 -> Leaf 1
        ],
    },


    # =====================================================
    # Szenario 3 - Hohe Last
    #
    # Gleiche Kommunikationsbeziehungen wie in Szenario 2,
    # jedoch mit deutlich höherer Datenrate.
    #
    # Dadurch lässt sich der Einfluss steigender Last
    # unabhängig vom Kommunikationsmuster untersuchen.
    # =====================================================

    3: {
        "name": "Szenario 3 - Hohe Last",
        "flow_rate": "2Gbps",

        "flows": [
            (0, 15),
            (4, 11),
            (8, 3),
            (12, 7),
        ],
    },


    # =====================================================
    # Szenario 4 - Überlast
    #
    # Identische Kommunikationsbeziehungen mit sehr hoher
    # Datenrate zur gezielten Erzeugung von Engpässen.
    # =====================================================

    4: {
        "name": "Szenario 4 - Überlast",
        "flow_rate": "12Gbps",

        "flows": [
            (0, 15),
            (4, 11),
            (8, 3),
            (12, 7),
        ],
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
    (0, 15): 0,   # Leaf 0 -> Leaf 3 über Spine 0
    (4, 11): 1,   # Leaf 1 -> Leaf 2 über Spine 1
    (8, 3): 2,    # Leaf 2 -> Leaf 0 über Spine 2
    (12, 7): 3,   # Leaf 3 -> Leaf 1 über Spine 3
}


# =========================================================
# Aktives Szenario laden
#
# Ab hier muss normalerweise nichts mehr geändert werden.
# =========================================================

ACTIVE_SCENARIO = SCENARIOS[SCENARIO]

SCENARIO_NAME = ACTIVE_SCENARIO["name"]

FLOW_RATE = ACTIVE_SCENARIO["flow_rate"]

TRAFFIC_FLOWS = [

    (source, destination, FLOW_RATE)

    for source, destination in ACTIVE_SCENARIO["flows"]

]

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
    for source_host, destination_host, _data_rate in TRAFFIC_FLOWS:

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

def configure_adaptive_routes(
    leaves,
    spine_leaf_interfaces,
    leaf_host_interfaces,
) -> None:
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

    print("\nLastabhängige Pfadzuordnung:")

    for source_host, destination_host, data_rate in TRAFFIC_FLOWS:

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

        # Spine mit der momentan geringsten zugewiesenen Last wählen.
        spine_index = min(
            range(NUM_SPINES),
            key=lambda index: spine_loads[index],
        )

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
        spine_loads[spine_index] += flow_rate_bps

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

def calculate_flow_metrics(stats) -> dict:
    tx_packets = int(stats.txPackets)
    rx_packets = int(stats.rxPackets)
    lost_packets = int(stats.lostPackets)
    tx_bytes = int(stats.txBytes)
    rx_bytes = int(stats.rxBytes)

    packet_loss_percent = (
        ((tx_packets - rx_packets) / tx_packets) * 100.0
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
    with open(filename, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow([
            "flow_id", "tx_packets", "rx_packets", "lost_packets",
            "tx_bytes", "rx_bytes", "packet_loss_percent",
            "throughput_mbit_s", "mean_delay_ms", "mean_jitter_ms",
        ])

        for flow_id, stats in flow_stats:
            """
            Berechnet alle Kennzahlen eines Flows.
            """
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

            print(f"\nFlow {int(flow_id)}")
            print(f'  Gesendete Pakete : {metrics["tx_packets"]}')
            print(f'  Empfangene Pakete: {metrics["rx_packets"]}')
            print(f'  Verlorene Pakete : {metrics["lost_packets"]}')
            print(f'  Paketverlust      : {metrics["packet_loss_percent"]:.2f} %')
            print(f'  Durchsatz         : {metrics["throughput_mbit_s"]:.3f} Mbit/s')
            print(f'  Mittlere Laufzeit : {metrics["mean_delay_ms"]:.3f} ms')
            print(f'  Mittlerer Jitter  : {metrics["mean_jitter_ms"]:.3f} ms')

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
) -> None:
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

        configure_adaptive_routes(
            leaves,
            spine_leaf_interfaces,
            leaf_host_interfaces,
        )

        print("Routingstrategie : Lastabhängiges Routing")

    else:

        raise ValueError(
            f"Unbekannte Routingstrategie: {ROUTING_STRATEGY}"
        )

def create_traffic(
    hosts,
    leaf_host_interfaces,
) -> None:
    """
    Erstellt alle Datenströme des aktiven Traffic-Szenarios.
    """

    print()
    print("Aktive Datenströme:")

    for source_host, destination_host, data_rate in TRAFFIC_FLOWS:

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

        sink_app.Start(ns.Seconds(SERVER_START))
        sink_app.Stop(ns.Seconds(SIMULATION_END))

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
    configure_routing_strategy(
        leaves,
        spine_leaf_interfaces,
        leaf_host_interfaces,
    )

    # Für Dateinamen Leerzeichen und Sonderzeichen ersetzen.
    FILE_LABEL = create_file_label()

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

    create_traffic(
        hosts,
        leaf_host_interfaces,
    )

    flow_monitor_helper = ns.FlowMonitorHelper()
    flow_monitor = flow_monitor_helper.InstallAll()

    ns.Simulator.Stop(ns.Seconds(SIMULATION_END))

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
    print(f"FlowMonitor   : {XML_FILENAME}")
    print(f"Routing       : {ROUTING_TABLE_FILENAME}")

    ns.Simulator.Destroy()


if __name__ == "__main__":
    main()