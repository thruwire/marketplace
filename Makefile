.PHONY: check deepagents-integration

check:
	python3 -m json.tool .agents/plugins/marketplace.json >/dev/null
	python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
	python3 -m json.tool plugins/foreman-deepagents/.claude-plugin/plugin.json >/dev/null
	python3 -m json.tool plugins/foreman-deepagents/hooks/hooks.json >/dev/null
	python3 -m json.tool plugins/thruwire/plugin.json >/dev/null
	python3 -m json.tool plugins/thruwire/mcp.json >/dev/null
	python3 -m unittest discover -s tests -v
	$(MAKE) -C plugins/foreman check
	sh -n plugins/foreman-deepagents/scripts/foreman-hook

# Run with a Python environment containing deepagents-code >= 0.1.83.
deepagents-integration:
	python3 tests/integration/check_deepagents.py
