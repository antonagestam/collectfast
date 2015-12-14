test:
	python runtests.py

distribute:
	python setup.py sdist bdist_wheel upload
