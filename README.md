# Salak — Product & Inventory Service

Snake fruit product & inventory microservice (Python/FastAPI + Granian) for Pomegranate ecosystem.
Single source of truth for products, pricing, categories, stock movement, and warehouse management.

## Why Refactor: From Monolith to Modular

**The problem with `app/main.py` (513 lines):**

When we started, a single `main.py` worked fine — all routes, SQL, auth, and config in one file.
But as the service grew, several symptoms appeared:

1. **Navigability** — Finding `bulk_upload` meant scrolling through 500+ lines. Finding the right SQL query to modify meant searching through mixed concerns.

2. **Testability** — You couldn't import a single endpoint or service function in isolation. Everything was entangled with FastAPI's app lifecycle.

3. **Inconsistency with Orange** — When we built Orange (Sales microservice), we used Elysia-style modular structure from day one. Two services with completely different code organizations made cross-service reasoning harder.

4. **Adding features required touching the monolith** — Want to add a new router? You had to find the right section in main.py, add the route, add the import. Easy to accidentally break adjacent routes.

**The Elysia-inspired solution:**

We split `main.py` into logical context boundaries — same pattern used across the Pomegranate stack:

```
app/
├── main.py              # App wiring only (60 lines now)
├── config.py            # Settings from env
├── db.py                # psycopg2 connection helper
├── auth.py              # JWT verification (Mangosteen JWKS)
├── routers/             # One file per domain
│   ├── health.py        # GET /health
│   ├── auth.py          # POST /auth/login
│   ├── warehouses.py    # /warehouses CRUD
│   ├── categories.py    # /categories CRUD
│   ├── products.py      # /products CRUD + list/search
│   ├── inventory.py     # /stock-in, /stock-out, /inventory
│   └── bulk.py          # /products/template, /products/bulk-upload
├── schemas/             # Pydantic request/response models (one file per domain)
│   ├── products.py
│   ├── categories.py
│   ├── warehouses.py
│   └── inventory.py
└── services/            # Business logic layer (placeholder for future extraction)
```

**Why this works:**

- **Prefix is in `include_router()`, not in the router file** — Routers are prefix-agnostic. This means you can reorder, regroup, or re-prefix routers without touching the router file itself.
- **One domain per file** — You always know where to look. `inventory.py` has stock operations. `bulk.py` has Excel upload. No hunting.
- **Schemas are reusable** — Pydantic models in `schemas/` can be imported in tests, CLI scripts, or future service-to-service clients.
- **Consistent with Orange** — Both Orange and Salak now share the same structural pattern. When you work on one, you immediately understand the other.
- **KISS** — We didn't over-split. Bulk upload stays in one file despite being 300+ lines internally. Products CRUD is in one file despite covering 5 endpoints. Logical boundaries, not mechanical decomposition.

**What didn't change:**
- All endpoint logic (SQL, error handling, auth checks) is identical — we only moved code
- Database schema and migrations are untouched
- Route paths are preserved exactly (verified with 27-route test)
- No new dependencies

## Overview

Salak uses:
- **FastAPI** (Python web framework)
- **Granian** (Rust-powered ASGI server — same as Orange)
- **PostgreSQL** (with database triggers for stock consistency)
- **Mangosteen** (Authentication via JWKS)
- **Minio** (Excel file storage for bulk upload)

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
- Starts Salak with Granian (port 4002)

### 3. Verify

```bash
curl http://localhost:4002/health
# {"status": "ok", "service": "salak"}
```

## Environment Variables

Create `.env` file:

```env
PORT=4002
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/salak
MANGOSTEEN_URL=http://localhost:4001
MANGOSTEEN_JWKS_URL=http://localhost:4001/api/.well-known/jwks.json
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=pomegranate
MINIO_SECRET_KEY=pomegranate123
```

## API Endpoints

All endpoints require JWT from Mangosteen except `/health`.

### Public (No Auth)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/auth/login` | Proxy login to Mangosteen → returns JWT |

### Protected (Requires JWT)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/warehouses` | List warehouses |
| POST | `/warehouses` | Create warehouse |
| GET | `/warehouses/{id}` | Get warehouse by ID |
| PUT | `/warehouses/{id}` | Update warehouse |
| DELETE | `/warehouses/{id}` | Delete warehouse (409 if has inventory) |
| GET | `/products` | List products (`?category=X&search=Y`) |
| POST | `/products` | Create product |
| GET | `/products/{id}` | Get product by ID |
| PUT | `/products/{id}` | Update product |
| DELETE | `/products/{id}` | Delete product (409 if has inventory) |
| GET | `/products/template` | Download Excel template for bulk upload |
| POST | `/products/bulk-upload` | Upload Excel → Minio → parse → bulk insert |
| POST | `/stock-in` | Add stock (delta positive) |
| POST | `/stock-out` | Remove stock (delta negative, checks real_qty) |
| GET | `/inventory` | Check inventory (`?sku=X` / `?product_id=Y` / `?warehouse_id=Z`) |
| GET | `/inventory/transactions` | Stock change history (`?product_id=X&limit=N`) |
| GET | `/categories` | List product categories |
| POST | `/categories` | Create category |
| GET | `/categories/{id}` | Get category by ID |
| PUT | `/categories/{id}` | Update category |
| DELETE | `/categories/{id}` | Delete category (409 if has products) |

### Example: Stock In

```bash
curl -X POST http://localhost:4002/stock-in \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "warehouse_id": 1, "quantity": 10, "reference_id": "PO-001"}'
```

### Example: Bulk Upload

```bash
curl -X POST http://localhost:4002/products/bulk-upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@products.xlsx"
```

### Example: Check Inventory by SKU

```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:4002/inventory?sku=PRD-001"
```

## Project Structure

```
salak/
├── app/
│   ├── main.py              # FastAPI app wiring + startup migrations (60 lines)
│   ├── config.py            # Settings from environment variables
│   ├── db.py                # psycopg2 helper (get_db with RealDictCursor)
│   ├── auth.py              # JWT verification via Mangosteen JWKS
│   ├── schemas/             # Pydantic models (request/response validation)
│   │   ├── products.py      # ProductCreate, ProductUpdate
│   │   ├── categories.py    # CategoryCreate, CategoryUpdate
│   │   ├── warehouses.py    # WarehouseCreate, WarehouseUpdate
│   │   └── inventory.py     # StockIn, StockOut
│   ├── routers/             # Route handlers (one file per domain)
│   │   ├── health.py        # GET /health
│   │   ├── auth.py          # POST /auth/login (proxy to Mangosteen)
│   │   ├── warehouses.py    # /warehouses CRUD
│   │   ├── categories.py    # /categories CRUD
│   │   ├── products.py      # /products CRUD + list + search
│   │   ├── inventory.py     # /stock-in, /stock-out, /inventory
│   │   └── bulk.py          # /products/template, /products/bulk-upload
│   └── services/            # Business logic layer (placeholder)
├── migrations/              # SQL migration files (folder-based, no Alembic)
│   ├── 001_init.sql
│   ├── 002_add_product_fields.sql
│   ├── 003_enforce_category_fk.sql
│   └── 004_add_search_index.sql
├── migrate.py               # Custom migration runner
├── Makefile                 # dev, migrate, db-reset, db-nuke, clean
├── pyproject.toml
└── .env.example
```

### Routing Convention

Routers define routes **without** a prefix. The prefix is applied at include time in `main.py`:

```python
# In main.py — clean separation of concerns
app.include_router(products_router, prefix="/products")   # routes get /products/*
app.include_router(inventory_router)                      # routes get /stock-in, /stock-out
```

This makes routers reusable with different prefixes if needed.

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

## Migrations

Folder-based SQL migrations (no Alembic/ORM):

```bash
make migrate          # Apply unapplied migrations
```

## Makefile Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start infra + migrate + Granian |
| `make stop` | Stop central infra containers |
| `make db-reset` | Restart Postgres (no data loss) |
| `make db-nuke` | Destroy all data (requires YES confirmation) |
| `make clean` | Remove build artifacts |

## Integration with Pomegranate Ecosystem

```
[Kelapa - Elm/Eixir]    (ecommerce storefront, admin)
        ↓ (JWT via Mangosteen)
[Salak - Python/FastAPI] (product master + inventory triggers)
        ↓ (stock reservation request)
[Orange - Python/FastAPI] (sales orders, invoices)
        ↓ (post invoice)
[Accounting - Python/FastAPI] (ledger)
```

- **Mangosteen (Go):** JWT authentication via JWKS endpoint
- **Orange (Python):** Receives orders, requests stock reservation from Salak
- **Granate (Rust):** CMS referencing product data
- **Kelapa (Elixir + Elm):** Ecommerce storefront & admin
- **Pome (Bun + HTMX):** Central backoffice — bulk operations, warehouse management

## License

MIT

---

Part of **Pomegranate** — Modular ERP/CMS stack. Pick the fruits you need. Skip the rest.