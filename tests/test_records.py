"""Tests for financial records endpoints (RBAC + CRUD + filtering)."""
import pytest


def _register_and_login(client, email, password, role="viewer", name="User"):
    client.post(
        "/auth/register",
        json={"name": name, "email": email, "password": password, "role": role},
    )
    resp = client.post("/auth/login", data={"username": email, "password": password})
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


RECORD_PAYLOAD = {
    "amount": 10000.0,
    "type": "income",
    "category": "Salary",
    "date": "2026-01-15",
    "notes": "January salary",
}


def test_admin_can_create_record(client):
    token = _register_and_login(client, "adminrec@test.com", "pass1234", "admin")
    resp = client.post("/records/", json=RECORD_PAYLOAD, headers=_auth(token))
    assert resp.status_code == 201
    data = resp.json()
    assert data["amount"] == 10000.0
    assert data["type"] == "income"
    assert data["category"] == "Salary"
    assert data["is_deleted"] is False


def test_viewer_cannot_create_record(client):
    token = _register_and_login(client, "viewerrec@test.com", "pass1234", "viewer")
    resp = client.post("/records/", json=RECORD_PAYLOAD, headers=_auth(token))
    assert resp.status_code == 403


def test_analyst_cannot_create_record(client):
    token = _register_and_login(client, "analystrec@test.com", "pass1234", "analyst")
    resp = client.post("/records/", json=RECORD_PAYLOAD, headers=_auth(token))
    assert resp.status_code == 403


def test_all_roles_can_list_records(client):
    admin_token = _register_and_login(client, "adminlist@test.com", "pass1234", "admin")
    client.post("/records/", json=RECORD_PAYLOAD, headers=_auth(admin_token))

    for role, email in [("viewer", "v@list.com"), ("analyst", "a@list.com")]:
        token = _register_and_login(client, email, "pass1234", role)
        resp = client.get("/records/", headers=_auth(token))
        assert resp.status_code == 200
        assert "records" in resp.json()


def test_records_filter_by_type(client):
    admin_token = _register_and_login(client, "adminfilt@test.com", "pass1234", "admin")
    client.post(
        "/records/",
        json={"amount": 5000, "type": "expense", "category": "Food", "date": "2026-02-01"},
        headers=_auth(admin_token),
    )
    resp = client.get("/records/?type=expense", headers=_auth(admin_token))
    assert resp.status_code == 200
    for record in resp.json()["records"]:
        assert record["type"] == "expense"


def test_records_pagination(client):
    admin_token = _register_and_login(client, "adminpag@test.com", "pass1234", "admin")
    for i in range(5):
        client.post(
            "/records/",
            json={"amount": 100 * (i + 1), "type": "income", "category": "Test", "date": "2026-03-01"},
            headers=_auth(admin_token),
        )
    resp = client.get("/records/?page=1&page_size=2", headers=_auth(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["records"]) <= 2


def test_admin_can_update_record(client):
    token = _register_and_login(client, "adminupd@test.com", "pass1234", "admin")
    create_resp = client.post("/records/", json=RECORD_PAYLOAD, headers=_auth(token))
    record_id = create_resp.json()["id"]

    resp = client.put(
        f"/records/{record_id}",
        json={"amount": 99999.0},
        headers=_auth(token),
    )
    assert resp.status_code == 200
    assert resp.json()["amount"] == 99999.0


def test_admin_can_soft_delete_record(client):
    token = _register_and_login(client, "admindel@test.com", "pass1234", "admin")
    create_resp = client.post("/records/", json=RECORD_PAYLOAD, headers=_auth(token))
    record_id = create_resp.json()["id"]

    del_resp = client.delete(f"/records/{record_id}", headers=_auth(token))
    assert del_resp.status_code == 204

    # Record should no longer appear in listing
    list_resp = client.get("/records/", headers=_auth(token))
    ids = [r["id"] for r in list_resp.json()["records"]]
    assert record_id not in ids


def test_invalid_amount_rejected(client):
    token = _register_and_login(client, "validamt@test.com", "pass1234", "admin")
    resp = client.post(
        "/records/",
        json={"amount": -500, "type": "income", "category": "Test", "date": "2026-01-01"},
        headers=_auth(token),
    )
    assert resp.status_code == 422


def test_record_not_found(client):
    token = _register_and_login(client, "notfound@test.com", "pass1234", "admin")
    resp = client.get("/records/99999", headers=_auth(token))
    assert resp.status_code == 404
