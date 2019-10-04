
buildegg:
	-find . -name "*.pyc" -delete
	-find . -name __pycache__ -exec rm -rf {} \;
	python setup.py bdist_egg
