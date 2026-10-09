# Foreman for Deep Agents Code

`foreman-deepagents` adds Foreman supervision to LangChain's Deep Agents Code
(`dcode`) through its native plugin hooks. The plugin invokes the separately
installed Foreman core runtime; it bundles no model SDK or credentials.

## Install and configure

Install `foreman-core >= 0.5.0` (Python 3.11+) and `deepagents-code >= 0.1.83`
(Python 3.12+) separately:

```bash
uv tool install 'foreman-core>=0.5.0'
uv tool install --python 3.12 'deepagents-code>=0.1.83'
foreman --version
dcode --version
```

Ensure `foreman` is on the PATH used to launch dcode. Configure the model provider
for dcode separately, following its [provider documentation](https://docs.langchain.com/oss/deepagents/code/overview).

Store `TYPESAFE_API_KEY` in Foreman's protected central file at
`${FOREMAN_DATA_DIR:-~/.foreman}/.env`. Native hook environments may remove API
key variables, so use the central file instead of relying on an exported key:

```bash
mkdir -p ~/.foreman
chmod 700 ~/.foreman
touch ~/.foreman/.env
chmod 600 ~/.foreman/.env
```

Edit the file to add `TYPESAFE_API_KEY=your-key`. Never commit it. The standard
Foreman configuration is `${FOREMAN_CONFIG:-${FOREMAN_DATA_DIR:-~/.foreman}/config.toml}`.
To limit supervision to selected repositories, merge this into that file:

```toml
[hooks]
repositories = ["/absolute/path/to/project"]
```

Omit `repositories` for global supervision or use `[]` to disable it. Packaged
responsibilities are enabled by default; central responsibility overrides and
extensions also apply. Validate your configuration with `foreman extension status`.

Review the plugin's [hooks](hooks/hooks.json) and [launcher](scripts/foreman-hook),
then add and install it:

```bash
dcode plugin marketplace add thruwire/marketplace
dcode plugin install foreman-deepagents@thruwire
dcode plugin list --json
```

Start a fresh dcode session in your repository and submit the task. Installing and
enabling a plugin authorizes its hooks; project workspace trust does not govern
plugin hooks. `/reload` also refreshes plugin discovery in an existing session,
but a fresh session ensures Foreman sees startup and the original prompt.

If the marketplace was already registered, re-run
`dcode plugin marketplace add thruwire/marketplace` to refresh its catalog before
installing. This also works with the minimum supported CLI version, 0.1.83.

## Choose one hook installation

This plugin is an alternative to `foreman deepagents setup`. Do not register
both for the same session: all matching native handlers execute, causing duplicate
Foreman assessments. If setup was used previously, remove only Foreman's handlers
invoking `hook --client deepagents` from `~/.deepagents/hooks.json` and any project
`.deepagents/hooks.json`, preserving other handlers and settings. Back up those
files first; no automatic removal happens during plugin installation.

The separately owned `foreman run` worker remains available without this plugin.
An enabled plugin also loads in headless dcode sessions; disable it for a
Foreman-owned worker profile to avoid duplicate supervision.

## Behavior, verification, and removal

The plugin forwards `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`,
`PostToolUseFailure`, `Stop`, and `SessionEnd` synchronously with 120-second
handler deadlines. Its launcher preserves stdin, stdout, stderr, and exit status
and selects the `deepagents` adapter explicitly. Tool denial and completion
continuation use the native response contract; post-tool stop requests become
model feedback. Native timeouts and most nonzero errors are diagnostics, not a
guarantee of blocking.

During a task, Foreman session records under `${FOREMAN_DATA_DIR:-~/.foreman}/sessions/`
should identify `client: "deepagents"`. Session-end removes them. Excluded
repositories or disabled responsibilities create no session state. Missing
credentials or a missing Foreman executable produce hook diagnostics.

```bash
dcode plugin disable foreman-deepagents@thruwire
# Or remove it:
dcode plugin uninstall foreman-deepagents@thruwire
```

Start a fresh session after changing plugin state. Disabling or uninstalling does
not remove handlers installed separately by setup. This is a dcode plugin; the
Codex Foreman plugin uses a different package and adapter.

See the [core integration guide](https://github.com/thruwire/foreman/blob/main/integrations/deepagents/README.md)
for worker configuration, responsibilities, native limitations, and troubleshooting.
