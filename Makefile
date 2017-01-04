test:
	. aws-credentials && ./runtests.py 

test-coverage:
	. aws-credentials && coverage run --source collectfast ./runtests.py

distribute:
	python setup.py sdist bdist_wheel upload
