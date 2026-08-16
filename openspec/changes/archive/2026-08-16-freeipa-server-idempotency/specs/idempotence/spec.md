## Purpose

Defines that the FreeIPA server role converges idempotently and reports changes truthfully: re-running it against an already-configured host makes no changes, every task's change status reflects whether it actually modified system state, and the molecule suite enforces this with a passing `idempotence` check.

## ADDED Requirements

### Requirement: Idempotent re-execution
Running the role when the target host's state already matches the desired state SHALL report zero changed tasks; no task SHALL be reported as changed on a run that makes no effective modification to the system.

#### Scenario: Second converge on an already-configured host
- **WHEN** the role is converged a second time against a host whose FreeIPA server, DNS config, services, and ACME state are already in the desired state
- **THEN** the run reports zero changed tasks

#### Scenario: First converge performs setup
- **WHEN** the role is converged for the first time on an unconfigured host
- **THEN** the tasks that install/configure the server report changed, and a subsequent re-run (Scenario above) reports no changes

### Requirement: Accurate change reporting
Each task's reported change status SHALL reflect whether it actually modified system state in this run. A blanket `changed_when: false` SHALL NOT be used on any task capable of modifying state; such suppression is permitted only for tasks that are strictly read-only (no side effects).

#### Scenario: Read-only task reports no change
- **WHEN** a strictly read-only task runs (e.g. retrieving the current hostname or querying ACME status)
- **THEN** it is reported as not changed, and this reporting is accurate because the task has no side effects

#### Scenario: State-changing task reports changed only when it modifies state
- **WHEN** a task capable of modifying system state runs but finds the system already in the desired state
- **THEN** it is reported as not changed, and it is reported as changed only on the run that actually performs the modification

### Requirement: Conditional DNS resolver restart
The `systemd-resolved` service SHALL be restarted only when the internal-domain DNS configuration written by the role changes during this run; when the configuration is already correct, no restart SHALL occur.

#### Scenario: DNS config unchanged
- **WHEN** the role runs and the generated DNS configuration file already matches the desired content
- **THEN** `systemd-resolved` is not restarted and no change is reported for it

#### Scenario: DNS config changed
- **WHEN** the role writes a new or modified DNS configuration file
- **THEN** `systemd-resolved` is restarted and the restart is reported as changed

### Requirement: Idempotent NetworkManager reload
The NetworkManager reload SHALL have no effect (and report no change) when NetworkManager is already configured to rely on `systemd-resolved`; it SHALL act only when that configuration is not yet in place.

#### Scenario: Reload unnecessary
- **WHEN** the role runs and NetworkManager is already configured as desired
- **THEN** no reload-induced change is reported

### Requirement: Accurate ACME activation
ACME enablement SHALL report changed only on the run that actually enables it, and SHALL NOT re-run or re-report when ACME is already enabled. The change decision SHALL NOT depend on parsing an unreliable success message from the command output.

#### Scenario: First run enables ACME
- **WHEN** the role runs and ACME is currently disabled
- **THEN** ACME is enabled and the task is reported as changed

#### Scenario: ACME already enabled
- **WHEN** the role runs and ACME is already enabled
- **THEN** the enablement task does not run and no change is reported for it

### Requirement: Molecule idempotence enforcement
The molecule test suite SHALL include an `idempotence` step in the test sequence of every scenario, and that step SHALL pass by confirming a second converge reports zero changed tasks.

#### Scenario: Idempotence step present and passing
- **WHEN** `molecule test` is run for any scenario (`default`, `kvm`, or `parallels`)
- **THEN** the `idempotence` step executes and passes, with the second converge reporting no changes
