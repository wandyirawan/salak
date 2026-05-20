from fastapi import APIRouter, HTTPException, Depends
from ..db import get_db
from ..auth import verify_token
from ..schemas.inventory import StockIn, StockOut

router = APIRouter(tags=["inventory"])

@router.post("/stock-in")
def stock_in(data: StockIn, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO inventory_transactions (product_id, warehouse_id, delta_qty, reference_id, notes) VALUES (%s, %s, %s, %s, %s) RETURNING *",
                    (data.product_id, data.warehouse_id, data.quantity, data.reference_id, data.notes))
        row = cur.fetchone()
        conn.commit()
        return row
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.post("/stock-out")
def stock_out(data: StockOut, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    try:
        # Check real_qty
        cur.execute("SELECT real_qty FROM inventory WHERE product_id=%s AND warehouse_id=%s",
                    (data.product_id, data.warehouse_id))
        row = cur.fetchone()
        if not row or row['real_qty'] < data.quantity:
            raise HTTPException(status_code=400, detail="Insufficient stock")

        cur.execute("INSERT INTO inventory_transactions (product_id, warehouse_id, delta_qty, reference_id, notes) VALUES (%s, %s, %s, %s, %s) RETURNING *",
                    (data.product_id, data.warehouse_id, -abs(data.quantity), data.reference_id, data.notes))
        row = cur.fetchone()
        conn.commit()
        return row
    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@router.get("/inventory")
def check_inventory(product_id: int = None, warehouse_id: int = None, sku: str = None, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    if sku:
        cur.execute("SELECT id FROM products WHERE sku=%s", (sku,))
        prod = cur.fetchone()
        if not prod:
            raise HTTPException(status_code=404, detail="SKU not found")
        product_id = prod['id']
    if product_id and warehouse_id:
        cur.execute("SELECT * FROM inventory WHERE product_id=%s AND warehouse_id=%s", (product_id, warehouse_id))
    elif product_id:
        cur.execute("SELECT * FROM inventory WHERE product_id=%s", (product_id,))
    else:
        cur.execute("SELECT * FROM inventory")
    rows = cur.fetchall()
    conn.close()
    return rows

@router.get("/inventory/transactions")
def list_transactions(product_id: int = None, limit: int = 50, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    q = "SELECT t.*, p.name as product_name, p.sku FROM inventory_transactions t LEFT JOIN products p ON t.product_id = p.id"
    params = []
    if product_id:
        q += " WHERE t.product_id = %s"
        params.append(product_id)
    q += " ORDER BY t.created_at DESC LIMIT %s"
    params.append(limit)
    cur.execute(q, params)
    rows = cur.fetchall()
    conn.close()
    return rows