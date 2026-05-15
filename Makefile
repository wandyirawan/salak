.PHONY: dev infra up stop restart db-reset db-nuke db-setup migrate clean

INFRA_DIR = ../infra

# Start everything
dev:
	@echo "🍈 Starting Salak..."
	$(MAKE) infra
	$(MAKE) migrate
	@echo "🚀 Starting Granian on :8000..."
	uv run granian --interface asgi --host 0.0.0.0 --port 8000 app.main:app

# Start infra dependencies (central Postgres + Minio)
infra:
	@cd $(INFRA_DIR) && docker compose up -d 2>/dev/null; \
	sleep 2; \
	echo "✅ Infra ready (pgsql:5433, minio:9000)"

# Run migrations
migrate:
	uv run python migrate.py

# Alias
up:
	$(MAKE) dev

# Stop all containers
stop:
	@cd $(INFRA_DIR) && docker compose stop 2>/dev/null || true
	@echo "Stopped."

# Restart infra (NO data loss)
db-reset:
	@cd $(INFRA_DIR) && docker compose restart postgres 2>/dev/null && echo "✅ Postgres restarted" || echo "⚠️  Infra not running? Run: make infra"

# DANGER: Delete everything including data volume
db-nuke:
	@echo "⚠️  WARNING: This will DELETE ALL DATA in Postgres volume!"
	@read -p "Type 'YES' to continue: " confirm && [ "$$confirm" = "YES" ]
	@cd $(INFRA_DIR) && docker compose down -v
	@cd $(INFRA_DIR) && docker compose up -d
	@sleep 2
	$(MAKE) migrate
	@echo "✅ Done. Fresh DB with migrations applied."

# Run migration manually
db-setup:
	$(MAKE) migrate

# Clean local build artifacts
clean:
	rm -rf .venv
	rm -rf __pycache__ *.pyc
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "Cleaned."
