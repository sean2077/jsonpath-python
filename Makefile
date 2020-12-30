
PYCACHE_DIR := $(shell find . -name '__pycache__' -type d)
PYTEST_DIR := $(shell find . -name '.pytest_cache' -type d)

.PHONY: test install

install:
	pip install . --no-index

uninstall:
	pip uninstall jsonpath

test:
	pytest tests -vv -s

clean:
	rm -rf $(PYCACHE_DIR) ${PYTEST_DIR}
