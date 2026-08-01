"""Central profile metadata for generation, validation, and operations."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Profile:
    name: str
    nodes: Path
    links: Path
    topology: Path
    configs: Path
    addressing: Path
    lab_name: str
    management_network: str
    management_subnet: str
    auto1_address: str
    expected_routers: int
    expected_links: int


PROFILES = {
    "daily": Profile("daily", ROOT / "inventory/daily-nodes.csv", ROOT / "inventory/daily-links.csv", ROOT / "topology/jncie-sp-daily.clab.yml", ROOT / "configs/daily", ROOT / "docs/DAILY-ADDRESSING-PLAN.md", "jncie-sp-daily", "jncie-sp-daily-mgmt", "10.204.251.0/24", "10.204.251.10", 8, 13),
    "optimized": Profile("optimized", ROOT / "inventory/optimized-nodes.csv", ROOT / "inventory/optimized-links.csv", ROOT / "topology/jncie-sp-optimized.clab.yml", ROOT / "configs/optimized", ROOT / "docs/OPTIMIZED-ADDRESSING-PLAN.md", "jncie-sp-optimized", "jncie-sp-optimized-mgmt", "10.204.252.0/24", "10.204.252.10", 10, 18),
    "master": Profile("master", ROOT / "inventory/nodes.csv", ROOT / "inventory/links.csv", ROOT / "topology/jncie-sp-master.clab.yml", ROOT / "configs/base", ROOT / "docs/ADDRESSING-PLAN.md", "jncie-sp-master", "jncie-sp-master-mgmt", "10.204.253.0/24", "10.204.253.10", 14, 25),
}

ALIASES = {"full": "master"}
BASELINES = {"mgmt-only", "isis"}


def resolve_profile(name: str) -> Profile:
    canonical = ALIASES.get(name, name)
    if canonical not in PROFILES:
        choices = ", ".join(sorted((*PROFILES, *ALIASES)))
        raise ValueError(f"Unsupported profile {name!r}; choose one of: {choices}")
    return PROFILES[canonical]


def resolve_baseline(name: str) -> str:
    if name not in BASELINES:
        raise ValueError("Baseline must be 'mgmt-only' or 'isis'; scenario state is applied separately")
    return name
