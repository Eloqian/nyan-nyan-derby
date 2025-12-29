.PHONY: dev db-migrate test clean

dev:
	docker-compose up --build

db-migrate:
	docker-compose exec backend alembic upgrade head

test:
	docker-compose exec backend pytest

clean:
	docker-compose down -v
