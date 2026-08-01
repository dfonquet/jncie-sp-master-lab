# Contributing

Contributions should preserve the repository's core contract: deterministic
generation, a minimal dual-stack IS-IS baseline, one heavy profile at a time,
and advanced JNCIE-SP technologies left as student exercises.

Before opening a pull request:

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

Use the canonical names `daily`, `optimized`, and `master`; `full` is accepted
only as a backward-compatible alias. Never commit Junos
images, credentials, private keys, packet captures, device backups, or
Containerlab runtime state. Document image versions and live validation
evidence without redistributing licensed software.
