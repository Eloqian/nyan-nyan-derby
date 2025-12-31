.PHONY: dev db-migrate test clean deploy deploy-down

dev:
	docker-compose up --build

db-migrate:
	docker-compose exec backend alembic upgrade head

test:
	docker-compose exec backend pytest

clean:
	docker-compose down -v

deploy:
	docker-compose -f docker-compose.prod.yml up --build -d

deploy-down:
	docker-compose -f docker-compose.prod.yml down
