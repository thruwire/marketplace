.PHONY: check test lint benchmark integration discovery

check: lint test

test:
	python3 -m unittest discover -s tests -v

lint:
	python3 -m py_compile scripts/benchmark tests/test_plugin.py tests/integration/fake_foreman.py tests/integration/run_live.py tests/integration/check_discovery.py examples/selective-pytest/run_demo.py examples/selective-pytest/src/foreman_selective_pytest/__init__.py examples/selective-pytest/sample_project/calculator.py examples/selective-pytest/sample_project/test_calculator.py
	sh -n scripts/foreman-hook scripts/doctor
	python3 -m json.tool .codex-plugin/plugin.json >/dev/null
	python3 -m json.tool hooks/hooks.json >/dev/null
	python3 -m json.tool tests/integration/hooks.json >/dev/null

benchmark:
	./scripts/benchmark

integration:
	./tests/integration/run_live.py

discovery:
	python3 tests/integration/check_discovery.py
