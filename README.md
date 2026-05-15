# Salak - Product Service

Snake fruit product & inventory service (Python/FastAPI + Granian) for Pomegranate ecosystem.
Single source of truth for products, pricing, categories, and stock.

## Overview

Salak is the central Product Service using:
- **FastAPI** (Python web framework)
- **Granian** (Rust-powered ASGI server)
- **PostgreSQL** (with database triggers for stock consistency)
- **Mangosteen** (Authentication via JWKS)

## Architecture

```
Kelapa (Ecommerce) / Pome (Backoffice)
    ↓ (JWT Token via Mangosteen)
Salak (Product Service)
    ↓ (INSERT to inventory_transactions)
PostgreSQL Trigger → Auto-update inventory (real_qty)
```

### Key Concept: Trigger-Based Stock Updates

- **History (Delta):** `inventory_transactions` table stores stock changes (+5, -3)
- **State (Real):** `inventory` table stores current stock (`real_qty`)
- **Trigger:** Database trigger automatically updates `real_qty` when new transaction is inserted

This ensures **ACID compliance** — stock updates are atomic and consistent.

## Prerequisites

- Python >= 3.12
- [uv](https://github.com/astral-sh/uv) (Python package manager)
- Docker & Docker Compose
- Make

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/wandyirawan/salak.git
cd salak
uv sync
```

### 2. Start

```bash
make dev
```

This command:
- Starts central infra (PostgreSQL :5433 + Minio :9000)
- Runs migrations automatically
- Starts Salak with Granian (port 8000)

### 3. Verify

```bash
curl http://localhost:8000/health
# {"status": "ok", "service": "salak"}
```

## Environment Variables

Create `.env` file:

```env
DATABASE_URL=postgresql://salak:salaksecret@localhost:5433/salak
MANGOSTEEN_URL=http://localhost:4000
MANGOSTEEN_JWKS_URL=http://localhost:4000/api/.well-known/jwks.json
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=pomegranate
MINIO_SECRET_KEY=pomegranate123
```

## API Endpoints

All endpoints require JWT from Mangosteen except `/health`.

### Protected (Requires JWT)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/db-check` | Database connection check |
| GET | `/warehouses` | List warehouses |
| POST | `/warehouses` | Create warehouse |
| GET | `/products` | List products (?category=X&search=Y) |
| POST | `/products` | Create product |
| GET | `/products/{id}` | Get product by ID |
| PUT | `/products/{id}` | Update product |
| GET | `/products/template` | Download Excel template for bulk upload |
| POST | `/products/bulk-upload` | Upload Excel → Minio → parse → bulk insert |
| POST | `/stock-in` | Add stock (delta positive) |
| POST | `/stock-out` | Remove stock (delta negative, checks real_qty) |
| GET | `/inventory` | Check inventory (?sku=X / ?product_id=Y / ?warehouse_id=Z) |
| GET | `/inventory/transactions` | Stock change history |
| GET | `/categories` | List product categories |
| POST | `/categories` | Create category |

### Public (No Auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |

### Example: Stock In

```bash
curl -X POST http://localhost:8000/stock-in \
  -H "Authorization: Bearer <JWT>" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "warehouse_id": 1, "quantity": 10, "reference_id": "PO-001"}'
```

### Example: Bulk Upload

```bash
curl -X POST http://localhost:8000/products/bulk-upload \
  -H "Authorization: Bearer <JWT>" \
  -F "file=@products.xlsx"
```

### Example: Check Inventory by SKU

```bash
curl -H "Authorization: Bearer <JWT>" \
  http://localhost:8000/inventory?sku=PRD-001
```

## Database Schema

### Tables

| Table | Purpose |
|-------|---------|
| `products` | Master product data (SKU, name, price, cost_price, description, category, images, attributes) |
| `categories` | Product taxonomy |
| `warehouses` | Warehouse locations |
| `inventory` | Current stock per product/warehouse (`real_qty`) |
| `inventory_transactions` | Stock change history (`delta_qty`) with trigger |
| `schema_migrations` | Migration tracking |

### Trigger Logic

```sql
-- When INSERT to inventory_transactions:
-- 1. Upsert inventory table (product_id + warehouse_id)
-- 2. real_qty = real_qty + delta_qty
-- 3. Handle ON CONFLICT for existing product/warehouse combos
```

## Development

### Migrations

Folder-based SQL migrations (no Alembic/ORM):

```bash
make migrate          # Apply unapplied migrations
```

Migration files: `migrations/001_init.sql`, `migrations/002_add_product_fields.sql`

### Makefile Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start infra + migrate + Granian |
| `make stop` | Stop central infra containers |
| `make db-reset` | Restart Postgres (NO data loss) |
| `make db-nuke` | Destroy all data (requires YES confirmation) |
| `make clean` | Remove build artifacts |

### Project Structure

```
salak/
├── app/
│   ├── main.py          # FastAPI app, routes, auth, DB
│   └── bulk.py           # Bulk upload (Excel → Minio → DB)
├── migrations/           # SQL migration files
├── migrate.py            # Custom migration runner
├── Makefile
├── pyproject.toml
└── .env
```

## Integration with Pomegranate Ecosystem

- **Mangosteen (Go):** JWT authentication via JWKS endpoint
- **Granate (Rust):** CMS referencing product data
- **Kelapa (Elixir + Elm):** Ecommerce storefront & admin — uses service token to read/write products/stock
- **Pome (Bun + HTMX):** Central backoffice — bulk operations, warehouse management

## License

MIT

---

Part of **Salad Buah** — Pick the fruits you need. Skip the rest.
