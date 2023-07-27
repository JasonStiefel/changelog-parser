VENV_LOCATION ?= venv

$(VENV_LOCATION):
	$(if $(filter 0,$(shell python3 --version >/dev/null 2>&1; echo $$?)),$\
		python3 -m venv --clea $@,$\
		$(if $(filter 0,$(shell python --version >/dev/null 2>&1; echo $$?)),$\
			python -m venv --clear $@,$\
			$(error Unable to determine a way to invoke python to create a venv)))

.PHONY: install
$(VENV_LOCATION)/bin/pytest: $(VENV_LOCATION)
	$</bin/python -m pip install -e .[test]
install-test: $(VENV_LOCATION)/bin/test-changelog;

.PHONY: test
test: $(VENV_LOCATION)/bin/pytest
	$<
