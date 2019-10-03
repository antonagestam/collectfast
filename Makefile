SHELL := /usr/bin/env bash

test:
	. storage-credentials && ./runtests.py

test-coverage:
	. storage-credentials && coverage run --source collectfast ./runtests.py

distribute:
	pip install --upgrade wheel twine setuptools
	python setup.py sdist bdist_wheel
	twine upload dist/*

lint:
	flake8
	sorti --check .
	black --check .
	mypy .
