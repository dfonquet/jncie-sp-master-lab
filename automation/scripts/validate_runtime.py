#!/usr/bin/env python3
"""Strict local runtime acceptance using Docker and Junos PyEZ.

This command never treats container presence as Junos acceptance. Credentials,
AUTO1, FPC state, alarms, interfaces and protocol reachability are explicit
gates. Public CI exercises the parsers with mocks; licensed vMX runtime evidence
must be collected locally.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[2]


def command(*args: str) -> str:
    return subprocess.run(args, check=True, capture_output=True, text=True).stdout


def credentials(environ: dict[str, str] | os._Environ[str] = os.environ) -> tuple[str, str]:
    username = environ.get("JUNOS_USERNAME", "").strip()
    password = environ.get("JUNOS_PASSWORD", "")
    missing = [name for name, value in (("JUNOS_USERNAME", username), ("JUNOS_PASSWORD", password)) if not value]
    if missing:
        raise ValueError(f"Missing required runtime credential(s): {', '.join(missing)}")
    return username, password


def text_values(xml: Any, path: str) -> list[str]:
    return [value.strip() for value in xml.xpath(path) if str(value).strip()]


def parse_fpc(xml: Any) -> dict[str, Any]:
    states = [value.lower() for value in text_values(xml, ".//fpc/state/text()")]
    online = sum(value == "online" for value in states)
    return {"states": states, "total": len(states), "online": online, "ok": bool(states) and online == len(states)}


def parse_alarms(xml: Any) -> dict[str, Any]:
    details = xml.xpath(".//alarm-detail")
    alarms = []
    for detail in details:
        alarms.append({
            "class": detail.xpath("string(alarm-class)").strip() or "unknown",
            "description": detail.xpath("string(alarm-description)").strip() or "unspecified alarm",
        })
    return {"active": alarms, "count": len(alarms), "ok": not alarms}


def ping_ok(xml: Any) -> bool:
    sent = text_values(xml, ".//probes-sent/text()")
    received = text_values(xml, ".//probe-responses/text()")
    if sent and received:
        return int(received[0]) == int(sent[0]) and int(sent[0]) > 0
    loss = text_values(xml, ".//packet-loss/text()")
    return bool(loss) and loss[0].rstrip(" %") == "0"


def expected_ports_and_peers(nodes: list[dict[str, str]], links: list[dict[str, str]]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    ports = {node["name"]: set() for node in nodes}
    peers = {node["name"]: set() for node in nodes}
    for link in links:
        ports[link["a"]].add(f"ge-0/0/{link['a_port']}"); peers[link["a"]].add(link["b"])
        ports[link["b"]].add(f"ge-0/0/{link['b_port']}"); peers[link["b"]].add(link["a"])
    return ports, peers


def inspect_auto1(lab_name: str, runner: Callable[..., str] = command) -> dict[str, Any]:
    name = f"clab-{lab_name}-AUTO1"
    running = set(runner("docker", "ps", "--format", "{{.Names}}").splitlines())
    result: dict[str, Any] = {"name": name, "running": name in running, "stack": False, "ok": False}
    if result["running"]:
        try:
            runner("docker", "exec", name, "python", "/tmp/verify_stack.py")
            result["stack"] = True
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            result["error"] = f"{type(exc).__name__}: {exc}"
    result["ok"] = result["running"] and result["stack"]
    return result


def validate_device(device: Any, node: dict[str, str], nodes: list[dict[str, str]], expected_ports: set[str], expected_peers: set[str], baseline: str) -> dict[str, Any]:
    interfaces = device.rpc.get_interface_information(terse=True)
    operational = {item.xpath("string(name)").strip() for item in interfaces.xpath(".//physical-interface[oper-status='up']")}
    missing_interfaces = sorted(expected_ports - operational)
    fpc = parse_fpc(device.rpc.get_fpc_information())
    alarms = parse_alarms(device.rpc.get_system_alarm_information())
    result: dict[str, Any] = {
        "ssh": True, "facts": dict(device.facts), "fpc": fpc, "alarms": alarms,
        "expected_interfaces": sorted(expected_ports), "missing_or_down_interfaces": missing_interfaces,
        "checks": {}, "failure_reasons": [],
    }
    checks = result["checks"]
    checks.update({"interfaces_up": not missing_interfaces, "fpc_online": fpc["ok"], "alarms_clear": alarms["ok"]})
    if baseline == "isis":
        adjacency_xml = device.rpc.get_isis_adjacency_information()
        adjacency_peers = {value.split(".")[0] for value in text_values(adjacency_xml, ".//system-name/text()")}
        remote = [item for item in nodes if item["name"] != node["name"]]
        route_v4: list[str] = []; route_v6: list[str] = []; ping_v4: list[str] = []; ping_v6: list[str] = []
        for peer in remote:
            address4 = peer["loopback_ipv4"].split("/")[0]; address6 = peer["loopback_ipv6"].split("/")[0]
            if device.rpc.get_route_information(destination=address4).xpath(".//rt"): route_v4.append(peer["name"])
            if device.rpc.get_route_information(destination=address6).xpath(".//rt"): route_v6.append(peer["name"])
            if ping_ok(device.rpc.ping(host=address4, count="3", rapid=True)): ping_v4.append(peer["name"])
            if ping_ok(device.rpc.ping(host=address6, count="3", rapid=True)): ping_v6.append(peer["name"])
        result["isis"] = {"expected_peers": sorted(expected_peers), "observed_peers": sorted(adjacency_peers)}
        result["remote_reachability"] = {"expected": len(remote), "route_ipv4": route_v4, "route_ipv6": route_v6, "ping_ipv4": ping_v4, "ping_ipv6": ping_v6}
        checks.update({
            "isis_adjacencies": expected_peers <= adjacency_peers,
            "remote_ipv4_routes": len(route_v4) == len(remote), "remote_ipv6_routes": len(route_v6) == len(remote),
            "remote_ipv4_pings": len(ping_v4) == len(remote), "remote_ipv6_pings": len(ping_v6) == len(remote),
        })
    result["failure_reasons"] = [name for name, passed in checks.items() if not passed]
    result["acceptance"] = all(checks.values())
    return result


def markdown_report(report: dict[str, Any]) -> str:
    lines = ["# Runtime Acceptance Report", "", f"- Profile: `{report['profile']}`", f"- Baseline: `{report['baseline']}`", f"- Overall acceptance: **{'PASS' if report['acceptance'] else 'FAIL'}**", f"- AUTO1: **{'PASS' if report['auto1']['ok'] else 'FAIL'}**", "", "| Node | Container | PyEZ | FPC | Alarms | Interfaces | IS-IS/routes/pings | Result |", "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for name, data in report["nodes"].items():
        checks = data.get("checks", {}); protocol = all(value for key, value in checks.items() if key.startswith(("isis_", "remote_"))) if checks else False
        lines.append(f"| {name} | {data.get('container_running', False)} | {data.get('ssh', False)} | {checks.get('fpc_online', False)} | {checks.get('alarms_clear', False)} | {checks.get('interfaces_up', False)} | {protocol if report['baseline'] == 'isis' else 'N/A'} | {'PASS' if data.get('acceptance') else 'FAIL'} |")
    lines.extend(["", "## Failure reasons", ""])
    failures = [f"- `{name}`: {', '.join(data.get('failure_reasons', ['not validated']))}" for name, data in report["nodes"].items() if not data.get("acceptance")]
    if not report["auto1"]["ok"]: failures.insert(0, "- `AUTO1`: container or automation stack validation failed")
    lines.extend(failures or ["- None."])
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("daily", "optimized", "master"), default="daily")
    parser.add_argument("--baseline", choices=("mgmt-only", "isis"), default="isis")
    parser.add_argument("--output", type=Path, default=ROOT / "automation/reports/runtime.json")
    args = parser.parse_args()
    try:
        username, password = credentials()
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr); return 2
    sys.path.insert(0, str(ROOT / "tools")); from profiles import resolve_profile
    profile = resolve_profile(args.profile)
    with profile.nodes.open(newline="", encoding="utf-8") as stream: nodes = list(csv.DictReader(stream))
    with profile.links.open(newline="", encoding="utf-8") as stream: links = list(csv.DictReader(stream))
    ports, peers = expected_ports_and_peers(nodes, links)
    running = set(command("docker", "ps", "--format", "{{.Names}}").splitlines())
    report: dict[str, Any] = {"profile": args.profile, "baseline": args.baseline, "timestamp": datetime.now(timezone.utc).isoformat(), "nodes": {}, "host": {}, "auto1": inspect_auto1(profile.lab_name)}
    report["host"] = {"memory": command("free", "-h"), "load": command("uptime")}
    from jnpr.junos import Device
    for node in nodes:
        container = f"clab-{profile.lab_name}-{node['name']}"; result: dict[str, Any] = {"container_running": container in running, "ssh": False, "acceptance": False, "failure_reasons": []}
        if not result["container_running"]: result["failure_reasons"] = ["container_not_running"]
        else:
            try:
                with Device(host=node["mgmt_ipv4"], user=username, passwd=password, gather_facts=True) as device:
                    result.update(validate_device(device, node, nodes, ports[node["name"]], peers[node["name"]], args.baseline))
            except Exception as exc:
                result.update({"error": f"{type(exc).__name__}: {exc}", "failure_reasons": ["pyez_connection_or_rpc"]})
        report["nodes"][node["name"]] = result
    report["acceptance"] = report["auto1"]["ok"] and all(item.get("acceptance", False) for item in report["nodes"].values())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    markdown = args.output.with_suffix(".md"); markdown.write_text(markdown_report(report), encoding="utf-8")
    print(f"Runtime acceptance={'PASS' if report['acceptance'] else 'FAIL'}; JSON={args.output}; Markdown={markdown}")
    return 0 if report["acceptance"] else 1


if __name__ == "__main__": raise SystemExit(main())
