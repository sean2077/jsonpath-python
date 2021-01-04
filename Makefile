.PHONY: test install

install:
	pip install . --no-index

uninstall:
	pip uninstall jsonpath

test:
	pytest test -vv -s


PYCACHE_DIR := $(shell find . -name '__pycache__' -type d)
PYTEST_DIR := $(shell find . -name '.pytest_cache' -type d)
EGG_DIR := $(shell find . -name '*.egg-info' -type d)

clean:
	rm -rf $(PYCACHE_DIR) ${PYTEST_DIR} ${EGG_DIR} dist

package: clean
	python3 setup.py sdist bdist_wheel

upload: package
	twine upload dist/*
