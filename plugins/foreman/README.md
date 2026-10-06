# Foreman for Codex

<img src="assets/logo.svg" alt="Foreman" width="128">

[Foreman](https://github.com/thruwire/foreman) is an agent supervisor and software factory foreman powered by TypeSafe’s Jev model. This plugin connects Codex lifecycle hooks to Foreman, where responsibility routing, Jev decisions, evidence collection, supervision, completion checks, and session state are implemented independently from the Codex worker.

This project is maintained by [ThruWire](https://thruwire.ai). It is not made, endorsed, or maintained by OpenAI.

The plugin source is maintained in this directory and published through the
[ThruWire marketplace](https://github.com/thruwire/marketplace) as `foreman@thruwire`.

Follow the [complete setup guide](SETUP.md) for the ordered configuration steps, including
credentials, local responsibilities, verification, explicit hook trust, and a fresh session.
It includes generic local responsibility configuration for the upcoming Foreman 0.4.2 release.

## Architecture

```text
Codex lifecycle event (JSON)
  -> scripts/foreman-hook
  -> foreman hook --client codex
  -> Codex hook response (JSON)
```

The launcher does not parse or reconstruct protocol data. It checks that `foreman` exists, then uses `exec` so Foreman receives stdin, stdout, stderr, exit status, and signals directly. The plugin does not set `FOREMAN_DATA_DIR`; Foreman's normal `~/.foreman` configuration and session storage remain in use.

The plugin registers synchronous handlers for:

- `SessionStart`
- `UserPromptSubmit`
- `PreToolUse`
- `PostToolUse`
- `Stop`
- `SessionEnd`

## Requirements

- Codex with plugin and lifecycle-hook support
- macOS or Linux
- Python 3.11 or newer (required by Foreman)
- `foreman-core >= 0.4.1`
- A TypeSafe API key in `TYPESAFE_API_KEY`

Install Foreman separately with either supported tool:

```bash
pipx install 'foreman-core>=0.4.1'
```

or:

```bash
uv tool install 'foreman-core>=0.4.1'
```

Keep the API key out of repositories, shell history, logs, and hook output. One shell-safe way to provide it for a Codex process is:

```bash
read -rs 'TYPESAFE_API_KEY?TypeSafe API key: '
printf '\n'
export TYPESAFE_API_KEY
codex
```

If you use the Codex desktop app, make the variable available to the app process through your operating-system secret-management or process-launch environment, then restart the app. The plugin never reads or prints the value itself.

## Install

```bash
codex plugin marketplace add thruwire/marketplace
codex plugin add foreman@thruwire
```

The marketplace entry points at this directory as a local source within the marketplace checkout.
That lets Codex read the manifest and artwork before installation, then cache the complete package;
users do not need a local checkout of either repository.

Confirm the installation:

```bash
codex plugin list --json
```

Configure the runtime, credentials, and responsibilities before enabling its hooks. In the desktop
app, use Settings → Hooks; in the CLI, use `/hooks`. Review and trust all six Foreman definitions,
then start a fresh Codex session and submit a new prompt. Plugin installation does not automatically
trust executable hooks; Codex skips untrusted hooks. See [setup step 7](SETUP.md#7-review-and-trust-the-hooks-then-start-a-fresh-session).

## Verify setup

From this plugin directory, run:

```bash
./scripts/doctor
```

The doctor checks that Foreman is on `PATH`, its installed version is supported, `TYPESAFE_API_KEY` is present without displaying it, and Foreman can load its own configuration through `foreman extension status`.

Within Codex, the bundled `foreman` skill can explain the integration and guide setup diagnostics. It does not make supervisory decisions in place of Foreman.

## Configuration

Configure Foreman through its normal CLI and files. By default, its central configuration is:

```text
${FOREMAN_CONFIG:-${FOREMAN_DATA_DIR:-~/.foreman}/config.toml}
```

This plugin deliberately does not redirect configuration or session state into `PLUGIN_DATA`.

Foreman command evidence providers are configured centrally, not in the repository being supervised. For example:

```toml
[[evidence.commands]]
id = "pytest"
command = ["python", "-m", "pytest", "-q"]
timeout_seconds = 120
```

Only checks that explicitly select `command.pytest` cause that trusted command to run. See the [Foreman evidence documentation](https://github.com/thruwire/foreman/blob/main/docs/evidence.md) for the complete model.

## Hook behavior and compatibility

The plugin transparently preserves Foreman's response. Current Codex behavior includes:

- `SessionStart` and `UserPromptSubmit` accept `hookSpecificOutput.additionalContext` as model context.
- `PreToolUse` accepts `permissionDecision: "deny"` and `permissionDecisionReason`; Foreman 0.4.1 emits this current shape.
- `PostToolUse` accepts `decision: "block"` as feedback after the tool has already run.
- `Stop` uses `decision: "block"` plus `reason` to create an automatic continuation prompt.
- `SessionEnd` is advisory and cannot steer the session; it lets Foreman clean up attached-session state.

No `PostToolUse` translation to `continue: false` is necessary. Codex explicitly supports both mechanisms, and they have different code-mode behavior. Preserving Foreman's response avoids changing its intended semantics.

## Trust and security

Hooks execute local programs with the same operating-system identity and environment as Codex. Before trusting these hooks, review [`hooks/hooks.json`](hooks/hooks.json) and [`scripts/foreman-hook`](scripts/foreman-hook). Every registered event invokes the separately installed `foreman` executable found on `PATH`.

The launcher treats hook input as opaque bytes and never logs it. Foreman receives tool inputs and outputs because they are part of the Codex lifecycle protocol. Review Foreman's configuration, extensions, and command evidence providers as trusted local code. Avoid emitting secrets from tools or evidence commands because hook feedback can become model-visible.

## Update

```bash
codex plugin marketplace upgrade thruwire
codex plugin add foreman@thruwire
```

Upgrade Foreman independently:

```bash
pipx upgrade foreman-core
```

or:

```bash
uv tool upgrade foreman-core
```

Start a new session after updating. Changed hook definitions require a new trust review in `/hooks`.

## Uninstall

```bash
codex plugin remove foreman@thruwire
codex plugin marketplace remove thruwire
```

This does not uninstall Foreman or remove `~/.foreman`. Remove `foreman-core` and Foreman's data separately only if you no longer use them.

## Troubleshooting

**Hooks appear but do not run:** open `/hooks` and trust the current definitions. Also confirm hooks are enabled and the project is trusted.

**The plugin is enabled but `/hooks` shows zero installed Foreman hooks:** upgrade the marketplace,
reinstall Foreman 0.1.1 or newer, and start a new session. Codex CLI 0.159.2 on the tested host
skipped the bundled hooks when a portable root `plugin.json` was present. Foreman now uses
`.codex-plugin/plugin.json` as its only manifest, with an explicit reference to the existing
`hooks/hooks.json`. Do not add user or project hook copies; they would run independently of the
plugin hooks. If discovery still fails, report the Codex version and plugin cache path.

**`foreman was not found on PATH`:** run `command -v foreman` in the environment that launches Codex. GUI applications can inherit a different `PATH` than interactive shells.

**Missing API key:** ensure `TYPESAFE_API_KEY` is present in the Codex process environment, then restart Codex. The doctor reports presence only and never prints the value.

**Configuration failure:** run `foreman extension status`. Fix the reported issue in Foreman's normal configuration or installed extensions; the plugin does not maintain a second configuration layer.

**A tool was denied:** the reason comes from Foreman's assessment. The launcher does not invent or rewrite denials.

**Completion continued once:** Foreman can reject an incomplete `Stop`. Codex converts the returned reason into one continuation prompt. Foreman uses `stop_hook_active` to avoid an infinite continuation loop.

**`PreToolUse` or `Stop arrived before work_submitted`:** hooks may have been enabled during an
existing turn, before Foreman received its initial prompt. Temporarily disable the Foreman hooks,
verify configuration, then start a fresh session before re-enabling them. See the ordered setup
guide; do not add separate hook copies or patch the installed runtime.

## Development

Run all dependency-free checks:

```bash
make check
```

The tests cover byte-for-byte stdin and stdout forwarding, stderr separation, exit status, missing dependencies, odd paths and working directories, doctor behavior, hook registration, Codex manifest structure, and all six fixture events.

Check the package through the real Codex plugin reader with `make discovery`. This verifies that
all six hooks come from the existing plugin configuration and makes no persistent configuration
changes or model calls. Set `CODEX_BIN` to test a particular Codex executable.

`tests/integration/fake_foreman.py` is a deterministic protocol double for exercising the installed plugin in a real Codex session when TypeSafe credentials are unavailable. It is test-only; production hooks always resolve the separately installed `foreman` executable from `PATH`.

Run live allow, deny, post-tool, continuation, and cleanup scenarios against Codex with:

```bash
make integration
```

The live test uses `tests/integration/hooks.json`, a project-scoped mirror of the plugin registration, to isolate Codex hook input/output behavior from plugin marketplace discovery. It invokes the same production launcher. The command uses Codex model capacity and passes `--dangerously-bypass-hook-trust` only inside its temporary, pre-vetted test repository.

Measure the three latency-sensitive paths against the installed Foreman:

```bash
./scripts/benchmark --iterations 5
```

The utility reports end-to-end `PreToolUse`, `PostToolUse`, and `Stop` latency. These paths can call Jev, and `Stop` can also run configured command evidence, so results depend on credentials, network conditions, configuration, and repository state.

### Advanced example: selective pytest supervision

[`examples/selective-pytest/`](examples/selective-pytest/) contains a runnable Foreman extension
showing conditional responsibility routing and external command evidence. A documentation-only
prompt does not activate its Python-test responsibility and does not run `pytest`. A Python-change
prompt activates the responsibility; on `Stop`, Foreman runs centrally configured `pytest -q` once
and evaluates two responsibility-owned checks from that result.

The example keeps this Codex plugin thin: routing, checks, command selection, evidence collection,
and completion policy all remain in Foreman. See the example README for installation, an isolated
real-Jev demo, expected output, and the command-provider trust boundary.

## Distribution

This directory is the installable plugin package:

- `.codex-plugin/plugin.json` is the Codex-native manifest and explicitly points to the bundled
  `hooks/hooks.json` configuration.
- A root portable `plugin.json` is intentionally absent to avoid suppressing hook discovery in
  affected Codex versions. This package targets Codex; the ThruWire MCP package keeps its portable
  manifest.
- The operational skill lives at `skills/foreman/SKILL.md`.
- Artwork lives in `assets/` and is referenced by the Codex manifest.

This repository owns both the installable package and its discovery metadata. The Codex catalog
exposes this directory as `foreman@thruwire`. Future assistant plugins should use their own package
directories and catalog entries.

Public directory submission is performed through the OpenAI plugin submission portal. Before submission, ThruWire must provide the final listing assets and public support, privacy-policy, and terms-of-service URLs; verify its publisher identity; prepare starter prompts; and provide the required positive and negative review test cases. Local executable hooks also require a supported execution environment and explicit user trust.
