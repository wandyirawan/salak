from fastapi import APIRouter, HTTPException, Depends
import psycopg2
from ..db import get_db
from ..auth import verify_token
from ..schemas.warehouses import WarehouseCreate, WarehouseUpdate

router = APIRouter(tags=["warehouses"])

@router.post("")
def create_warehouse(data: WarehouseCreate, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO warehouses (name, location) VALUES (%s, %s) RETURNING *",
                    (data.name, data.location))
        row = cur.fetchone()
        conn.commit()
        return row
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("")
def list_warehouses(user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM warehouses")
    rows = cur.fetchall()
    conn.close()
    return rows

@router.get("/{warehouse_id}")
def get_warehouse(warehouse_id: int, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM warehouses WHERE id=%s", (warehouse_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return row

@router.put("/{warehouse_id}")
def update_warehouse(warehouse_id: int, data: WarehouseUpdate, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    try:
        updates = {k: v for k, v in data.dict().items() if v is not None}
        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")
        set_clause = ", ".join(f"{k} = %s" for k in updates)
        vals = list(updates.values()) + [warehouse_id]
        cur.execute(f"UPDATE warehouses SET {set_clause} WHERE id = %s RETURNING *", vals)
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        conn.commit()
        return row
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.delete("/{warehouse_id}")
def delete_warehouse(warehouse_id: int, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM warehouses WHERE id = %s RETURNING *", (warehouse_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Warehouse not found")
        conn.commit()
        return {"deleted": row["id"], "name": row["name"]}
    except HTTPException:
        raise
    except psycopg2.errors.ForeignKeyViolation:
        conn.rollback()
        raise HTTPException(status_code=409, detail="Cannot delete: warehouse has inventory or transaction records")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()