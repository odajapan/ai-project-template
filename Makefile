.PHONY: clean data lint requirements requirements-all sync_data_to_s3 sync_data_from_s3 test coverage format check typecheck precommit activate hooks create_environment venv which_src

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
BUCKET = [OPTIONAL] your-bucket-for-syncing-data (do not include 's3://')
PROFILE = default
PROJECT_NAME = your_project_name
# A checkout's own .venv is used without activating it, but only once `make venv`
# has finished (it writes the marker below), so a bare or stale .venv (e.g. from
# a hand-run `python -m venv .venv`) is ignored. Otherwise whatever "python" is on
# PATH (a conda env, an activated venv). Chosen when make starts, so run
# `make venv` as its own invocation, not `make venv check`. Tools run as
# `$(PYTHON_INTERPRETER) -m <tool>` because macOS's make 3.81 looks single-command
# recipes up on its startup PATH, so putting .venv/bin on PATH here would not work.
# Override at invocation time, e.g. `make PYTHON_INTERPRETER=python3.11 requirements`.
# realpath is empty when .venv/bin/python is a dangling symlink (the Python it was
# built from was removed), so such a .venv falls back like a missing one.
VENV_MARKER = $(PROJECT_DIR)/.venv/.make-venv-ok
ifneq (,$(and $(wildcard $(VENV_MARKER)),$(realpath $(PROJECT_DIR)/.venv/bin/python)))
PYTHON_INTERPRETER = $(PROJECT_DIR)/.venv/bin/python
else
PYTHON_INTERPRETER = python
endif

# A shared env's editable install (e.g. a conda env) points at one checkout, so
# a clone or worktree without its own .venv would run that checkout's src from
# every target below (scripts/*.py, the CLI). Put this checkout's src first.
# The checkout path must not contain ':' (it would split the PYTHONPATH entry).
export PYTHONPATH := $(PROJECT_DIR)/src$(if $(PYTHONPATH),:$(PYTHONPATH))

# Interpreter that creates .venv: the newest pyenv 3.12.x (highest patch number,
# so 3.12.11 beats 3.12.9), else python3.12 on PATH. Recursively expanded, so the
# shell runs only when a target uses it. Override: `make VENV_PYTHON=/path/to/python3.12 venv`.
VENV_PYTHON ?= $(or $(shell ls -d $(HOME)/.pyenv/versions/3.12.*/bin/python 2>/dev/null | awk -F/ '{ split($$(NF-2), v, "."); print v[3], $$0 }' | sort -n | tail -n 1 | cut -d' ' -f2-),python3.12)
# Canonical extras for this project. Every doc and CI job installs exactly
# this set; override at invocation time, e.g. `make EXTRAS=dev requirements`.
EXTRAS ?= dev,claude,jira

ifeq (,$(shell which conda))
HAS_CONDA=False
else
HAS_CONDA=True
endif

#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Install Python Dependencies (development environment)
requirements:
	$(PYTHON_INTERPRETER) -c 'import sys; sys.version_info >= (3, 12) or sys.exit(f"Python 3.12+ required, found {sys.version}")'
	$(PYTHON_INTERPRETER) -m pip install -U pip
	$(PYTHON_INTERPRETER) -m pip install -e ".[$(EXTRAS)]"

## Install with the heavier data-science extras as well
requirements-all:
	$(MAKE) EXTRAS=dev,claude,jira,notebook,viz,docs,cloud requirements

# A plain `python -m venv` keeps a dead bin/python symlink (its Python was
# removed), so an unusable .venv is rebuilt with --clear instead.
## Create this checkout's own .venv and editable-install the canonical extras (idempotent; no conda needed)
venv:
	@$(PROJECT_DIR)/.venv/bin/python -c '' 2>/dev/null || command -v $(VENV_PYTHON) >/dev/null || { echo "make venv: '$(VENV_PYTHON)' not found; set VENV_PYTHON=/path/to/python3.12" >&2; exit 1; }
	@$(PROJECT_DIR)/.venv/bin/python -c '' 2>/dev/null || $(VENV_PYTHON) -m venv --clear $(PROJECT_DIR)/.venv
	$(PROJECT_DIR)/.venv/bin/python -m pip install -e '$(PROJECT_DIR)[$(EXTRAS)]'
	@touch $(VENV_MARKER)

## Print the interpreter and PYTHONPATH make uses and the your_project_name it resolves to (should be this checkout's src/)
which_src:
	@echo "interpreter=$(PYTHON_INTERPRETER)"
	@$(PYTHON_INTERPRETER) -c "import os, your_project_name as m; print('PYTHONPATH=' + os.environ.get('PYTHONPATH', '')); print('module=' + m.__file__)"

## Make Dataset
data:
	$(PYTHON_INTERPRETER) src/your_project_name/data/make_dataset.py data/raw data/processed

## Delete all compiled Python files and build metadata
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -not -path "./.claude/*" -exec rm -r {} +

## Lint using ruff (style rules + formatting drift)
lint:
	$(PYTHON_INTERPRETER) -m ruff check src tests scripts
	$(PYTHON_INTERPRETER) -m ruff format --check src tests scripts

## Format code with ruff
format:
	$(PYTHON_INTERPRETER) -m ruff check --fix src tests scripts
	$(PYTHON_INTERPRETER) -m ruff format src tests scripts

## Run static type checks with mypy
typecheck:
	$(PYTHON_INTERPRETER) -m mypy src scripts

## Upload Data to S3
sync_data_to_s3:
ifeq (default,$(PROFILE))
	aws s3 sync data/ s3://$(BUCKET)/data/
else
	aws s3 sync data/ s3://$(BUCKET)/data/ --profile $(PROFILE)
endif

## Download Data from S3
sync_data_from_s3:
ifeq (default,$(PROFILE))
	aws s3 sync s3://$(BUCKET)/data/ data/
else
	aws s3 sync s3://$(BUCKET)/data/ data/ --profile $(PROFILE)
endif

## Set up a shared conda env from environment.yml (per-checkout environments: `make venv`)
create_environment:
ifeq (True,$(HAS_CONDA))
		@echo ">>> Detected conda, creating/updating environment from environment.yml."
		conda env create -f environment.yml || conda env update -f environment.yml
		@echo ">>> Activate with:\nconda activate $(PROJECT_NAME)"
else
	@echo ">>> No conda; creating this checkout's .venv with make venv instead."
	$(MAKE) venv
endif

## Show the command to activate the conda environment for this project
activate:
	@echo "conda activate $(PROJECT_NAME)"

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Run tests
test:
	$(PYTHON_INTERPRETER) -m pytest

## Run tests with a coverage report
coverage:
	$(PYTHON_INTERPRETER) -m pytest --cov=src --cov-report=term-missing

## Run linting, type checks, and tests
check: lint typecheck test

# The ruff and mypy hooks are `language: system`, so pre-commit finds them on
# PATH, not through the interpreter that starts it; when make uses a .venv (an
# interpreter given by path), its bin/ goes first. A shell assignment inside
# the command is fine under make 3.81; only a bare leading command is not.
## Run pre-commit on all files
precommit:
	PATH="$(if $(findstring /,$(PYTHON_INTERPRETER)),$(dir $(PYTHON_INTERPRETER)):)$$PATH" $(PYTHON_INTERPRETER) -m pre_commit run --all-files

## Install repo-local Git hooks (branch guards in .githooks/)
# The hook files are committed with the executable bit set, so no chmod is
# needed — which also keeps this target working when the sandbox denies
# writes under .githooks/.
hooks:
	git config core.hooksPath .githooks
	@echo ">>> Git hooks installed (.githooks/ via core.hooksPath)."
#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
