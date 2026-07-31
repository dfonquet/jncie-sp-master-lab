# Contributing

Contributions should preserve the repository's core contract: deterministic
generation, a minimal dual-stack IS-IS baseline, one heavy profile at a time,
and advanced JNCIE-SP technologies left as student exercises.

Before opening a pull request:

```bash
python3 -m compileall -q tools
python3 tools/build_lab.py
python3 tools/validate_artifacts.py
git diff --check
```

For the extended profiles, set `JNCIE_PROFILE=optimized` or
`JNCIE_PROFILE=full` for both generation and validation. Never commit Junos
images, credentials, private keys, packet captures, device backups, or
Containerlab runtime state. Document image versions and live validation
evidence without redistributing licensed software.
