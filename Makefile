.PHONY: check

check:
	python3 -m json.tool .agents/plugins/marketplace.json >/dev/null
	python3 -m json.tool plugins/thruwire/plugin.json >/dev/null
	python3 -m json.tool plugins/thruwire/mcp.json >/dev/null
	python3 -m unittest discover -s tests -v
	$(MAKE) -C plugins/foreman check
