SHELL := /bin/bash

# Install project dependencies
.PHONY: install
install: ## install the project
	python3 -m venv venv
	source venv/bin/activate && pip install -e .


# HELP

.PHONY: help
help:
	@ grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
