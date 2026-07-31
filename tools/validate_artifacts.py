#!/usr/bin/env python3
"""Static acceptance checks for generated JNCIE-SP master artifacts."""

import csv
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROFILE = os.environ.get("JNCIE_PROFILE", "daily")
if PROFILE == "full":
    NODES = "inventory/nodes.csv"
    LINKS = "inventory/links.csv"
    CONFIGS = "configs/base"
    TOPOLOGY = "topology/jncie-sp-master.clab.yml"
    EXPECTED_NODES, EXPECTED_LINKS = 14, 25
elif PROFILE == "optimized":
    NODES = "inventory/optimized-nodes.csv"
    LINKS = "inventory/optimized-links.csv"
    CONFIGS = "configs/optimized"
    TOPOLOGY = "topology/jncie-sp-optimized.clab.yml"
    EXPECTED_NODES, EXPECTED_LINKS = 10, 18
elif PROFILE == "daily":
    NODES = "inventory/daily-nodes.csv"
    LINKS = "inventory/daily-links.csv"
    CONFIGS = "configs/daily"
    TOPOLOGY = "topology/jncie-sp-daily.clab.yml"
    EXPECTED_NODES, EXPECTED_LINKS = 8, 13
else:
    raise SystemExit(f"Unsupported JNCIE_PROFILE: {PROFILE}")


def rows(path: str) -> list[dict[str, str]]:
    with (ROOT / path).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


nodes = rows(NODES)
links = rows(LINKS)
assert len(nodes) == EXPECTED_NODES, f"expected {EXPECTED_NODES} nodes, found {len(nodes)}"
assert len(links) == EXPECTED_LINKS, f"expected {EXPECTED_LINKS} links, found {len(links)}"

for key in ("name", "mgmt_ipv4", "loopback_ipv4", "loopback_ipv6", "isis_net"):
    values = [node[key] for node in nodes]
    assert len(values) == len(set(values)), f"duplicate {key}"

known = {node["name"] for node in nodes}
endpoints: set[tuple[str, str]] = set()
for link in links:
    assert link["a"] in known and link["b"] in known, f"unknown endpoint in link {link['id']}"
    assert link["a"] != link["b"], f"self-link {link['id']}"

for node in nodes:
    config = ROOT / CONFIGS / f"{node['name']}.set"
    assert config.exists(), f"missing config for {node['name']}"
    text = config.read_text(encoding="utf-8").lower()
    assert "set protocols isis" in text, f"IS-IS missing on {node['name']}"
    for forbidden in ("set protocols bgp", "set protocols mpls", "set protocols ldp", "set protocols rsvp"):
        assert forbidden not in text, f"advanced protocol found on {node['name']}: {forbidden}"

topology = (ROOT / TOPOLOGY).read_text(encoding="utf-8")
assert topology.count("startup-config:") == EXPECTED_NODES
assert topology.count("- endpoints:") == EXPECTED_LINKS
assert "ge-0/0/0" not in topology

print(f"PASS profile={PROFILE}: {EXPECTED_NODES} nodes, {EXPECTED_LINKS} links, unique addressing, IS-IS-only generated base")
