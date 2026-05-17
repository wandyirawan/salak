import os
import psycopg2
from psycopg2.extras import RealDictCursor
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from dotenv import load_dotenv
import logging
import jwt
import requests
from jwt.algorithms import RSAAlgorithm

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Salak Inventory", description="Snake fruit inventory (Python/Granian)")

# CORS — allow Pome (Bun/Elysia) frontend
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4021", "http://127.0.0.1:4021"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Setup
security = HTTPBearer()
_jwks_cache = None

def get_jwks():
    global _jwks_cache
    if not _jwks_cache:
        url = os.getenv("MANGOSTEEN_JWKS_URL")
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        _jwks_cache = resp.json()
    return _jwks_cache

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        jwks = get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header["kid"]
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Invalid token key")
        public_key = RSAAlgorithm.from_jwk(key)
        payload = jwt.decode(token, public_key, algorithms=["RS256"], options={"verify_aud": False})
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

def get_db():
    return psycopg2.connect(os.getenv("DATABASE_URL"), cursor_factory=RealDictCursor)

# Pydantic Models
class ProductCreate(BaseModel):
    sku: str
    name: str
    unit: str = "pcs"
    price: float = 0
    cost_price: float = 0
    description: str = ""
    category_id: int = None
    is_active: bool = True
    images: list = []
    attributes: dict = {}

class ProductUpdate(BaseModel):
    name: str = None
    unit: str = None
    price: float = None
    cost_price: float = None
    description: str = None
    category_id: int = None
    is_active: bool = None
    images: list = None
    attributes: dict = None

class CategoryCreate(BaseModel):
    name: str
    slug: str = None
    parent_id: int = None

class CategoryUpdate(BaseModel):
    name: str = None
    slug: str = None
    parent_id: int = None

class WarehouseCreate(BaseModel):
    name: str
    location: str = ""

class WarehouseUpdate(BaseModel):
    name: str = None
    location: str = None

class StockIn(BaseModel):
    product_id: int
    warehouse_id: int
    quantity: float
    reference_id: str = ""
    notes: str = ""

class StockOut(BaseModel):
    product_id: int
    warehouse_id: int
    quantity: float
    reference_id: str = ""
    notes: str = ""

@app.on_event("startup")
def startup():
    logger.info("Running migrations...")
    try:
        from migrate import run_migrations
        run_migrations()
        logger.info("Migrations done.")
    except Exception as e:
        logger.error(f"Migration failed: {e}")

@app.get("/health")
def health():
    return {"status": "ok", "service": "salak"}

# Auth proxy to Mangosteen
class LoginRequest(BaseModel):
    email: str
    password: str

@app.post("/auth/login")
def proxy_login(data: LoginRequest):
    """Proxy login to Mangosteen, return JWT for subsequent Salak API calls."""
    try:
        mangosteen = os.getenv("MANGOSTEEN_URL", "http://localhost:4000")
        resp = requests.post(
            f"{mangosteen}/api/auth/login",
            json={"email": data.email, "password": data.password},
            timeout=10,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=resp.status_code, detail=resp.text)
        return resp.json()
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Mangosteen unreachable: {e}")

@app.get("/db-check")
def db_check(user: dict = Depends(verify_token)):
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        conn.close()
        return {"db_status": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Warehouse Endpoints
@app.post("/warehouses")
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

@app.get("/warehouses")
def list_warehouses(user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM warehouses")
    rows = cur.fetchall()
    conn.close()
    return rows

@app.get("/warehouses/{warehouse_id}")
def get_warehouse(warehouse_id: int, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM warehouses WHERE id=%s", (warehouse_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Warehouse not found")
    return row

@app.put("/warehouses/{warehouse_id}")
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

@app.delete("/warehouses/{warehouse_id}")
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

# Product Endpoints
@app.post("/products")
def create_product(data: ProductCreate, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO products (sku, name, unit, price, cost_price, description, 
                                  category_id, is_active, images, attributes) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING *
        """, (data.sku, data.name, data.unit, data.price, data.cost_price, data.description,
              data.category_id, data.is_active, psycopg2.extras.Json(data.images),
              psycopg2.extras.Json(data.attributes)))
        row = cur.fetchone()
        conn.commit()
        return row
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

@app.put("/products/{product_id}")
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

@app.get("/products")
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

@app.get("/products/{product_id}")
def get_product(product_id: int, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT p.*, c.name as category_name FROM products p LEFT JOIN categories c ON p.category_id = c.id WHERE p.id=%s", (product_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Product not found")
    return row

@app.delete("/products/{product_id}")
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
    except psycopg2.errors.ForeignKeyViolation as e:
        conn.rollback()
        raise HTTPException(status_code=409, detail="Cannot delete: product has inventory or transaction records")
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# Stock Endpoints
@app.post("/stock-in")
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

@app.post("/stock-out")
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

@app.get("/inventory")
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

@app.get("/inventory/transactions")
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

# Category Endpoints
@app.get("/categories")
def list_categories(user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories ORDER BY name")
    rows = cur.fetchall()
    conn.close()
    return rows

@app.post("/categories")
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

@app.get("/categories/{category_id}")
def get_category(category_id: int, user: dict = Depends(verify_token)):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM categories WHERE id=%s", (category_id,))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Category not found")
    return row

@app.put("/categories/{category_id}")
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

@app.delete("/categories/{category_id}")
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

if __name__ == "__main__":
    import granian
    granian.run("app.main:app", host="0.0.0.0", port=8000, interface="asgi")


# Register routers
from app.bulk import router as bulk_router
app.include_router(bulk_router)
