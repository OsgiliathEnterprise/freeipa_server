## Context

See proposal.md for motivation. The role's tasks live in `tasks/prereq.yml`, `tasks/facts.yml`, `tasks/freeipa-server.yml`, and `tasks/post-install.yml`; molecule scenarios are under `molecule/{default,kvm,parallels}/`. Current `changed_when` usages:

- `facts.yml` — `hostname` command (read-only) → `changed_when: False`
- `freeipa-server.yml` — `ipa-acme-manage status` (read-only) → `changed_when: False`; `ipa-acme-manage enable` (state-changing, gated by `when:` on ACME being disabled) → stdout-parsing `changed_when` flagged as wrong in an inline comment
- `prereq.yml` — `nmcli general reload` (state-changing) → blanket `changed_when: false`
- `post-install.yml` — restart `systemd-resolved` via `state: restarted` (always reports changed) → suppressed with blanket `changed_when: false`

The molecule `test_sequence` in all three scenarios has `- idempotence` commented out. Included external roles (`freeipa.ansible_freeipa.ipaserver`, `tcharl.ansible_hostname`, `tcharl.ansible_routing`) are not editable here but their change reporting affects the converge result.

## Goals / Non-Goals

**Goals**
- Every task's reported change status reflects whether it actually modified state; no blanket suppression on state-changing tasks.
- A second converge against an already-configured host reports zero changed tasks.
- The molecule `idempotence` step is enabled in all scenarios and passes.

**Non-Goals**
- Rewriting the included external roles' internals (out of scope; we can only gate/scope from this role).
- Changing what the role configures (hostname, DNS, services, ACME) — behavior stays identical, only change-reporting and conditionality improve.

## Decisions

### Decision 1: Classify each `changed_when` as read-only vs state-changing
Keep `changed_when: false` **only** for strictly read-only tasks (`facts.yml` hostname lookup, `freeipa-server.yml` ACME status check) — there it is exact because the task has no side effects. Replace it on every state-changing task with an exact condition or a gate.

- *Alternative considered:* leave all as `false`. Rejected — that is precisely the shortcut being removed; it hides real changes and gives false confidence in idempotency.

### Decision 2: Make the `systemd-resolved` restart conditional on config change
Register the DNS template task's result, then gate the restart with `when: <template_task>.changed`. Use `state: restarted` only when the template actually changed; drop the blanket `changed_when: false`. On a re-run where `/etc/systemd/resolved.conf.d/head.conf` is already correct, the template reports no change → the restart task is skipped → nothing reported as changed.

- *Alternative considered:* always restart and suppress with `changed_when: false`. Rejected — not accurate (a restart did happen) and masks drift.
- *Alternative considered:* use a `systemd` check/reload instead of restart. Noted; `restarted` gated on change is the minimal, behavior-preserving fix.

### Decision 3: Make the ACME activation exact by relying on its existing gate
The enable task already runs only when `when: 'ACME is disabled' in <status>.stdout`. Within that gate, running the command always results in a state change, so set `changed_when` to reflect "ran ⇒ changed" (e.g. `true`) and remove the unreliable stdout-success-message parsing and its misleading comment. Keep `failed_when` for genuine failures. On a re-run ACME is enabled → the gate is false → task skipped → no change reported.

- *Alternative considered:* keep parsing stdout for a success string. Rejected — the inline comment documents that the command returns the same output on first and repeat runs, so it cannot distinguish "changed" from "already enabled".

### Decision 4: Make `nmcli general reload` idempotent
The reload exists to make NetworkManager rely on `systemd-resolved`. Recommended approach: gate the reload on an observable end-state check (NetworkManager not yet configured to use `systemd-resolved`) so it is a no-op and reports no change when already set up. If a reliable detection signal proves unavailable during implementation, fall back to running the reload only when the related resolver configuration was actually written/changed in this run.

- *Alternative considered:* keep always-running with `changed_when: false`. Rejected — same shortcut problem as Decision 2; it reports nothing even though a reload executed.
- The exact detection mechanism is confirmed empirically during implementation (see Open Questions).

### Decision 5: Enable the molecule `idempotence` step in all scenarios
Uncomment `- idempotence` in `molecule/{default,kvm,parallels}/molecule.yml` `test_sequence`. Iterate on converge until a second run reports zero changed tasks. If an included external role is inherently non-idempotent and cannot be gated from this role, scope the check or document the residual as a known limitation rather than masking it with blanket suppression.

- *Alternative considered:* enable only in `default`. Rejected — all three scenarios share the same converge; leaving two disabled hides regressions.

## Risks / Trade-offs

- [Included external roles report spurious changes on re-run, failing the molecule idempotence check] → Mitigation: run molecule during implementation and gate/scope from this role where possible; document any residual that cannot be fixed here.
- [`nmcli general reload` has no clean "did anything change" signal] → Mitigation: Decision 4's end-state gating; confirm the detection mechanism empirically before finalizing.
- [Gating the `systemd-resolved` restart on template `.changed` could skip a needed restart if the file is correct but the service is stale] → Mitigation: acceptable trade-off for idempotency; a genuinely changed config still triggers the restart, and first-run always writes the file (reports change) so the initial restart happens.
- [Behavioral drift risk from removing blanket `changed_when: false`] → Mitigation: changes are limited to change-reporting and conditionality; configured end-state is unchanged, verified by existing molecule verify tests.

## Migration Plan

No data migration. Changes are confined to task files and molecule configs. Rollback = revert the affected files. Because behavior (end-state) is preserved, no downstream coordination is required; the only observable difference is more accurate `changed` reporting and a passing idempotence check.

## Open Questions

- What is the most reliable observable signal that NetworkManager already relies on `systemd-resolved`, to gate the reload in Decision 4? (Answer empirically during implementation without changing the spec.)
- Do any included external roles (`ipaserver`, `ansible_hostname`, `ansible_routing`) report changes on a no-op re-run, and can each be gated from this role? (Determined by running molecule; affects whether Decision 5 needs scoping.)
