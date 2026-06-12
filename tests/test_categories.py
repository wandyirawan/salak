import pytest

def test_create_category(client, auth_headers):
    payload = {
        "name": "Test Cat"
    }
    resp = client.post("/categories", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Test Cat"

def test_list_categories(client, auth_headers):
    # Create 2 categories
    for i in range(2):
        payload = {
            "name": f"Category {i}"
        }
        resp = client.post("/categories", json=payload, headers=auth_headers)
        assert resp.status_code == 200

    resp = client.get("/categories", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2

def test_get_category(client, auth_headers):
    # Create category
    payload = {
        "name": "Get Test Category"
    }
    resp = client.post("/categories", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    category = resp.json()
    category_id = category["id"]

    # Get category
    resp = client.get(f"/categories/{category_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == category_id
    assert data["name"] == "Get Test Category"

def test_get_category_404(client, auth_headers):
    resp = client.get("/categories/99999", headers=auth_headers)
    assert resp.status_code == 404

def test_update_category(client, auth_headers):
    # Create category
    payload = {
        "name": "Update Test Category"
    }
    resp = client.post("/categories", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    category = resp.json()
    category_id = category["id"]

    # Update category
    update_payload = {
        "name": "Updated Category Name"
    }
    resp = client.put(f"/categories/{category_id}", json=update_payload, headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated Category Name"

def test_delete_category(client, auth_headers):
    # Create category
    payload = {
        "name": "Delete Test Category"
    }
    resp = client.post("/categories", json=payload, headers=auth_headers)
    assert resp.status_code == 200
    category = resp.json()
    category_id = category["id"]
    category_name = category["name"]

    # Delete category
    resp = client.delete(f"/categories/{category_id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["deleted"] == category_id
    assert data["name"] == category_name
