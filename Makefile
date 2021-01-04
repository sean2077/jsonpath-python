
PYCACHE_DIR := $(shell find . -name '__pycache__' -type d)
PYTEST_DIR := $(shell find . -name '.pytest_cache' -type d)

.PHONY: test install

install:
	pip install . --no-index

uninstall:
	pip uninstall jsonpath

test:
	pytest test -vv -s

clean:
	rm -rf $(PYCACHE_DIR) ${PYTEST_DIR} dist jsonpath.egg-info

package: clean
	python3 setup.py sdist bdist_wheel

upload: package
	twine upload dist/*
