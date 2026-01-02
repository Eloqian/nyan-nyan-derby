.PHONY: dev db-migrate test clean deploy deploy-down

dev:
	docker-compose up --build
	docker image prune -f

db-migrate:
	docker-compose exec backend alembic upgrade head

test:
	docker-compose exec backend pytest

clean:
	docker-compose down -v

deploy:
	docker-compose -f docker-compose.prod.yml up --build -d
	docker image prune -f

deploy-down:
	docker-compose -f docker-compose.prod.yml down

update:
	docker-compose -f docker-compose.prod.yml up --build -d backend frontend
	docker image prune -f

logs:
	docker-compose -f docker-compose.prod.yml logs -f
