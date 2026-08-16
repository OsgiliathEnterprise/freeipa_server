## Why

The `tcharl.freeipa_server` role is not reliably idempotent and does not report changes accurately. Several state-changing tasks use a blanket `changed_when: false` as a shortcut (e.g. the `systemd-resolved` restart in `post-install.yml`, the `nmcli general reload` in `prereq.yml`), so real changes are silently suppressed, and one task (`ipa-acme-manage enable`) uses an unreliable stdout-parsing `changed_when` that is flagged as wrong in an inline comment. Because of this, the molecule `idempotence` step is commented out in every scenario — we cannot prove a second converge makes no changes. We want the role to be genuinely idempotent with truthful change reporting and a passing idempotence test.

## What Changes

- Replace blanket `changed_when: false` on **state-changing** tasks with exact conditions that reflect whether system state actually changed in this run.
- Audit every existing `changed_when` in the role; keep `false` only where the task is genuinely read-only (e.g. `hostname`, `ipa-acme-manage status`).
- Fix the ACME activation task (`freeipa-server.yml`) whose `changed_when` parses stdout and is marked wrong; make its change reporting exact given it is already gated to run only when ACME is disabled.
- Make the `systemd-resolved` restart in `post-install.yml` conditional on the DNS config template actually changing, instead of always restarting and suppressing with `changed_when: false`.
- Make the `nmcli general reload` in `prereq.yml` idempotent (only run / report changed when a reload is genuinely needed).
- Enable the molecule `idempotence` step in all scenarios (`default`, `kvm`, `parallels`) and ensure a second converge reports zero changed tasks so the check passes.

## Capabilities

### New Capabilities
- `idempotence`: The role's execution must be idempotent with accurate change reporting — re-running the role when system state already matches the desired state SHALL report no changes, each task's change status SHALL reflect whether it actually modified state (no blanket suppression on state-changing tasks), and the molecule test suite SHALL include a passing `idempotence` check.

### Modified Capabilities
<!-- No existing specs exist under openspec/specs/; nothing to modify. -->

## Impact

- `tasks/prereq.yml` — exact/idempotent handling of `nmcli general reload`.
- `tasks/post-install.yml` — conditional `systemd-resolved` restart tied to template change.
- `tasks/freeipa-server.yml` — corrected ACME activation `changed_when`; read-only status check kept accurate.
- `molecule/default/molecule.yml`, `molecule/kvm/molecule.yml`, `molecule/parallels/molecule.yml` — enable the `idempotence` step in `test_sequence`.
- Possibly additional gating so included external roles (`freeipa.ansible_freeipa.ipaserver`, `tcharl.ansible_hostname`, `tcharl.ansible_routing`) do not report spurious changes on a re-run, if the molecule idempotence run surfaces them.
