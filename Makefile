SHELL := /usr/bin/env bash

test:
	. storage-credentials && pytest

test-coverage:
	. storage-credentials && coverage run --source collectfast -m pytest

distribute:
	pip install --upgrade wheel twine setuptools
	python setup.py sdist bdist_wheel
	twine upload dist/*

lint:
	flake8
	sorti --check .
	black --check .
	mypy .
