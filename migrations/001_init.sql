-- 001_init.sql
-- Products Master
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    unit VARCHAR(50) DEFAULT 'pcs',
    attributes JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW()
);

-- Warehouses
CREATE TABLE IF NOT EXISTS warehouses (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location TEXT
);

-- Inventory Real Qty (State)
CREATE TABLE IF NOT EXISTS inventory (
    product_id INT REFERENCES products(id),
    warehouse_id INT REFERENCES warehouses(id),
    real_qty NUMERIC(15, 2) NOT NULL DEFAULT 0,
    PRIMARY KEY (product_id, warehouse_id)
);

-- Inventory Transactions (History / Delta)
CREATE TABLE IF NOT EXISTS inventory_transactions (
    id SERIAL PRIMARY KEY,
    product_id INT REFERENCES products(id),
    warehouse_id INT REFERENCES warehouses(id),
    delta_qty NUMERIC(15, 2) NOT NULL,
    reference_id VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Function Trigger
CREATE OR REPLACE FUNCTION update_inventory_qty()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO inventory (product_id, warehouse_id, real_qty)
    VALUES (NEW.product_id, NEW.warehouse_id, NEW.delta_qty)
    ON CONFLICT (product_id, warehouse_id) 
    DO UPDATE SET real_qty = inventory.real_qty + NEW.delta_qty;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger
DROP TRIGGER IF EXISTS trg_update_stock ON inventory_transactions;
CREATE TRIGGER trg_update_stock
AFTER INSERT ON inventory_transactions
FOR EACH ROW
EXECUTE FUNCTION update_inventory_qty();

-- Migration Tracker
CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT NOW()
);
