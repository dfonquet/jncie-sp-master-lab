# Scenario Framework

Scenarios add an initial or faulty state to a generated physical profile. They
never become part of the normal baseline and solutions are never applied by
default.

## Contract

Each scenario directory may contain `task.md`, `metadata.yml`, `initial/`,
`faults/`, `checks/`, `solution/`, `cleanup/`, and ignored local `evidence/`.
Metadata uses: `id`, `title`, `domain`, `objectives`, `difficulty`,
`estimated_minutes`, `profile`, `baseline`, `logical_roles`, `prerequisites`,
`status`, and `runtime_validated`. Status is one of `Planned`, `Implemented`,
`Statically validated`, `Runtime validated`, `Blocked by image`, or
`Out of scope`.

The initial catalog maps every public JPR-962 objective to a scenario ID in
[Blueprint Coverage](../docs/BLUEPRINT-COVERAGE.md). The five foundational
examples below define tasks but deliberately contain no automatically applied
solution.

| ID | Domain | Exercise | Status |
| --- | --- | --- | --- |
| CORE-ISIS-001 | Core Technologies | IS-IS adjacency failure | Implemented |
| CORE-POLICY-001 | Core Technologies | Import/export policy defect | Implemented |
| CORE-BFD-001 | Core Technologies | BFD detection | Implemented |
| CORE-BGP-AUTH-001 | Core Technologies | BGP authentication mismatch | Implemented |
| CORE-RIB-GROUP-001 | Core Technologies | RIB-group route sharing | Implemented |

Use `mgmt-only` when the underlay itself is part of the task and `isis` for a
focused technology exercise. Capture runtime evidence locally and sanitize it
before publication.
