from fastapi import APIRouter, HTTPException, Depends
import psycopg2
from ..db import get_db
from ..auth import verify_token
from ..schemas.categories import CategoryCreate, CategoryUpdate

router = APIRouter(tags=["categories"])

@router.get("")
def list_categories(user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows

@router.post("")
def create_category(data: CategoryCreate, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    try:
        slug = data.slug or data.name.lower().replace(" ", "-")
        cur.execute(
            "INSERT INTO categories (name, slug, parent_id) VALUES (%s, %s, %s) RETURNING *",
            (data.name, slug, data.parent_id))
        row = cur.fetchone()
        conn.commit()
        return row
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/{category_id}")
def get_category(category_id: int, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories WHERE id=%s", (category_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Category not found")
    return row

@router.put("/{category_id}")
def update_category(category_id: int, data: CategoryUpdate, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    try:
        updates = {k: v for k, v in data.dict().items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        vals = list(updates.values()) + [category_id]
        cur.execute(f"UPDATE categories SET {set_clause} WHERE id = %s RETURNING *", vals)
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Category not found")
        conn.commit()
        return row
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.delete("/{category_id}")
def delete_category(category_id: int, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM categories WHERE id = %s RETURNING *", (category_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Category not found")
        conn.commit()
        return {"deleted": row["id"], "name": row["name"]}
    except HTTPException:
        raise
    except psycopg2.errors.ForeignKeyViolation:
        conn.rollback()
        raise HTTPException(status_code=409, detail="Cannot delete: products or sub-categories still reference this category")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()