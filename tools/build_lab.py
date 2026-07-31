#!/usr/bin/env python3
"""Generate the JNCIE-SP master topology, base configs, and addressing tables."""

from __future__ import annotations

import csv
import ipaddress
import os
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = os.environ.get("JNCIE_PROFILE", "daily")
if PROFILE == "full":
    NODES_FILE = ROOT / "inventory" / "nodes.csv"
    LINKS_FILE = ROOT / "inventory" / "links.csv"
    TOPOLOGY_FILE = ROOT / "topology" / "jncie-sp-master.clab.yml"
    CONFIG_DIR = ROOT / "configs" / "base"
    ADDRESSING_FILE = ROOT / "docs" / "ADDRESSING-PLAN.md"
    LAB_NAME = "jncie-sp-master"
    MGMT_NETWORK = "jncie-sp-master-mgmt"
    MGMT_SUBNET = "10.204.253.0/24"
    CONFIG_SUBDIR = "base"
    AUTO1_IP = None
elif PROFILE == "optimized":
    NODES_FILE = ROOT / "inventory" / "optimized-nodes.csv"
    LINKS_FILE = ROOT / "inventory" / "optimized-links.csv"
    TOPOLOGY_FILE = ROOT / "topology" / "jncie-sp-optimized.clab.yml"
    CONFIG_DIR = ROOT / "configs" / "optimized"
    ADDRESSING_FILE = ROOT / "docs" / "OPTIMIZED-ADDRESSING-PLAN.md"
    LAB_NAME = "jncie-sp-optimized"
    MGMT_NETWORK = "jncie-sp-optimized-mgmt"
    MGMT_SUBNET = "10.204.252.0/24"
    CONFIG_SUBDIR = "optimized"
    AUTO1_IP = "10.204.252.10"
elif PROFILE == "daily":
    NODES_FILE = ROOT / "inventory" / "daily-nodes.csv"
    LINKS_FILE = ROOT / "inventory" / "daily-links.csv"
    TOPOLOGY_FILE = ROOT / "topology" / "jncie-sp-daily.clab.yml"
    CONFIG_DIR = ROOT / "configs" / "daily"
    ADDRESSING_FILE = ROOT / "docs" / "DAILY-ADDRESSING-PLAN.md"
    LAB_NAME = "jncie-sp-daily"
    MGMT_NETWORK = "jncie-sp-daily-mgmt"
    MGMT_SUBNET = "10.204.251.0/24"
    CONFIG_SUBDIR = "daily"
    AUTO1_IP = "10.204.251.10"
else:
    raise SystemExit(f"Unsupported JNCIE_PROFILE: {PROFILE}")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def link_addresses(link_id: int) -> tuple[str, str, str, str]:
    ipv4 = ipaddress.ip_network(f"10.0.{link_id}.0/31")
    ipv6 = ipaddress.ip_network(f"2001:db8:1000:{link_id}::/127")
    return (
        f"{ipv4[0]}/31",
        f"{ipv4[1]}/31",
        f"{ipv6[0]}/127",
        f"{ipv6[1]}/127",
    )


def main() -> None:
    nodes = read_csv(NODES_FILE)
    links = read_csv(LINKS_FILE)
    node_by_name = {node["name"]: node for node in nodes}
    if len(node_by_name) != len(nodes):
        raise SystemExit("Duplicate node name detected")

    attachments: dict[str, list[dict[str, object]]] = defaultdict(list)
    next_port: dict[str, int] = defaultdict(lambda: 1)
    rendered_links: list[tuple[str, int, str, int]] = []

    for link in links:
        a, b = link["a"], link["b"]
        if a not in node_by_name or b not in node_by_name:
            raise SystemExit(f"Unknown endpoint in link {link['id']}: {a}, {b}")
        a_port, b_port = next_port[a], next_port[b]
        next_port[a] += 1
        next_port[b] += 1
        a4, b4, a6, b6 = link_addresses(int(link["id"]))
        metric = int(link["metric"])
        attachments[a].append(
            {"peer": b, "port": a_port, "ipv4": a4, "ipv6": a6, "metric": metric, "id": link["id"], "purpose": link["purpose"]}
        )
        attachments[b].append(
            {"peer": a, "port": b_port, "ipv4": b4, "ipv6": b6, "metric": metric, "id": link["id"], "purpose": link["purpose"]}
        )
        rendered_links.append((a, a_port, b, b_port))

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    TOPOLOGY_FILE.parent.mkdir(parents=True, exist_ok=True)
    ADDRESSING_FILE.parent.mkdir(parents=True, exist_ok=True)

    for node in nodes:
        name = node["name"]
        router_id = node["loopback_ipv4"].split("/")[0]
        lines = [
            f"set system host-name {name}",
            f"set routing-options router-id {router_id}",
            f"set interfaces lo0 unit 0 description \"{node['role']} ROUTER-ID\"",
            f"set interfaces lo0 unit 0 family inet address {node['loopback_ipv4']}",
            f"set interfaces lo0 unit 0 family inet6 address {node['loopback_ipv6']}",
            f"set interfaces lo0 unit 0 family iso address {node['isis_net']}",
            "set protocols isis level 1 disable",
            "set protocols isis level 2 wide-metrics-only",
            "set protocols isis topologies ipv6-unicast",
            "set protocols isis interface lo0.0 passive",
        ]
        for item in attachments[name]:
            interface = f"ge-0/0/{item['port']}"
            lines.extend(
                [
                    f"set interfaces {interface} description \"{item['purpose']} -> {item['peer']}\"",
                    f"set interfaces {interface} unit 0 family inet address {item['ipv4']}",
                    f"set interfaces {interface} unit 0 family inet6 address {item['ipv6']}",
                    f"set interfaces {interface} unit 0 family iso",
                    f"set protocols isis interface {interface}.0 point-to-point",
                    f"set protocols isis interface {interface}.0 level 2 metric {item['metric']}",
                    f"set protocols isis interface {interface}.0 level 2 ipv6-unicast metric {item['metric']}",
                ]
            )
        (CONFIG_DIR / f"{name}.set").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    topology = [
        f"name: {LAB_NAME}",
        "",
        "mgmt:",
        f"  network: {MGMT_NETWORK}",
        f"  ipv4-subnet: {MGMT_SUBNET}",
        "",
        "topology:",
        "  defaults:",
        "    kind: juniper_vmx",
        "    image: vrnetlab/vr-vmx:21.3R1.9-prepared",
        "",
        "  nodes:",
    ]
    for node in nodes:
        topology.extend(
            [
                f"    {node['name']}:",
                f"      mgmt-ipv4: {node['mgmt_ipv4']}",
                f"      startup-config: ../configs/{CONFIG_SUBDIR}/{node['name']}.set",
                f"      startup-delay: {node['startup_delay']}",
            ]
        )
    if AUTO1_IP:
        topology.extend(
            [
                "    AUTO1:",
                "      kind: linux",
                "      image: jncie-sp-automation:1.0",
                f"      mgmt-ipv4: {AUTO1_IP}",
                "      binds:",
                "        - ../:/workspace/jncie-sp-master",
            ]
        )
    topology.extend(["", "  links:"])
    for a, a_port, b, b_port in rendered_links:
        topology.append(f'    - endpoints: ["{a}:eth{a_port}", "{b}:eth{b_port}"]')
    TOPOLOGY_FILE.write_text("\n".join(topology) + "\n", encoding="utf-8", newline="\n")

    doc = [
        "# Master Lab Addressing Plan",
        "",
        "Generated from `inventory/nodes.csv` and `inventory/links.csv`. Do not edit generated configs directly.",
        "",
        "## Infrastructure blocks",
        "",
        "| Function | Prefix | Rationale |",
        "| --- | --- | --- |",
        f"| Management | {MGMT_SUBNET} | Out-of-band Containerlab access |",
        "| IPv4 loopbacks | 10.255.0.0/24 | Stable router IDs and protocol endpoints |",
        "| IPv4 P2P | 10.0.0.0/8 sliced into /31 | Address-efficient RFC 3021 links |",
        "| IPv6 loopbacks | 2001:db8:500:abcd::/64 sliced into /128 | Documentation-only infrastructure IDs |",
        "| IPv6 P2P | 2001:db8:1000::/48 sliced into /127 | RFC 6164 point-to-point links |",
        "| IS-IS area | 49.0001 | Single Level 2 provider domain |",
        "",
        "## Nodes",
        "",
        "| Node | Role | Management | IPv4 loopback | IPv6 loopback | IS-IS NET |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for node in nodes:
        doc.append(
            f"| {node['name']} | {node['role']} | {node['mgmt_ipv4']} | {node['loopback_ipv4']} | {node['loopback_ipv6']} | `{node['isis_net']}` |"
        )
    doc.extend(
        [
            "",
            "## Links",
            "",
            "| ID | Purpose | Endpoint A | IPv4 A | IPv6 A | Endpoint B | IPv4 B | IPv6 B | Metric |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for link, rendered in zip(links, rendered_links):
        a, a_port, b, b_port = rendered
        a4, b4, a6, b6 = link_addresses(int(link["id"]))
        doc.append(
            f"| {link['id']} | {link['purpose']} | {a} ge-0/0/{a_port} | {a4} | {a6} | {b} ge-0/0/{b_port} | {b4} | {b6} | {link['metric']} |"
        )
    ADDRESSING_FILE.write_text("\n".join(doc) + "\n", encoding="utf-8", newline="\n")
    print(f"Generated profile={PROFILE}: {len(nodes)} nodes, {len(links)} links, {len(nodes)} configs")


if __name__ == "__main__":
    main()
