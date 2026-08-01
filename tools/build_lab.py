#!/usr/bin/env python3
"""Deterministically generate JNCIE-SP topology, configs, and addressing."""

from __future__ import annotations

import argparse
import csv
import ipaddress
import os
from collections import defaultdict
from pathlib import Path
from typing import Iterable

from profiles import Profile, resolve_baseline, resolve_profile


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def link_addresses(link_id: int) -> tuple[str, str, str, str]:
    ipv4 = ipaddress.ip_network(f"10.0.{link_id}.0/31")
    ipv6 = ipaddress.ip_network(f"2001:db8:1000:{link_id}::/127")
    return f"{ipv4[0]}/31", f"{ipv4[1]}/31", f"{ipv6[0]}/127", f"{ipv6[1]}/127"


def interface(port: str | int) -> str:
    return f"ge-0/0/{int(port)}"


def render_config(node: dict[str, str], attachments: Iterable[dict[str, str]], baseline: str) -> str:
    lines = [
        f"set system host-name {node['name']}",
        "set system services ssh",
        "set system services netconf ssh",
        f"set routing-options router-id {node['loopback_ipv4'].split('/')[0]}",
    ]
    if baseline == "isis":
        lines.extend([
            f"set interfaces lo0 unit 0 description \"{node['role']} ROUTER-ID\"",
            f"set interfaces lo0 unit 0 family inet address {node['loopback_ipv4']}",
            f"set interfaces lo0 unit 0 family inet6 address {node['loopback_ipv6']}",
            f"set interfaces lo0 unit 0 family iso address {node['isis_net']}",
            "set protocols isis level 1 disable",
            "set protocols isis level 2 wide-metrics-only",
            "set protocols isis topologies ipv6-unicast",
            "set protocols isis interface lo0.0 passive",
        ])
    for item in sorted(attachments, key=lambda value: int(value["port"])):
        name = interface(item["port"])
        lines.append(f"set interfaces {name} description \"{item['purpose']} -> {item['peer']}\"")
        if baseline == "isis":
            lines.extend([
                f"set interfaces {name} unit 0 family inet address {item['ipv4']}",
                f"set interfaces {name} unit 0 family inet6 address {item['ipv6']}",
                f"set interfaces {name} unit 0 family iso",
                f"set protocols isis interface {name}.0 point-to-point",
                f"set protocols isis interface {name}.0 level 2 metric {item['metric']}",
                f"set protocols isis interface {name}.0 level 2 ipv6-unicast metric {item['metric']}",
            ])
    return "\n".join(lines) + "\n"


def generate(profile: Profile, baseline: str) -> None:
    nodes = read_csv(profile.nodes)
    links = sorted(read_csv(profile.links), key=lambda row: int(row["id"]))
    attachments: dict[str, list[dict[str, str]]] = defaultdict(list)
    for link in links:
        a4, b4, a6, b6 = link_addresses(int(link["id"]))
        for node, peer, port, ipv4, ipv6 in (
            (link["a"], link["b"], link["a_port"], a4, a6),
            (link["b"], link["a"], link["b_port"], b4, b6),
        ):
            attachments[node].append({"peer": peer, "port": port, "ipv4": ipv4, "ipv6": ipv6, "metric": link["metric"], "purpose": link["purpose"]})

    profile.configs.mkdir(parents=True, exist_ok=True)
    expected = {f"{node['name']}.set" for node in nodes}
    for stale in profile.configs.glob("*.set"):
        if stale.name not in expected:
            stale.unlink()
    for node in nodes:
        (profile.configs / f"{node['name']}.set").write_text(render_config(node, attachments[node["name"]], baseline), encoding="utf-8", newline="\n")

    topology = [
        f"name: {profile.lab_name}", "", "mgmt:",
        f"  network: {profile.management_network}", f"  ipv4-subnet: {profile.management_subnet}", "",
        "topology:", "  defaults:", "    kind: juniper_vmx", "    image: vrnetlab/vr-vmx:21.3R1.9-prepared", "", "  nodes:",
    ]
    for node in nodes:
        topology.extend([f"    {node['name']}:", f"      mgmt-ipv4: {node['mgmt_ipv4']}", f"      startup-config: ../{profile.configs.relative_to(profile.topology.parents[1]).as_posix()}/{node['name']}.set", f"      startup-delay: {node['startup_delay']}"])
    topology.extend(["    AUTO1:", "      kind: linux", "      image: jncie-sp-automation:1.0", f"      mgmt-ipv4: {profile.auto1_address}", "      binds:", "        - ../:/workspace/jncie-sp-master", "", "  links:"])
    for link in links:
        topology.append(f'    - endpoints: ["{link["a"]}:eth{link["a_port"]}", "{link["b"]}:eth{link["b_port"]}"]')
    profile.topology.write_text("\n".join(topology) + "\n", encoding="utf-8", newline="\n")

    doc = [
        f"# {profile.name.title()} Profile Addressing Plan", "",
        f"> Generated from `{profile.nodes.relative_to(profile.nodes.parents[1]).as_posix()}` and `{profile.links.relative_to(profile.links.parents[1]).as_posix()}`. Do not edit this artifact manually.", "",
        f"Baseline: `{baseline}`. Management network: `{profile.management_subnet}`.", "", "## Nodes", "",
        "| Node | Role | Management | IPv4 loopback | IPv6 loopback | IS-IS NET |", "| --- | --- | --- | --- | --- | --- |",
    ]
    doc.extend(f"| {n['name']} | {n['role']} | {n['mgmt_ipv4']} | {n['loopback_ipv4']} | {n['loopback_ipv6']} | `{n['isis_net']}` |" for n in nodes)
    doc.extend(["", "## Links", "", "| ID | Purpose | Endpoint A | IPv4 A | IPv6 A | Endpoint B | IPv4 B | IPv6 B | Metric |", "| --- | --- | --- | --- | --- | --- | --- | --- | ---: |"])
    for link in links:
        a4, b4, a6, b6 = link_addresses(int(link["id"]))
        doc.append(f"| {link['id']} | {link['purpose']} | {link['a']} {interface(link['a_port'])} | {a4} | {a6} | {link['b']} {interface(link['b_port'])} | {b4} | {b6} | {link['metric']} |")
    profile.addressing.write_text("\n".join(doc) + "\n", encoding="utf-8", newline="\n")
    print(f"Generated profile={profile.name} baseline={baseline}: {len(nodes)} routers, {len(links)} links, AUTO1")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", default=os.environ.get("JNCIE_PROFILE", "daily"))
    parser.add_argument("--baseline", default=os.environ.get("JNCIE_BASELINE", "isis"))
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        generate(resolve_profile(args.profile), resolve_baseline(args.baseline))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
