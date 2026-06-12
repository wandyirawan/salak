import os
import pytest
from fastapi.testclient import TestClient
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()
os.environ["DATABASE_URL"] = "postgresql://salak:salak123@localhost:5433/salak_test"

def get_test_db():
    return connect(os.environ["DATABASE_URL"], cursor_factory=RealDictCursor)

def override_verify_token():
    return {"sub": "test-user-123", "email": "test@example.com", "role": "admin"}

@pytest.fixture(scope="module")
def test_app():
    from app.main import app
    from app.auth import verify_token
    app.dependency_overrides[verify_token] = override_verify_token
    yield app
    app.dependency_overrides.clear()

@pytest.fixture(scope="module")
def client(test_app):
    with TestClient(test_app) as c:
        yield c

@pytest.fixture(scope="function", autouse=True)
def clean_db():
    yield
    conn = get_test_db()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM inventory_transactions")
        cur.execute("DELETE FROM inventory")
        cur.execute("DELETE FROM products")
        cur.execute("DELETE FROM categories")
        cur.execute("DELETE FROM warehouses")
        conn.commit()
    finally:
        conn.close()

@pytest.fixture
def auth_headers():
    return {"Authorization": "Bearer mock-test-token"}
