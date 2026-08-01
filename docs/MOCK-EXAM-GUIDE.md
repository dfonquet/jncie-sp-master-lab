# Six-Hour Mock Exam Workflow

This independently authored workflow uses public JPR-962 objectives and normal
Junos engineering practice. It does not reproduce confidential exam content.

## Lifecycle

1. Generate `master` with `mgmt-only` for a full-build exam, or `isis` for a
   services-focused exam.
2. Record a clean configuration snapshot and runtime report.
3. Select tasks from all official domains plus optional multicast.
4. Apply separately stored faults only after the candidate begins.
5. Allocate 100 points: management 20, core 45, edge 35. Multicast may replace
   part of core/edge scoring when included.
6. Run task-level checks for partial credit and an end-to-end acceptance pass.
7. Export evidence and a Markdown score report.
8. Destroy the profile and regenerate artifacts before the next attempt.

Recommended timing is 15 minutes for assessment, 315 minutes for implementation
and troubleshooting, and 30 minutes for final validation. Checks should award
independent points for configuration intent, protocol state, and service
reachability. Solutions remain outside the normal startup path.
