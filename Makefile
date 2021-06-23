SHELL := /usr/bin/env bash

test:
ifdef mark
	. storage-credentials && pytest -m "$(mark)"
else
	. storage-credentials && pytest
endif

test-skip-live:
	SKIP_LIVE_TESTS=true pytest

test-coverage:
	. storage-credentials && coverage run --source collectfast -m pytest

clean:
	rm -rf Collectfast.egg-info __pycache__ build dist

build: clean
	python3 -m pip install --upgrade wheel twine setuptools
	python3 setup.py sdist bdist_wheel

distribute: build
	python3 -m twine upload dist/*

test-distribute: build
	python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*

lint:
	flake8
	sorti --check .
	black --check .
	mypy .

format:
	sorti .
	black .
