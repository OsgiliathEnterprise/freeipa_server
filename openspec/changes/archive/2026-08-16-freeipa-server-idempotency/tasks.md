## 1. Audit change reporting

- [x] 1.1 Inventory every `changed_when` in `tasks/` and classify each task as read-only or state-changing (read-only: `facts.yml` hostname lookup, `freeipa-server.yml` ACME status check; state-changing: `prereq.yml` nmcli reload, `post-install.yml` systemd-resolved restart, `freeipa-server.yml` ACME enable)
- [x] 1.2 Confirm read-only tasks keep `changed_when: false` (exact for no-side-effect commands); record any task whose classification is ambiguous

## 2. Make state-changing tasks exact and idempotent

- [x] 2.1 In `tasks/post-install.yml`, register the DNS template task result and gate the `systemd-resolved` restart with `when: <template_task>.changed`; remove the blanket `changed_when: false` so a restart is reported only when the config actually changed
- [x] 2.2 In `tasks/freeipa-server.yml`, replace the stdout-parsing ACME activation `changed_when` (and its misleading comment) with an exact "ran ⇒ changed" condition, keeping the existing `when:` gate on ACME being disabled and the `failed_when` for genuine failures
- [x] 2.3 In `tasks/prereq.yml`, make `nmcli general reload` idempotent by gating it on an observable end-state check (NetworkManager not yet relying on `systemd-resolved`) so it is a no-op / reports no change when already configured; if no reliable signal exists, gate it on the related resolver config being written/changed this run
- [x] 2.4 Verify no state-changing task retains a blanket `changed_when: false`

## 3. Enable molecule idempotence

- [x] 3.1 Uncomment `- idempotence` in `molecule/default/molecule.yml` `test_sequence`
- [x] 3.2 Uncomment `- idempotence` in `molecule/kvm/molecule.yml` `test_sequence`
- [x] 3.3 Uncomment `- idempotence` in `molecule/parallels/molecule.yml` `test_sequence`

## 4. Verify everything works

- [x] 4.1 Ran `molecule test -s parallels` (the fully-supported scenario in this environment; the `default`/VirtualBox scenario needs the `vagrant-virtualbox` plugin, which is not installed here). Converge passed on a fresh fedora-43 VM (`ok=44 changed=11`).
- [x] 4.2 **This role's tasks produced 0 spurious changes on re-converge** — verified idempotent (post-install DNS/restart, prereq nmcli gate, ACME enable all no-op on the second run). Residual that cannot be fixed from this role: two upstream spurious-changed verify tasks in `freeipa.ansible_freeipa.ipaserver` (`Firewalld - Verify runtime/permanent zone`, install.yml:53-64) — read-only `firewall-cmd --info-zone` shell tasks with no `changed_when: false`, so they always report `changed`. They are gated only by `ipaserver_firewalld_zone is defined`, which this role must set (it drives the real firewall config), so they cannot be scoped out without disabling required firewall configuration. **Known limitation — fix belongs upstream in `freeipa.ansible_freeipa`** (add `changed_when: false` to those two verify tasks).
- [ ] 4.3 Converge is green and this role's idempotency is verified, but the molecule built-in `idempotence` step cannot be fully green while firewalld config stays enabled, solely due to the external upstream limitation in 4.2; `verify` was not reached (molecule halts at the idempotence failure). A fully-green local run requires patching those two upstream verify tasks locally (`changed_when: false`) or tolerating them — neither is durable/committable from this role, so full green awaits the upstream fix.
