# Salak Inventory

Snake fruit inventory service (Python/FastAPI + Granian) for Pomegranate ecosystem.

## Overview

Salak is a lightweight inventory management service using:
- **FastAPI** (Python web framework)
- **Granian** (Rust-powered ASGI server)
- **PostgreSQL** (with database triggers for stock consistency)
- **Mangosteen** (Authentication via JWKS)

## Architecture

```
Pomelo (Ecommerce) / HR App
    ↓ (JWT Token)
Salak (Inventory Service)
    ↓ (INSERT to inventory_transactions)
PostgreSQL Trigger → Auto-update inventory (real_qty)
```

### Key Concept: Trigger-Based Stock Updates

- **History (Delta):** `inventory_transactions` table stores stock changes (+5, -3)
- **State (Real):** `inventory` table stores current stock (real_qty)
- **Trigger:** Database trigger automatically updates `real_qty` when new transaction is inserted

This ensures **ACID compliance** - stock updates are atomic and consistent.

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

### 2. Start Database

```bash
make dev
```

This command:
- Starts PostgreSQL container (port 5433)
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
```

## API Endpoints

### Public (No Auth)
- `GET /health` - Health check
- `GET /db-check` - Database connection check
- `GET /warehouses` - List warehouses
- `GET /products` - List products
- `GET /inventory` - Check inventory (all/by product/warehouse)

### Protected (Requires JWT from Mangosteen)
- `POST /warehouses` - Create warehouse
- `POST /products` - Create product
- `POST /stock-in` - Add stock (delta positive)
- `POST /stock-out` - Remove stock (delta negative, checks real_qty)
- `GET /inventory/check?sku=X` - Check stock by SKU

### Example: Stock In

```bash
curl -X POST http://localhost:8000/stock-in \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "warehouse_id": 1, "quantity": 10, "reference_id": "PO-001"}'
```

## Database Schema

### Tables
- `products` - Master product data (SKU, name, attributes JSONB)
- `warehouses` - Warehouse locations
- `inventory` - Current stock per product/warehouse (real_qty)
- `inventory_transactions` - Stock change history (delta_qty)
- `schema_migrations` - Migration tracking

### Trigger Logic

```sql
-- When INSERT to inventory_transactions:
-- 1. Insert/Update inventory table
-- 2. real_qty = real_qty + delta_qty
-- 3. Handle conflict (ON CONFLICT) for existing product/warehouse
```

## Development

### Run Migrations Manually

```bash
uv run python migrate.py
```

### Stop Services

```bash
make stop
```

### Reset Database

```bash
make db-reset
```

## Integration with Pomegranate Ecosystem

- **Mangosteen (Go):** Provides JWT authentication (JWKS endpoint)
- **Granate (Rust):** CMS that may reference inventory data
- **Pomelo (Elixir):** Ecommerce that calls `/stock-out` on orders
- **HR App (Go):** May call `/stock-out` for asset management

## License

MIT

---

Part of **Pomegranate** - Lightweight ERP ecosystem.
