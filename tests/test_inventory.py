import pytest

def test_stock_in(client, auth_headers):
    # Create product first
    product_payload = {
        "sku": "INV-PROD-001",
        "name": "Stock In Test Product",
        "price": 10000
    }
    resp = client.post("/products", json=product_payload, headers=auth_headers)
    assert resp.status_code == 200
    product = resp.json()
    product_id = product["id"]

    # Create warehouse
    warehouse_payload = {
        "name": "Stock In Warehouse"
    }
    resp = client.post("/warehouses", json=warehouse_payload, headers=auth_headers)
    assert resp.status_code == 200
    warehouse = resp.json()
    warehouse_id = warehouse["id"]

    # Stock in
    payload = {
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "quantity": 100
    }
    resp = client.post("/stock-in", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["product_id"] == product_id
    assert data["warehouse_id"] == warehouse_id
    assert data["delta_qty"] == 100

def test_stock_out(client, auth_headers):
    # Create product first
    product_payload = {
        "sku": "INV-PROD-002",
        "name": "Stock Out Test Product",
        "price": 10000
    }
    resp = client.post("/products", json=product_payload, headers=auth_headers)
    assert resp.status_code == 200
    product = resp.json()
    product_id = product["id"]

    # Create warehouse
    warehouse_payload = {
        "name": "Stock Out Warehouse"
    }
    resp = client.post("/warehouses", json=warehouse_payload, headers=auth_headers)
    assert resp.status_code == 200
    warehouse = resp.json()
    warehouse_id = warehouse["id"]

    # Stock in 100 first
    stock_in_payload = {
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "quantity": 100
    }
    resp = client.post("/stock-in", json=stock_in_payload, headers=auth_headers)
    assert resp.status_code == 200

    # Stock out 30
    stock_out_payload = {
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "quantity": 30
    }
    resp = client.post("/stock-out", json=stock_out_payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["product_id"] == product_id
    assert data["warehouse_id"] == warehouse_id
    assert data["delta_qty"] == -30

def test_stock_out_insufficient(client, auth_headers):
    # Create product first
    product_payload = {
        "sku": "INV-PROD-003",
        "name": "Insufficient Stock Test Product",
        "price": 10000
    }
    resp = client.post("/products", json=product_payload, headers=auth_headers)
    assert resp.status_code == 200
    product = resp.json()
    product_id = product["id"]

    # Create warehouse
    warehouse_payload = {
        "name": "Insufficient Stock Warehouse"
    }
    resp = client.post("/warehouses", json=warehouse_payload, headers=auth_headers)
    assert resp.status_code == 200
    warehouse = resp.json()
    warehouse_id = warehouse["id"]

    # Stock out 99999 without stocking in first (should fail)
    payload = {
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "quantity": 99999
    }
    resp = client.post("/stock-out", json=payload, headers=auth_headers)
    assert resp.status_code == 400

def test_check_inventory(client, auth_headers):
    # Create product first
    product_payload = {
        "sku": "INV-PROD-004",
        "name": "Check Inventory Test Product",
        "price": 10000
    }
    resp = client.post("/products", json=product_payload, headers=auth_headers)
    assert resp.status_code == 200
    product = resp.json()
    product_id = product["id"]

    # Create warehouse
    warehouse_payload = {
        "name": "Check Inventory Warehouse"
    }
    resp = client.post("/warehouses", json=warehouse_payload, headers=auth_headers)
    assert resp.status_code == 200
    warehouse = resp.json()
    warehouse_id = warehouse["id"]

    # Stock in
    payload = {
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "quantity": 50
    }
    resp = client.post("/stock-in", json=payload, headers=auth_headers)
    assert resp.status_code == 200

    # Check inventory
    resp = client.get("/inventory", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0

def test_check_inventory_by_sku(client, auth_headers):
    # Create product with specific SKU
    product_payload = {
        "sku": "INV-SKU",
        "name": "SKU Inventory Test Product",
        "price": 10000
    }
    resp = client.post("/products", json=product_payload, headers=auth_headers)
    assert resp.status_code == 200
    product = resp.json()
    product_id = product["id"]

    # Create warehouse
    warehouse_payload = {
        "name": "SKU Inventory Warehouse"
    }
    resp = client.post("/warehouses", json=warehouse_payload, headers=auth_headers)
    assert resp.status_code == 200
    warehouse = resp.json()
    warehouse_id = warehouse["id"]

    # Stock in
    payload = {
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "quantity": 25
    }
    resp = client.post("/stock-in", json=payload, headers=auth_headers)
    assert resp.status_code == 200

    # Check inventory by SKU
    resp = client.get("/inventory?sku=INV-SKU", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0

def test_list_transactions(client, auth_headers):
    # Create product first
    product_payload = {
        "sku": "INV-PROD-005",
        "name": "Transactions Test Product",
        "price": 10000
    }
    resp = client.post("/products", json=product_payload, headers=auth_headers)
    assert resp.status_code == 200
    product = resp.json()
    product_id = product["id"]

    # Create warehouse
    warehouse_payload = {
        "name": "Transactions Warehouse"
    }
    resp = client.post("/warehouses", json=warehouse_payload, headers=auth_headers)
    assert resp.status_code == 200
    warehouse = resp.json()
    warehouse_id = warehouse["id"]

    # Stock in
    payload = {
        "product_id": product_id,
        "warehouse_id": warehouse_id,
        "quantity": 75
    }
    resp = client.post("/stock-in", json=payload, headers=auth_headers)
    assert resp.status_code == 200

    # List transactions
    resp = client.get("/inventory/transactions", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
