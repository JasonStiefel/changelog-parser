VENV_LOCATION ?= venv

.PHONY: help
help: ## Displays helptext for useful targets in this makefile
	@grep -E '^[\*\/\%a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
	sort | \
	awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-8s\033[0m %s\n", $$1, $$2}'

$(VENV_LOCATION):
	$(if $(filter 0,$(shell python3 --version >/dev/null 2>&1; echo $$?)),$\
		python3 -m venv --clear $@,$\
		$(if $(filter 0,$(shell python --version >/dev/null 2>&1; echo $$?)),$\
			python -m venv --clear $@,$\
			$(error Unable to determine a way to invoke python to create a venv)))

$(foreach exec,pytest coverage pylint,$(VENV_LOCATION)/bin/$(exec)): $(VENV_LOCATION)
	$</bin/python -m pip install -e .[test]

.PHONY: test
test: $(VENV_LOCATION)/bin/pytest ## run unit tests
	$<

cover: $(VENV_LOCATION)/bin/coverage ## run unit tests and generate a coverage report
	$< run -m pytest
	$< html --directory $@

.PHONY: lint
lint: $(VENV_LOCATION)/bin/pylint
	$< src