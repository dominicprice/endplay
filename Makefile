export PYTHONPATH := ${PYTHONPATH}:${PWD}/src

.PHONY: format
format:
	pipenv run isort --tc --profile black .
	pipenv run black .

.PHONY: test
test:
	pipenv run pytest tests

.PHONY: lint
lint:
	pipenv run mypy --check-untyped-defs src/endplay
	pipenv run mypy --check-untyped-defs tests
