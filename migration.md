# Poetry → uv migration notes for `tcharl.freeipa_server`

## Purpose

This document records the migration discussion, the practical conversion steps applied in this role, and the troubleshooting performed afterward.

Date range covered: 2026-06-06 to 2026-06-07.

---

## 1. Initial request

The original question was how to convert the role from a Poetry-based workflow to a `uv`-based workflow.

The relevant starting points were:

- `pyproject.toml` using Poetry metadata and dependency groups
- `tox.ini` using `poetry install`, `poetry lock`, `poetry export`, and `poetry build`
- `requirements-poetry.txt` containing the Poetry bootstrap dependency

Initial Poetry-driven `tox` behavior in `tox.ini` was:

```ini
[testenv:pipdep]
commands =
    poetry install --no-root --no-interaction --no-ansi
    poetry lock
    rm -rf requirements.txt
    poetry export -f requirements.txt --without-hashes -o requirements.txt
    rm -rf requirements-dev.txt
    poetry export -f requirements.txt --with dev --without-hashes -o requirements-dev.txt

[testenv:package]
commands =
    poetry build
```

---

## 2. Migration approach agreed on

The migration was performed in two parts:

1. Convert project metadata from Poetry-style configuration to a `uv`-compatible / PEP 621 layout.
2. Replace Poetry commands in `tox.ini` with `uv` commands.

### Command mapping used

| Poetry command | Replacement |
| --- | --- |
| `poetry lock` | `uv lock` |
| `poetry export -f requirements.txt --without-hashes -o requirements.txt` | `uv export --format requirements.txt --no-dev --no-hashes --output-file requirements.txt` |
| `poetry export -f requirements.txt --with dev --without-hashes -o requirements-dev.txt` | `uv export --format requirements.txt --all-groups --no-hashes --output-file requirements-dev.txt` |
| `poetry build` | `uv build` |
| `poetry install --no-root --no-interaction --no-ansi` | removed for this workflow |

---

## 3. Project changes applied

### 3.1 `pyproject.toml`

The project was converted to a PEP 621 style file:

- `[tool.poetry]` → `[project]`
- Poetry dependency groups → `[dependency-groups]`
- `build-system` switched from `poetry-core` to `hatchling`
- `tool.hatch` configuration added for packaging the role content
- `tool.uv` section added

Current notable settings:

- `requires-python = ">=3.11,<3.14"`
- runtime dependencies kept for:
  - `ansible`
  - `jmespath`
  - `netaddr`
- dev dependency group kept for:
  - `flake8`
  - `yamllint`
  - `tox`
  - `pytest-testinfra`
  - `python-vagrant`
  - `molecule`
  - `molecule-plugins[vagrant]`
  - `ansible-lint`

### 3.2 Metadata corrections made during migration

These corrections were necessary during migration:

- `license = "Apache2"` was normalized to `license = "Apache-2.0"`
- `ansible-lint = "v26.4.0"` was normalized to `ansible-lint==26.4.0`

### 3.3 `tox.ini`

`tox.ini` was updated to use `uv`:

```ini
[testenv:pipdep]
allowlist_externals=rm
deps =
    -r requirements-uv.txt
commands =
    uv lock
    rm -rf requirements.txt
    uv export --format requirements.txt --no-dev --no-hashes --output-file requirements.txt
    rm -rf requirements-dev.txt
    uv export --format requirements.txt --all-groups --no-hashes --output-file requirements-dev.txt

[testenv:package]
deps =
    -r requirements-uv.txt
commands =
    uv build
```

### 3.4 Bootstrap requirements file

The bootstrap file was renamed conceptually from Poetry to uv usage:

- old: `requirements-poetry.txt`
- new: `requirements-uv.txt`

The file content is now simply:

```txt
uv
```

### 3.5 Generated / lock artifacts

The following artifacts were regenerated as part of the migration:

- `uv.lock`
- `requirements.txt`
- `requirements-dev.txt`

---

## 4. Validation performed after migration

The following commands were used to validate the basic migration:

```zsh
cd /Users/charliemordant/Code/Sources/Platform/platform-2020/ansible/roles/tcharl.freeipa_server
uv lock
uv export --format requirements.txt --no-dev --no-hashes --output-file requirements.txt
uv export --format requirements.txt --all-groups --no-hashes --output-file requirements-dev.txt
uv build
tox -e pipdep,package
```

### Result

These passed successfully:

- `uv lock`
- `uv export ... requirements.txt`
- `uv export ... requirements-dev.txt`
- `uv build`
- `tox -e pipdep,package`

At this point, the role was functionally migrated for lock/export/build flows.

---

## 5. Follow-up troubleshooting request

A follow-up request asked to test a Molecule execution that had worked before the migration:

```zsh
tox -e test-exec-monorepo -- --scenario-name=parallels
```

### 5.1 Reproduced failure

The command was executed and failed quickly with this error:

```text
RuntimeError: Python 3.14 requires ansible-core version >= 2.20.0, and we found 2.18.17.
```

### 5.2 Root cause

The issue was not the `uv` lock/export/build conversion itself.

The actual regression came from how `tox` created the environment after the switch to the uv-backed runner:

- the local default `python3` on the machine is `Python 3.14.5`
- the uv-backed tox runner created `.tox/test-exec-monorepo` with Python 3.14
- the project dependency set still resolved to `ansible-core 2.18.x`
- `ansible-compat` rejects that combination under Python 3.14

So the problem was:

**tox environment interpreter selection changed after the migration, and the test env started using Python 3.14 instead of Python 3.13.**

### 5.3 Fix applied

A default interpreter pin was added to `tox.ini`:

```ini
[testenv]
basepython = python3.13
```

This keeps tox test environments on Python 3.13, which is compatible with the currently resolved Ansible stack.

---

## 6. Retest after the interpreter fix

The same command was run again:

```zsh
cd /Users/charliemordant/Code/Sources/Platform/platform-2020/ansible/roles/tcharl.freeipa_server
tox -e test-exec-monorepo -- --scenario-name=parallels
```

### Result after the fix

The previous immediate failure disappeared.

Observed behavior after the fix:

- tox recreated `test-exec-monorepo` with `cpython3.13`
- Molecule started correctly
- the `parallels` scenario executed through:
  - `dependency`
  - `cleanup`
  - `destroy`
  - `syntax`
  - `create`
  - `prepare`
  - `converge`
- the run then continued into the actual FreeIPA installation and provisioning flow
- the terminal session timed out after 300 seconds while the scenario was still progressing

This means:

- the uv migration no longer causes the previous tox/Molecule interpreter crash
- the remaining runtime is a long-running scenario execution, not the original regression

---

## 7. Important observations from the retest

### 7.1 The main regression is fixed

The critical post-migration regression was:

- **wrong Python interpreter selected for tox envs**

That regression is fixed by:

```ini
[testenv]
basepython = python3.13
```

### 7.2 The remaining run is long, not obviously broken by uv

After the interpreter fix, the scenario got far enough to:

- create the Parallels VM
- connect with Ansible
- run prepare steps
- start role convergence
- start FreeIPA installation tasks

So at the time of writing, there is **no reproduced uv-specific failure left** for this scenario.

### 7.3 Warnings seen during the run

Warnings seen but not addressed in this migration:

- duplicate installed collection versions between local collections and tox-installed collections
- many Ansible warnings of the form:
  - `Module invocation had junk after the JSON data`
- target guest Python reported by gathered facts as `3.14.0`

Those warnings existed during execution, but none of them reproduced the original post-migration failure.

---

## 8. Current recommended commands

### Refresh lock and requirements

```zsh
cd /Users/charliemordant/Code/Sources/Platform/platform-2020/ansible/roles/tcharl.freeipa_server
uv lock
uv export --format requirements.txt --no-dev --no-hashes --output-file requirements.txt
uv export --format requirements.txt --all-groups --no-hashes --output-file requirements-dev.txt
```

### Build package

```zsh
cd /Users/charliemordant/Code/Sources/Platform/platform-2020/ansible/roles/tcharl.freeipa_server
tox -e package
```

### Regenerate dependency files and build package together

```zsh
cd /Users/charliemordant/Code/Sources/Platform/platform-2020/ansible/roles/tcharl.freeipa_server
tox -e pipdep,package
```

### Run the monorepo Parallels scenario

```zsh
cd /Users/charliemordant/Code/Sources/Platform/platform-2020/ansible/roles/tcharl.freeipa_server
tox -e test-exec-monorepo -- --scenario-name=parallels
```

---

## 9. Final status summary

### Migration status

Completed:

- Poetry metadata removed from the role workflow
- `uv` adopted for lock/export/build
- tox updated to bootstrap and execute with `uv`
- `requirements-uv.txt` introduced
- `uv.lock` added

### Regression status

Resolved:

- `tox -e test-exec-monorepo -- --scenario-name=parallels` no longer fails immediately with the Python 3.14 / ansible-core incompatibility once `basepython = python3.13` is set

### Remaining operational note

- the Parallels Molecule scenario is long-running and may need a larger terminal timeout or a dedicated run outside the default interactive timeout window to observe full completion

---

## 10. Minimal checklist for future migrations in similar roles

- [ ] convert Poetry metadata to `[project]` + `[dependency-groups]`
- [ ] replace `poetry-core` with a supported backend (`hatchling` was used here)
- [ ] swap `poetry lock` → `uv lock`
- [ ] swap `poetry export` → `uv export`
- [ ] swap `poetry build` → `uv build`
- [ ] replace Poetry bootstrap dependency with `uv`
- [ ] regenerate `requirements.txt`, `requirements-dev.txt`, and `uv.lock`
- [ ] run `tox -e pipdep,package`
- [ ] test at least one real Molecule scenario
- [ ] if tox is using uv-backed envs, explicitly pin `basepython` to a supported interpreter

---

## 11. Files involved in this migration

Primary files:

- `pyproject.toml`
- `tox.ini`
- `requirements-uv.txt`
- `requirements.txt`
- `requirements-dev.txt`
- `uv.lock`

Reference CI files checked during the migration:

- `.github/workflows/molecule.yml`
- `.github/workflows/release-galaxy.yml`
- `.travis.yml`

---

## 12. CI/CD update procedure

This section records the minimal CI/CD update that was applied after the local `uv` migration was validated.

### Goal

Keep the same job responsibilities:

- GitHub Actions:
  - requirements installation check
  - lint
  - Galaxy release/import
- Travis CI:
  - Molecule execution with the `kvm` scenario

Only replace the Python package bootstrap and command invocation style so that CI uses `uv` instead of direct `pip install ... tox ansible` style flows.

### Important constraint kept during the CI update

The CI update did **not** change who provides Python 3.13:

- GitHub Actions continues to provision Python with `actions/setup-python`
- Travis CI continues to provision Python with:

```yaml
python:
  - "3.13"
```

So in CI, `uv` is used to run Python tooling, but it is **not** responsible for installing Python 3.13 in the current workflow design.

### Procedure applied

#### 12.1 Update `.github/workflows/molecule.yml`

For the `requirements` and `lint` jobs:

1. Keep the existing jobs and their purpose unchanged.
2. Ensure Python 3.13 is explicitly configured through `actions/setup-python`.
3. Install `uv` with:

```zsh
python -m pip install --upgrade uv
```

4. Replace direct `ansible-galaxy` execution with:

```zsh
uv tool run --python 3.13 --from ansible-core ansible-galaxy ...
```

5. Replace direct `tox` execution with:

```zsh
uv tool run --python 3.13 --with tox tox -e lint
```

#### 12.2 Update `.github/workflows/release-galaxy.yml`

For the Galaxy release/import job:

1. Keep the single `galaxy` job and its release/import purpose unchanged.
2. Set Python explicitly to 3.13 with `actions/setup-python`.
3. Replace the old pip dependency install step with `uv` installation only:

```zsh
python -m pip install --upgrade uv
```

4. Replace direct `ansible-galaxy role import` execution with:

```zsh
uv tool run --python 3.13 --from ansible-core ansible-galaxy role import ...
```

5. Update the cache path from pip cache to uv cache:

- old cache path: `~/.cache/pip`
- new cache path: `~/.cache/uv`

#### 12.3 Update `.travis.yml`

For the Travis Molecule execution:

1. Keep `python: "3.13"` unchanged.
2. Keep the same apt packages and `vagrant-libvirt` installation.
3. Replace the old Python tooling bootstrap:

```zsh
pip install wheel pyopenssl tox ansible
```

with:

```zsh
pip install uv
```

4. Replace the direct `ansible-galaxy` calls with:

```zsh
uv tool run --python 3.13 --from ansible-core ansible-galaxy role install -r requirements-standalone.yml
uv tool run --python 3.13 --from ansible-core ansible-galaxy collection install -r requirements-collections.yml
```

5. Replace the direct Molecule tox execution with:

```zsh
uv tool run --python 3.13 --with tox tox -e test-exec -- --scenario-name=kvm
```

### Why `ansible-core` is used for `ansible-galaxy`

During validation, `uv` reported that `ansible-galaxy` is provided by `ansible-core`, not directly by the `ansible` meta-package executable set. For that reason, the CI commands were normalized to:

```zsh
uv tool run --python 3.13 --from ansible-core ansible-galaxy ...
```

### Validation commands used locally for the CI migration

The following commands were used to confirm that the CI-style invocations are valid locally:

```zsh
cd /Users/charliemordant/Code/Sources/Platform/platform-2020/ansible/roles/tcharl.freeipa_server
uv tool run --python 3.13 --with tox tox -e lint --notest
uv tool run --python 3.13 --from ansible-core ansible-galaxy --version
```

### Result of the CI/CD update

The CI procedure after this update is:

- keep CI job structure unchanged
- keep Python 3.13 provisioning unchanged
- install `uv`
- run `tox` and `ansible-galaxy` through `uv`

This preserves the original CI intent while aligning the CI execution model with the new `uv`-based local workflow.

