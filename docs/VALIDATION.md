# Validation and Acceptance

## Static acceptance

Run from the repository root:

```bash
python3 -m compileall -q tools automation tests
python3 tools/build_lab.py --profile daily --baseline isis
python3 tools/validate_artifacts.py --profile daily --baseline isis
python3 tools/build_lab.py --profile optimized --baseline isis
python3 tools/validate_artifacts.py --profile optimized --baseline isis
python3 tools/build_lab.py --profile master --baseline isis
python3 tools/validate_artifacts.py --profile master --baseline isis
python3 -m pytest -q
git diff --check
git diff --exit-code
```

Static validation parses CSV and YAML, validates addressing, stable ports,
startup references, minimal-baseline boundaries, graph redundancy and generated
documentation. GitHub-hosted CI never boots licensed vMX software.

## Runtime acceptance

After one profile is healthy, export credentials without committing them:

```bash
export JUNOS_USERNAME=admin
read -rsp "Junos password: " JUNOS_PASSWORD; export JUNOS_PASSWORD; echo
python3 automation/scripts/validate_runtime.py --profile daily --baseline isis
```

The optional PyEZ report checks container presence, SSH/facts and alarms and
captures host memory/load in JSON and Markdown. Protocol-specific scenario
checks should additionally validate RE responsiveness, FPC state, interfaces,
routes, IPv4/IPv6 loopbacks and expected neighbor count per router. A physical
IS-IS link creates two neighbor endpoint observations: 13 daily links produce
26 observations, 18 optimized links produce 36, and 25 master links produce 50.

Runtime reports are ignored because they can expose local names or operational
data. Sanitize evidence before publication.
