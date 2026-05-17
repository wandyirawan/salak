-- 003_enforce_category_fk.sql
-- Change category_id FK from ON DELETE SET NULL to ON DELETE RESTRICT
-- Products must always belong to a category (like Magento behavior)

-- Step 1: Drop existing FK
ALTER TABLE products
    DROP CONSTRAINT IF EXISTS products_category_id_fkey;

-- Step 2: Re-add with RESTRICT (prevents deleting a category that still has products)
ALTER TABLE products
    ADD CONSTRAINT products_category_id_fkey
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT;
