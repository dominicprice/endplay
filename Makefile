export PYTHONPATH := ${PYTHONPATH}:${PWD}/src

.PHONY: format
format:
	pipenv run isort .
	pipenv run yapf -ir .

.PHONY: test
test:
	pipenv run pytest tests
