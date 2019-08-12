test:
	. aws-credentials && ./runtests.py

test-coverage:
	. aws-credentials && coverage run --source collectfast ./runtests.py

distribute:
	pip install --upgrade wheel twine setuptools
	python setup.py sdist bdist_wheel
	twine upload dist/*
