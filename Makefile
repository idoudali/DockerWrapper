SHELL := /bin/bash

# Compile requirements
# The below target assumes that pip-tools package has been installed
# by the user on the host.
.PHONY: compile-requirements
compile-requirements: ## compile requirements from .in files to .txt files
	pip-compile --output-file=requirements.txt requirements.in
	pip-compile --output-file=requirements.dev.txt requirements.dev.in


# Create virtual environment and install requirements
venv/bin/activate: requirements.txt requirements.dev.txt ## create virtual environment and install requirements
	python3 -m venv venv
	source venv/bin/activate && pip install -r requirements.txt
	source venv/bin/activate && pip install -r requirements.dev.txt

.PHONY: venv
venv: venv/bin/activate ## create virtual environment and install requirements

# Install project dependencies
.PHONY: install
install: venv ## install the project
	source venv/bin/activate && pip install -e .

# Build documentation
.PHONY: docs
docs: venv ## build the documentation using mkdocs
	source venv/bin/activate && mkdocs build

# HELP

.PHONY: help
help:
	@ grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
