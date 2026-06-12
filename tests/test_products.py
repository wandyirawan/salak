import pytest

def test_create_product(client, auth_headers):
    payload = {
        "sku": "PROD-001",
        "name": "Test Product",
        "price": 10000
    }
    resp = client.post("/products", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["sku"] == "PROD-001"
    assert data["name"] == "Test Product"
    assert data["price"] == 10000

def test_list_products(client, auth_headers):
    # Create 2 products
    for i in range(2):
        payload = {
            "sku": f"PROD-{i:03d}",
            "name": f"Test Product {i}",
            "price": 10000 + i
        }
        resp = client.post("/products", json=payload, headers=auth_headers)
        assert resp.status_code == 200

    resp = client.get("/products", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2

def test_get_product(client, auth_headers):
    # Create product
    payload = {
        "sku": "PROD-GET",
        "name": "Get Test Product",
        "price": 15000
    }
    resp = client.post("/products", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    product = resp.json()
    product_id = product["id"]

    # Get product
    resp = client.get(f"/products/{product_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == product_id
    assert data["sku"] == "PROD-GET"
    assert data["name"] == "Get Test Product"

def test_get_product_404(client, auth_headers):
    resp = client.get("/products/99999", headers=auth_headers)
    assert resp.status_code == 404

def test_get_cogs(client, auth_headers):
    # Create product with cost_price
    payload = {
        "sku": "PROD-COGS",
        "name": "COGS Test Product",
        "price": 15000,
        "cost_price": 5000
    }
    resp = client.post("/products", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    product = resp.json()
    product_id = product["id"]

    # Get COGS
    resp = client.get(f"/products/{product_id}/cogs", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "sku" in data
    assert "cost_price" in data
    assert data["cost_price"] == 5000

def test_get_cogs_404(client, auth_headers):
    resp = client.get("/products/99999/cogs", headers=auth_headers)
    assert resp.status_code == 404

def test_update_product(client, auth_headers):
    # Create product
    payload = {
        "sku": "PROD-UPDATE",
        "name": "Update Test Product",
        "price": 15000
    }
    resp = client.post("/products", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    product = resp.json()
    product_id = product["id"]

    # Update product
    update_payload = {
        "name": "Updated Product Name"
    }
    resp = client.put(f"/products/{product_id}", json=update_payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Product Name"

def test_update_product_404(client, auth_headers):
    payload = {
        "name": "Updated Product Name"
    }
    resp = client.put("/products/99999", json=payload, headers=auth_headers)
    assert resp.status_code == 404

def test_delete_product(client, auth_headers):
    # Create product
    payload = {
        "sku": "PROD-DELETE",
        "name": "Delete Test Product",
        "price": 15000
    }
    resp = client.post("/products", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    product = resp.json()
    product_id = product["id"]
    product_sku = product["sku"]

    # Delete product
    resp = client.delete(f"/products/{product_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["deleted"] == product_id
    assert data["sku"] == product_sku

def test_delete_product_404(client, auth_headers):
    resp = client.delete("/products/99999", headers=auth_headers)
    assert resp.status_code == 404
