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

The runtime gate is deliberately strict. It exits with code `2` before Docker
inspection if either credential is absent, exits with code `1` when any
acceptance check fails, and returns `0` only after every Junos router and AUTO1
pass. The generated JSON contains raw structured evidence; the companion
Markdown report exposes the overall result and per-node failures.

Each Junos router must satisfy all applicable checks:

- its expected Containerlab container is running and PyEZ connects;
- every discovered FPC is `Online`, and at least one FPC is reported;
- no active system alarm exists;
- all inventory-defined physical interfaces are operational;
- for the `isis` baseline, all directly connected IS-IS peers are observed;
- every remote provider loopback has an IPv4 and IPv6 route;
- every remote provider loopback answers a three-probe IPv4 and IPv6 ping.

AUTO1 must be running and `/tmp/verify_stack.py` must complete successfully
inside the container. Container presence alone is never considered acceptance.
A physical IS-IS link creates two neighbor endpoint observations: 13 daily
links produce 26 observations, 18 optimized links produce 36, and 25 master
links produce 50.

Unit tests under `tests/test_runtime.py` exercise credentials, FPC state,
alarms, AUTO1, routes, pings and Markdown reporting with PyEZ-compatible mocks.
They validate logic only and are not a substitute for local vMX evidence.

Runtime reports are ignored because they can expose local names or operational
data. Sanitize evidence before publication.
