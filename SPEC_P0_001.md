# SPEC_P0_001: COGS Endpoint for Salak

## Description
Add a public (authenticated) endpoint that returns the cost_price (COGS) for a product
so Orange can validate selling price >= COGS before allowing a sale.

## Acceptance Criteria
- [ ] `GET /products/{id}/cogs` returns `{product_id, sku, cost_price}`
- [ ] Returns 404 if product not found
- [ ] Requires JWT (use existing `verify_token` from `app/auth.py`)
- [ ] No new dependencies
- [ ] No new files — add to existing `app/routers/products.py`
- [ ] All existing tests pass

## Files to Modify
- `app/routers/products.py` — add `get_product_cogs` route
- `app/schemas/products.py` — add `ProductCogsResponse` schema (if needed, or just return dict)

## Do
- Use existing psycopg2 raw SQL pattern (RealDictCursor)
- Use existing `verify_token` dependency for auth
- Return simple JSON: `{"product_id": int, "sku": str, "cost_price": float}`
- Add route inside products router (no separate file)

## Don't
- Do NOT create new router file
- Do NOT expose full product details — only cogs fields
- Do NOT change any existing routes or behavior
- Do NOT introduce new dependencies

## Context
Salak already has `cost_price` column in the `products` table (from migration 002).
Orange needs to call `GET http://localhost:8000/products/{product_id}/cogs` to validate pricing.
This is a minimal read-only endpoint.

## Completion
Write DONE.md summarizing what was implemented.
