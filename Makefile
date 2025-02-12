.PHONY: install run test lint format

install:
	poetry install

run-local:
	docker-compose -f docker/docker-compose.yml up --build

run-prod:
	docker-compose -f docker/docker-compose.prod.yml up -d

test:
	poetry run pytest

lint:
	poetry run mypy src
	poetry run black --check src
	poetry run isort --check-only src

format:
	poetry run black src
	poetry run isort src