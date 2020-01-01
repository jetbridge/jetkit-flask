.PHONY: dist

dist:
	python setup.py sdist

checks:
	pipenv run flake8
	pipenv run mypy .
	pipenv run bento check
	pipenv run pytest -x