-- 004_add_search_index.sql
-- GIN trigram index for product name + SKU search
-- Enables fast ILIKE '%search_term%' without full table scan

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_products_name_gin
    ON products USING GIN (name gin_trgm_ops);

CREATE INDEX IF NOT EXISTS idx_products_sku_gin
    ON products USING GIN (sku gin_trgm_ops);
