"""Tests for dashboard analytics endpoints."""
import pytest


def _register_and_login(client, email, password, role="admin", name="User"):
    client.post(
        "/auth/register",
        json={"name": name, "email": email, "password": password, "role": role},
    )
    resp = client.post("/auth/login", data={"username": email, "password": password})
    return resp.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def _seed_records(client, token):
    records = [
        {"amount": 50000, "type": "income", "category": "Salary", "date": "2026-01-01"},
        {"amount": 20000, "type": "income", "category": "Freelance", "date": "2026-01-15"},
        {"amount": 15000, "type": "expense", "category": "Rent", "date": "2026-01-05"},
        {"amount": 5000, "type": "expense", "category": "Food", "date": "2026-02-10"},
    ]
    for r in records:
        client.post("/records/", json=r, headers=_auth(token))


def test_summary_all_roles(client):
    admin_token = _register_and_login(client, "sumadmin@test.com", "pass1234", "admin")
    _seed_records(client, admin_token)

    for role, email in [("viewer", "sumv@t.com"), ("analyst", "suma@t.com")]:
        token = _register_and_login(client, email, "pass1234", role)
        resp = client.get("/dashboard/summary", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "total_income" in data
        assert "total_expense" in data
        assert "net_balance" in data
        assert data["net_balance"] == data["total_income"] - data["total_expense"]


def test_category_breakdown_analyst_and_admin(client):
    admin_token = _register_and_login(client, "cbadmin@test.com", "pass1234", "admin")
    _seed_records(client, admin_token)

    analyst_token = _register_and_login(client, "cbanalyst@test.com", "pass1234", "analyst")

    for token in [admin_token, analyst_token]:
        resp = client.get("/dashboard/category-breakdown", headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        assert "breakdown" in data
        assert len(data["breakdown"]) > 0


def test_category_breakdown_viewer_denied(client):
    viewer_token = _register_and_login(client, "cbviewer@test.com", "pass1234", "viewer")
    resp = client.get("/dashboard/category-breakdown", headers=_auth(viewer_token))
    assert resp.status_code == 403


def test_monthly_trends(client):
    admin_token = _register_and_login(client, "mtadmin@test.com", "pass1234", "admin")
    _seed_records(client, admin_token)

    resp = client.get("/dashboard/monthly-trends?months=12", headers=_auth(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "trends" in data
    for trend in data["trends"]:
        assert "year" in trend
        assert "month" in trend
        assert "income" in trend
        assert "expense" in trend
        assert trend["net"] == pytest.approx(trend["income"] - trend["expense"])


def test_recent_activity(client):
    admin_token = _register_and_login(client, "raadmin@test.com", "pass1234", "admin")
    _seed_records(client, admin_token)

    resp = client.get("/dashboard/recent-activity?limit=3", headers=_auth(admin_token))
    assert resp.status_code == 200
    data = resp.json()
    assert "transactions" in data
    assert len(data["transactions"]) <= 3


def test_unauthenticated_access_denied(client):
    resp = client.get("/dashboard/summary")
    assert resp.status_code == 401
