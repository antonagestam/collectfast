test:
	./runtests.py

test-coverage:
	coverage run --source collectfast ./runtests.py

distribute:
	python setup.py sdist bdist_wheel upload
