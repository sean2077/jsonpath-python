# project metadata
NAME := `python setup.py --name`
FULLNAME := `python setup.py --fullname`
VERSION := `python setup.py --version`
BUILD := `git rev-parse --short HEAD`

.PHONY: info help clean dist docs
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

info: ## project info
	@echo $(FULLNAME) at $(BUILD)

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-build clean-pyc ## remove all build, test, coverage and Python artifacts

clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

lint: ## check style with black
	find $(NAME) -name '*.py' -type f -not -path "*/pb/*" -not -path "*/data/*" -exec black {} +

docs: ## format docs
	doctoc --gitlab README.md

install: ## install the package to the active Python's site-packages
	pip install . -U --no-index

uninstall: ## uninstall the package
	pip uninstall $(NAME)

dist: clean ## package
	python3 setup.py sdist bdist_wheel

upload: dist # upload the package to pypi
	twine upload dist/*
