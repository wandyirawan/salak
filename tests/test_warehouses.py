import pytest

def test_create_warehouse(client, auth_headers):
    payload = {
        "name": "WH1"
    }
    resp = client.post("/warehouses", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "WH1"

def test_list_warehouses(client, auth_headers):
    # Create 2 warehouses
    for i in range(2):
        payload = {
            "name": f"Warehouse {i}"
        }
        resp = client.post("/warehouses", json=payload, headers=auth_headers)
        assert resp.status_code == 200

    resp = client.get("/warehouses", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2

def test_get_warehouse(client, auth_headers):
    # Create warehouse
    payload = {
        "name": "Get Test Warehouse"
    }
    resp = client.post("/warehouses", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    warehouse = resp.json()
    warehouse_id = warehouse["id"]

    # Get warehouse
    resp = client.get(f"/warehouses/{warehouse_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == warehouse_id
    assert data["name"] == "Get Test Warehouse"

def test_get_warehouse_404(client, auth_headers):
    resp = client.get("/warehouses/99999", headers=auth_headers)
    assert resp.status_code == 404

def test_update_warehouse(client, auth_headers):
    # Create warehouse
    payload = {
        "name": "Update Test Warehouse"
    }
    resp = client.post("/warehouses", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    warehouse = resp.json()
    warehouse_id = warehouse["id"]

    # Update warehouse
    update_payload = {
        "name": "Updated Warehouse Name"
    }
    resp = client.put(f"/warehouses/{warehouse_id}", json=update_payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Warehouse Name"

def test_delete_warehouse(client, auth_headers):
    # Create warehouse
    payload = {
        "name": "Delete Test Warehouse"
    }
    resp = client.post("/warehouses", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    warehouse = resp.json()
    warehouse_id = warehouse["id"]
    warehouse_name = warehouse["name"]

    # Delete warehouse
    resp = client.delete(f"/warehouses/{warehouse_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["deleted"] == warehouse_id
    assert data["name"] == warehouse_name
