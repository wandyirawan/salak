from fastapi import APIRouter, HTTPException, Depends
import psycopg2
from psycopg2.extras import Json
from ..db import get_db
from ..auth import verify_token
from ..schemas.products import ProductCreate, ProductUpdate

router = APIRouter(tags=["products"])

@router.post("")
def create_product(data: ProductCreate, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO products (sku, name, unit, price, cost_price, description,
                                  category_id, is_active, images, attributes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *
        """, (data.sku, data.name, data.unit, data.price, data.cost_price, data.description,
              data.category_id, data.is_active, Json(data.images), Json(data.attributes)))
        row = cur.fetchone()
        conn.commit()
        return row
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("")
def list_products(category_id: int = None, search: str = None, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    q = "SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.is_active = TRUE"
    params = []
    if category_id:
        q += " AND p.category_id = %s"
        params.append(category_id)
    if search:
        q += " AND (p.name ILIKE %s OR p.sku ILIKE %s)"
        params.extend([f"%{search}%", f"%{search}%"])
    q += " ORDER BY p.name"
    cur.execute(q, params)
    rows = cur.fetchall()
    conn.close()
    return rows

@router.get("/{product_id}")
def get_product(product_id: int, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.id=%s", (product_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return row

@router.put("/{product_id}")
def update_product(product_id: int, data: ProductUpdate, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    try:
        updates = {k: v for k, v in data.dict().items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        vals = list(updates.values()) + [product_id]
        cur.execute(f"UPDATE products SET {set_clause} WHERE id = %s RETURNING *", vals)
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Product not found")
        conn.commit()
        return row
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.delete("/{product_id}")
def delete_product(product_id: int, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM products WHERE id = %s RETURNING *", (product_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Product not found")
        conn.commit()
        return {"deleted": row["id"], "sku": row["sku"]}
    except HTTPException:
        raise
    except psycopg2.errors.ForeignKeyViolation:
        conn.rollback()
        raise HTTPException(status_code=409, detail="Cannot delete: product has inventory or transaction records")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()