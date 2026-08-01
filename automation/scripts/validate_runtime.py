#!/usr/bin/env python3
"""Optional local runtime acceptance using Docker and Junos PyEZ."""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


def command(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--profile", choices=("daily", "optimized", "master"), default="daily"); parser.add_argument("--baseline", choices=("mgmt-only", "isis"), default="isis"); parser.add_argument("--output", type=Path, default=ROOT / "automation/reports/runtime.json"); args = parser.parse_args()
    sys_path = ROOT / "tools"; import sys; sys.path.insert(0, str(sys_path))
    from profiles import resolve_profile
    profile = resolve_profile(args.profile)
    with profile.nodes.open(newline="", encoding="utf-8") as stream: nodes = list(csv.DictReader(stream))
    with profile.links.open(newline="", encoding="utf-8") as stream: links = list(csv.DictReader(stream))
    expected_ports: dict[str, set[str]] = {node["name"]: set() for node in nodes}
    for link in links:
        expected_ports[link["a"]].add(f"ge-0/0/{link['a_port']}")
        expected_ports[link["b"]].add(f"ge-0/0/{link['b_port']}")
    running = set(command("docker", "ps", "--format", "{{.Names}}").splitlines())
    report: dict[str, Any] = {"profile": args.profile, "baseline": args.baseline, "timestamp": datetime.now(timezone.utc).isoformat(), "nodes": {}, "host": {}}
    report["host"]["memory"] = command("free", "-h"); report["host"]["load"] = command("uptime")
    password = os.environ.get("JUNOS_PASSWORD"); username = os.environ.get("JUNOS_USERNAME", "admin")
    for node in nodes:
        container = f"clab-{profile.lab_name}-{node['name']}"; result: dict[str, Any] = {"container_running": container in running}
        if result["container_running"] and password:
            try:
                from jnpr.junos import Device
                with Device(host=node["mgmt_ipv4"], user=username, passwd=password, gather_facts=True) as device:
                    interfaces = device.rpc.get_interface_information(terse=True)
                    operational = {
                        item.xpath("string(name)").strip()
                        for item in interfaces.xpath(".//physical-interface[oper-status='up']")
                    }
                    expected = expected_ports[node["name"]]
                    adjacency_count = len(device.rpc.get_isis_adjacency_information().xpath(".//isis-adjacency")) if args.baseline == "isis" else 0
                    result.update({
                        "ssh": True,
                        "facts": dict(device.facts),
                        "alarms": device.rpc.get_system_alarm_information().xpath("string(.)").strip(),
                        "fpc": device.rpc.get_fpc_information().xpath("string(.)").strip(),
                        "expected_interfaces": sorted(expected),
                        "missing_or_down_interfaces": sorted(expected - operational),
                        "isis_neighbor_observations": adjacency_count,
                        "expected_isis_neighbor_observations": len(expected) if args.baseline == "isis" else 0,
                        "ipv4_loopback_present": bool(device.rpc.get_route_information(destination=node["loopback_ipv4"].split("/")[0]).xpath(".//rt")),
                        "ipv6_loopback_present": bool(device.rpc.get_route_information(destination=node["loopback_ipv6"].split("/")[0]).xpath(".//rt")),
                    })
                    result["acceptance"] = (
                        not result["missing_or_down_interfaces"]
                        and (args.baseline != "isis" or adjacency_count == len(expected))
                        and (args.baseline != "isis" or result["ipv4_loopback_present"] and result["ipv6_loopback_present"])
                    )
            except Exception as exc: result.update({"ssh": False, "error": f"{type(exc).__name__}: {exc}"})
        else: result["ssh"] = False
        report["nodes"][node["name"]] = result
    args.output.parent.mkdir(parents=True, exist_ok=True); args.output.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    markdown = args.output.with_suffix(".md"); markdown.write_text("# Runtime Acceptance Report\n\n" + f"Profile: `{args.profile}`; baseline: `{args.baseline}`.\n\n" + "| Node | Container | SSH/PyEZ |\n| --- | --- | --- |\n" + "\n".join(f"| {name} | {data['container_running']} | {data['ssh']} |" for name, data in report["nodes"].items()) + "\n", encoding="utf-8")
    failed = [name for name, data in report["nodes"].items() if not data["container_running"] or password and (not data["ssh"] or not data.get("acceptance", False))]
    print(f"Runtime report: {args.output} and {markdown}; failed={len(failed)}")
    return 1 if failed else 0


if __name__ == "__main__": raise SystemExit(main())
