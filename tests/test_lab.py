"""Regression tests for the deterministic lab model."""

from __future__ import annotations

import csv
import copy
import hashlib
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from build_lab import generate  # noqa: E402
from profiles import PROFILES, resolve_profile  # noqa: E402
from validate_artifacts import LINK_COLUMNS, NODE_COLUMNS, ValidationError, graph_summary, read_csv, validate  # noqa: E402
import validate_artifacts as validator  # noqa: E402


def digest(paths: list[Path]) -> str:
    result = hashlib.sha256()
    for path in sorted(paths):
        result.update(path.read_bytes())
    return result.hexdigest()


@pytest.mark.parametrize("name", ["daily", "optimized", "master"])
def test_profile_selection(name: str) -> None:
    assert resolve_profile(name).name == name


def test_full_alias() -> None:
    assert resolve_profile("full") is PROFILES["master"]


@pytest.mark.parametrize("name", ["daily", "optimized", "master"])
def test_generated_yaml_and_counts(name: str) -> None:
    profile = resolve_profile(name); generate(profile, "isis"); validate(profile, "isis")
    topology = yaml.safe_load(profile.topology.read_text(encoding="utf-8"))
    assert len(topology["topology"]["nodes"]) == profile.expected_routers + 1
    assert len(topology["topology"]["links"]) == profile.expected_links
    assert len(list(profile.configs.glob("*.set"))) == profile.expected_routers


@pytest.mark.parametrize("name", ["daily", "optimized", "master"])
def test_deterministic_generation(name: str) -> None:
    profile = resolve_profile(name); generate(profile, "isis")
    outputs = [profile.topology, profile.addressing, *profile.configs.glob("*.set")]
    before = digest(outputs); generate(profile, "isis"); assert digest(outputs) == before


def test_row_order_does_not_define_ports() -> None:
    links = read_csv(PROFILES["daily"].links, LINK_COLUMNS)
    expected = {(row["a"], row["a_port"], row["b"], row["b_port"]) for row in links}
    assert expected == {(row["a"], row["a_port"], row["b"], row["b_port"]) for row in reversed(links)}


def test_graph_invariants() -> None:
    for profile in PROFILES.values():
        summary = graph_summary(read_csv(profile.nodes, NODE_COLUMNS), read_csv(profile.links, LINK_COLUMNS))
        assert summary["bridges"] == [] and summary["articulation"] == []


@pytest.mark.parametrize("mutation,message", [
    ({"id": "1"}, "duplicate link ID"),
    ({"a": "UNKNOWN"}, "unknown endpoint"),
    ({"a_port": "0"}, "port zero"),
])
def test_invalid_link_data_is_detectable(mutation: dict[str, str], message: str) -> None:
    links = read_csv(PROFILES["daily"].links, LINK_COLUMNS)
    if "id" in mutation: links[1]["id"] = mutation["id"]
    else: links[0].update(mutation)
    if message == "duplicate link ID":
        values = [row["id"] for row in links]
        assert len(values) != len(set(values))
    elif message == "unknown endpoint": assert links[0]["a"] == "UNKNOWN"
    else: assert int(links[0]["a_port"]) <= 0


def test_csv_schema_failure() -> None:
    with pytest.raises(ValidationError, match="missing columns"):
        read_csv(ROOT / "tests/fixtures/bad-nodes.csv", NODE_COLUMNS)


def test_baseline_forbidden_protocols() -> None:
    generate(PROFILES["daily"], "isis")
    text = "\n".join(path.read_text(encoding="utf-8").lower() for path in PROFILES["daily"].configs.glob("*.set"))
    for forbidden in ("set protocols bgp", "set protocols mpls", "set protocols ldp", "set protocols rsvp"):
        assert forbidden not in text


@pytest.mark.parametrize(("target", "field", "value", "message"), [
    ("nodes", "name", "P1", "duplicate node name"),
    ("nodes", "mgmt_ipv4", "not-an-ip", "does not appear"),
    ("nodes", "isis_net", "49.BAD", "invalid IS-IS NET"),
    ("links", "id", "1", "duplicate link ID"),
    ("links", "a", "UNKNOWN", "unknown endpoint"),
    ("links", "a_port", "0", "port zero"),
    ("links", "a_port", "1", "duplicate port"),
])
def test_structural_rejections(monkeypatch: pytest.MonkeyPatch, target: str, field: str, value: str, message: str) -> None:
    profile = PROFILES["daily"]
    nodes = copy.deepcopy(read_csv(profile.nodes, NODE_COLUMNS)); links = copy.deepcopy(read_csv(profile.links, LINK_COLUMNS))
    index = 1 if target == "nodes" and field == "name" or target == "links" and field == "id" else 2 if target == "links" and message == "duplicate port" else 0
    (nodes if target == "nodes" else links)[index][field] = value
    original = validator.read_csv
    monkeypatch.setattr(validator, "read_csv", lambda path, required: nodes if path == profile.nodes else links if path == profile.links else original(path, required))
    with pytest.raises((ValidationError, ValueError), match=message): validator.validate(profile, "isis")
