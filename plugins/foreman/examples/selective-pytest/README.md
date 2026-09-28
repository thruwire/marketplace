# Selectively routed pytest responsibility

This example demonstrates a richer Foreman use case while keeping the Codex integration a protocol-only
bridge. The plugin still forwards lifecycle JSON unchanged. An optional Foreman extension owns the
policy:

```text
Codex prompt
  -> Foreman/Jev routing
     -> documentation-only work: do not activate selective-pytest.python-tests
     -> Python work: activate selective-pytest.python-tests
        -> assess pytest_completed and pytest_passed
        -> on Stop, run command.pytest once
        -> allow completion or request more work from the evidence
```

Foreman's global responsibilities remain active in both branches. The point is that the specialized
Python responsibility—and its external command—are selected only when the prompt calls for Python
behavior or testing. Foreman assesses the two checks together because they select the same evidence,
and deduplicates the provider so `pytest` runs once.

## Components

- `src/foreman_selective_pytest/__init__.py` registers a conditional responsibility through the
  `foreman.extensions` entry-point contract.
- `foreman-config.toml` enables the extension and declares the trusted external command as the argv
  array `["pytest", "-q"]`. Foreman does not invoke a shell.
- `sample_project/` is a tiny passing Python project used by the demo.
- `run_demo.py` runs a negative routing case and a positive routing case through the production
  `scripts/foreman-hook` launcher, then inspects Foreman's temporary attached-session state.

The command provider is completion evidence. Foreman does not run it for every lifecycle event. It
runs on `Stop` only when a routed responsibility's checks select `command.pytest`.

## Install the example

Install it into the same Python environment as `foreman`. For a development virtual environment:

```bash
../foreman/.venv/bin/python -m pip install --no-deps -e ./examples/selective-pytest
export PATH="$PWD/../foreman/.venv/bin:$PATH"
```

For a pipx-managed Foreman installation:

```bash
pipx inject foreman-core ./examples/selective-pytest
```

For normal use, merge these entries into `~/.foreman/config.toml`; do not replace unrelated
Foreman configuration:

```toml
[extensions."selective-pytest"]

[[evidence.commands]]
id = "pytest"
command = ["pytest", "-q"]
timeout_seconds = 120
```

Review this configuration before enabling it. Command evidence is trusted local code and executes
with Foreman's operating-system permissions in the supervised repository. The command is centrally
configured so a target repository cannot silently choose a different executable, but repository
test configuration and test code still influence what `pytest` executes.

Confirm discovery:

```bash
foreman extension status selective-pytest
```

## Run the isolated demo

The demo requires `TYPESAFE_API_KEY`, `foreman`, and `pytest` in its existing environment. It never
reads or copies a dotenv file. It creates both the Foreman data directory and sample target in a
temporary directory, then removes them.

```bash
python3 examples/selective-pytest/run_demo.py
```

Expected summary:

```text
docs-only: routed=no, command.pytest runs=0
python-change: routed=yes, command.pytest runs=1, status=completed, exit=0
selective pytest demo passed
```

Routing and check scores come from Jev, so ambiguous prompts should not be used as deterministic
tests. The demo deliberately uses an explicit negative prompt and an explicit positive prompt.
