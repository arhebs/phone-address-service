.PHONY: up down test lint

up:
	docker compose up --build -d

down:
	docker compose down

test:
	docker compose run --rm api pytest -q

lint:
	ruff check .
