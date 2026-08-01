#!/usr/bin/env python3
"""Structural and graph validation for generated JNCIE-SP artifacts."""

from __future__ import annotations

import argparse
import csv
import ipaddress
import os
import re
from collections import defaultdict, deque
from pathlib import Path
from typing import Any

import yaml

from profiles import Profile, resolve_baseline, resolve_profile

NODE_COLUMNS = {"name", "role", "mgmt_ipv4", "loopback_ipv4", "loopback_ipv6", "isis_net", "startup_delay"}
LINK_COLUMNS = {"id", "a", "a_port", "b", "b_port", "purpose", "metric"}
ROLES = {"P", "PE", "RR"}
FORBIDDEN = ("set protocols bgp", "set protocols mpls", "set protocols ldp", "set protocols rsvp", "segment-routing", "routing-instances")
NET_RE = re.compile(r"^49\.\d{4}(?:\.\d{4}){3}\.00$")


class ValidationError(ValueError):
    """An actionable static validation failure."""


def read_csv(path: Path, required: set[str]) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValidationError(f"{path}: missing columns: {', '.join(sorted(missing))}")
        return list(reader)


def unique(rows: list[dict[str, str]], key: str, label: str) -> None:
    values = [row[key] for row in rows]
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise ValidationError(f"duplicate {label}: {', '.join(duplicates)}")


def connected(nodes: set[str], edges: list[tuple[str, str]], removed_node: str | None = None, removed_edge: tuple[str, str] | None = None) -> bool:
    remaining = nodes - ({removed_node} if removed_node else set())
    if not remaining:
        return True
    graph: dict[str, set[str]] = defaultdict(set)
    for a, b in edges:
        if removed_node in (a, b) or removed_edge and {a, b} == set(removed_edge):
            continue
        graph[a].add(b); graph[b].add(a)
    seen = set(); queue = deque([next(iter(remaining))])
    while queue:
        node = queue.popleft()
        if node in seen: continue
        seen.add(node); queue.extend(graph[node] - seen)
    return seen == remaining


def graph_summary(nodes: list[dict[str, str]], links: list[dict[str, str]]) -> dict[str, Any]:
    roles = {row["name"]: row["role"] for row in nodes}
    core = {name for name, role in roles.items() if role == "P"}
    core_edges = [(row["a"], row["b"]) for row in links if row["a"] in core and row["b"] in core]
    bridges = [edge for edge in core_edges if not connected(core, core_edges, removed_edge=edge)]
    articulation = [node for node in core if not connected(core, core_edges, removed_node=node)]
    for name, role in roles.items():
        if role in {"PE", "RR"}:
            p_links = sum(1 for row in links if name in (row["a"], row["b"]) and (row["b"] if row["a"] == name else row["a"]) in core)
            if p_links != 2:
                raise ValidationError(f"{name}: expected exactly two P-facing links, found {p_links}")
    if bridges or articulation:
        raise ValidationError(f"core redundancy failed: bridges={bridges}, articulation={articulation}")
    ring = [int(row["metric"]) for row in links if row["purpose"] == "CORE-RING"]
    chords = [int(row["metric"]) for row in links if row["purpose"] == "CORE-CHORD"]
    if chords and max(ring) >= min(chords):
        raise ValidationError("CORE-CHORD metrics must be higher than CORE-RING metrics")
    return {"core_nodes": len(core), "core_edges": len(core_edges), "bridges": bridges, "articulation": articulation}


def validate(profile: Profile, baseline: str) -> None:
    nodes = read_csv(profile.nodes, NODE_COLUMNS); links = read_csv(profile.links, LINK_COLUMNS)
    if len(nodes) != profile.expected_routers or len(links) != profile.expected_links:
        raise ValidationError(f"{profile.name}: expected {profile.expected_routers} routers/{profile.expected_links} links, found {len(nodes)}/{len(links)}")
    unique(nodes, "name", "node name"); unique(nodes, "mgmt_ipv4", "management address"); unique(nodes, "loopback_ipv4", "IPv4 loopback"); unique(nodes, "loopback_ipv6", "IPv6 loopback"); unique(nodes, "isis_net", "IS-IS NET"); unique(links, "id", "link ID")
    known = {row["name"] for row in nodes}; mgmt_net = ipaddress.ip_network(profile.management_subnet)
    for node in nodes:
        if node["role"] not in ROLES: raise ValidationError(f"{node['name']}: unsupported role {node['role']}")
        if ipaddress.ip_address(node["mgmt_ipv4"]) not in mgmt_net: raise ValidationError(f"{node['name']}: management address is outside {mgmt_net}")
        if ipaddress.ip_interface(node["loopback_ipv4"]).network.prefixlen != 32: raise ValidationError(f"{node['name']}: IPv4 loopback must be /32")
        if ipaddress.ip_interface(node["loopback_ipv6"]).network.prefixlen != 128: raise ValidationError(f"{node['name']}: IPv6 loopback must be /128")
        if not NET_RE.fullmatch(node["isis_net"]): raise ValidationError(f"{node['name']}: invalid IS-IS NET {node['isis_net']}")
        if int(node["startup_delay"]) < 0: raise ValidationError(f"{node['name']}: startup delay cannot be negative")
    endpoint_pairs: set[frozenset[str]] = set(); ports: set[tuple[str, int]] = set()
    for link in links:
        a, b = link["a"], link["b"]
        if a not in known or b not in known: raise ValidationError(f"link {link['id']}: unknown endpoint")
        if a == b: raise ValidationError(f"link {link['id']}: self-link")
        pair = frozenset((a, b))
        if pair in endpoint_pairs: raise ValidationError(f"link {link['id']}: duplicate endpoint pair {a}-{b}")
        endpoint_pairs.add(pair)
        for node, field in ((a, "a_port"), (b, "b_port")):
            try: port = int(link[field])
            except ValueError as exc: raise ValidationError(f"link {link['id']}: {field} must be an integer") from exc
            if port <= 0: raise ValidationError(f"link {link['id']}: port zero/negative is unsupported by the validated vMX image")
            if (node, port) in ports: raise ValidationError(f"link {link['id']}: duplicate port {node}:{port}")
            ports.add((node, port))
        if int(link["metric"]) <= 0: raise ValidationError(f"link {link['id']}: metric must be positive")
    summary = graph_summary(nodes, links)
    topology = yaml.safe_load(profile.topology.read_text(encoding="utf-8"))
    topo_nodes = topology["topology"]["nodes"]; topo_links = topology["topology"]["links"]
    if "AUTO1" not in topo_nodes: raise ValidationError(f"{profile.name}: AUTO1 is missing")
    if len(topo_nodes) != len(nodes) + 1 or len(topo_links) != len(links): raise ValidationError(f"{profile.name}: generated topology count mismatch")
    for node in nodes:
        expected = f"../{profile.configs.relative_to(profile.topology.parents[1]).as_posix()}/{node['name']}.set"
        if topo_nodes[node["name"]]["startup-config"] != expected: raise ValidationError(f"{node['name']}: startup-config reference mismatch")
        config = profile.configs / f"{node['name']}.set"
        if not config.exists(): raise ValidationError(f"{node['name']}: generated config missing")
        text = config.read_text(encoding="utf-8").lower()
        if baseline == "isis" and "set protocols isis" not in text: raise ValidationError(f"{node['name']}: IS-IS missing")
        if baseline == "mgmt-only" and "set protocols isis" in text: raise ValidationError(f"{node['name']}: IS-IS present in mgmt-only baseline")
        for forbidden in FORBIDDEN:
            if forbidden in text: raise ValidationError(f"{node['name']}: forbidden baseline technology: {forbidden}")
    expected_endpoints = [{"endpoints": [f"{row['a']}:eth{row['a_port']}", f"{row['b']}:eth{row['b_port']}"]} for row in sorted(links, key=lambda item: int(item["id"]))]
    if topo_links != expected_endpoints: raise ValidationError(f"{profile.name}: topology endpoints do not match explicit inventory ports")
    addressing = profile.addressing.read_text(encoding="utf-8")
    if profile.nodes.name not in addressing or profile.links.name not in addressing: raise ValidationError(f"{profile.name}: addressing source references are incorrect")
    print(f"PASS profile={profile.name} baseline={baseline}: routers={len(nodes)} links={len(links)} core_nodes={summary['core_nodes']} core_edges={summary['core_edges']} articulation=0 bridges=0")


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--profile", default=os.environ.get("JNCIE_PROFILE", "daily")); parser.add_argument("--baseline", default=os.environ.get("JNCIE_BASELINE", "isis")); args = parser.parse_args()
    try: validate(resolve_profile(args.profile), resolve_baseline(args.baseline))
    except (ValidationError, ValueError, KeyError, OSError, yaml.YAMLError) as exc:
        print(f"FAIL: {exc}"); return 1
    return 0


if __name__ == "__main__": raise SystemExit(main())
