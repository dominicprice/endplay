export PYTHONPATH := ${PYTHONPATH}:${PWD}/src

.PHONY: format
format:
	poetry run isort --tc --profile black .
	poetry run black .

.PHONY: test
test:
	poetry run pytest tests

.PHONY: lint
lint:
	poetry run mypy --check-untyped-defs src/endplay
	poetry run mypy --check-untyped-defs tests
