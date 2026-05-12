.PHONY: dev stop restart db-reset db-nuke db-setup

# Start full dev environment
dev:
	@echo "Starting Salak..."
	docker-compose up -d db
	@sleep 3
	@echo "Starting Salak with Granian..."
	uv run granian --interface asgi --host 0.0.0.0 --port 8000 app.main:app

# Stop containers (KEEP DATA)
stop:
	docker-compose stop

# Restart DB (NO data loss)
db-reset:
	docker-compose stop db
	docker-compose up -d db

# DANGER: Delete everything including data volume
db-nuke:
	@echo "WARNING: This will DELETE ALL DATA in Postgres volume!"
	@read -p "Type 'YES' to continue: " confirm && [ "$$confirm" = "YES" ]
	docker-compose down -v
	docker-compose up -d db

# Run migrations manually
db-setup:
	uv run python migrate.py
