
coverage:
	nosetests -v --cover-html --cover-html-dir=./coverage --with-coverage --cover-package=avocado

tests:
	INTEGRATION=1 nosetests -v

test: tests

fast:
	nosetests -v

