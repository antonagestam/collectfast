test:
	. aws-credentials && ./runtests.py 

distribute:
	python setup.py sdist bdist_wheel upload
