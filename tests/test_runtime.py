"""Unit tests for strict runtime acceptance without licensed Junos images."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_runtime", ROOT / "automation/scripts/validate_runtime.py")
runtime = importlib.util.module_from_spec(SPEC); assert SPEC.loader; SPEC.loader.exec_module(runtime)


class XML:
    def __init__(self, values: dict[str, list[object]] | None = None): self.values = values or {}
    def xpath(self, path: str): return self.values.get(path, [])


class Item:
    def __init__(self, name: str): self.name = name
    def xpath(self, path: str): return self.name if path == "string(name)" else ""


class Alarm:
    def __init__(self, alarm_class: str, description: str): self.alarm_class = alarm_class; self.description = description
    def xpath(self, path: str): return self.alarm_class if path == "string(alarm-class)" else self.description if path == "string(alarm-description)" else ""


def good_ping() -> XML: return XML({".//probes-sent/text()": ["3"], ".//probe-responses/text()": ["3"]})


def test_credentials_are_mandatory() -> None:
    with pytest.raises(ValueError, match="JUNOS_USERNAME, JUNOS_PASSWORD"):
        runtime.credentials({})
    assert runtime.credentials({"JUNOS_USERNAME": "admin", "JUNOS_PASSWORD": "secret"}) == ("admin", "secret")


def test_fpc_requires_present_and_all_online() -> None:
    assert runtime.parse_fpc(XML({".//fpc/state/text()": ["Online", "Online"]}))["ok"]
    assert not runtime.parse_fpc(XML({".//fpc/state/text()": ["Online", "Offline"]}))["ok"]
    assert not runtime.parse_fpc(XML())["ok"]


def test_active_alarm_is_a_failure() -> None:
    clear = runtime.parse_alarms(XML({".//alarm-detail": []})); assert clear["ok"]
    active = runtime.parse_alarms(XML({".//alarm-detail": [Alarm("Major", "FPC offline")]}))
    assert not active["ok"] and active["active"][0]["class"] == "Major"


def test_ping_requires_zero_loss() -> None:
    assert runtime.ping_ok(good_ping())
    assert not runtime.ping_ok(XML({".//probes-sent/text()": ["3"], ".//probe-responses/text()": ["2"]}))


def test_auto1_checks_container_and_stack() -> None:
    calls: list[tuple[str, ...]] = []
    def runner(*args: str) -> str:
        calls.append(args)
        return "clab-jncie-sp-daily-AUTO1\n" if args[1] == "ps" else "stack ok\n"
    result = runtime.inspect_auto1("jncie-sp-daily", runner)
    assert result["ok"] and any(call[1] == "exec" for call in calls)


def test_validate_device_checks_remote_routes_and_dual_stack_pings() -> None:
    nodes = [
        {"name": "P1", "loopback_ipv4": "10.255.0.1/32", "loopback_ipv6": "2001:db8:ffff::1/128"},
        {"name": "P2", "loopback_ipv4": "10.255.0.2/32", "loopback_ipv6": "2001:db8:ffff::2/128"},
    ]
    rpc = SimpleNamespace(
        get_interface_information=lambda **_: XML({".//physical-interface[oper-status='up']": [Item("ge-0/0/1")]}),
        get_fpc_information=lambda: XML({".//fpc/state/text()": ["Online", "Online"]}),
        get_system_alarm_information=lambda: XML({".//alarm-detail": []}),
        get_isis_adjacency_information=lambda: XML({".//system-name/text()": ["P2.00"]}),
        get_route_information=lambda **_: XML({".//rt": [object()]}),
        ping=lambda **_: good_ping(),
    )
    result = runtime.validate_device(SimpleNamespace(rpc=rpc, facts={"hostname": "P1"}), nodes[0], nodes, {"ge-0/0/1"}, {"P2"}, "isis")
    assert result["acceptance"]
    assert all(result["checks"].values())


def test_markdown_exposes_failed_acceptance() -> None:
    report = {"profile": "daily", "baseline": "isis", "acceptance": False, "auto1": {"ok": False}, "nodes": {"P1": {"container_running": True, "ssh": True, "acceptance": False, "checks": {"fpc_online": False, "alarms_clear": True, "interfaces_up": True}, "failure_reasons": ["fpc_online"]}}}
    markdown = runtime.markdown_report(report)
    assert "Overall acceptance: **FAIL**" in markdown and "`P1`: fpc_online" in markdown
