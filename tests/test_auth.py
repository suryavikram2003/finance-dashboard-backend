"""Tests for authentication endpoints."""
import pytest


def register_user(client, email, password, role="viewer", name="Test User"):
    return client.post(
        "/auth/register",
        json={"name": name, "email": email, "password": password, "role": role},
    )


def login_user(client, email, password):
    return client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )


def test_register_success(client):
    resp = register_user(client, "test1@example.com", "pass1234")
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "test1@example.com"
    assert data["role"] == "viewer"
    assert data["is_active"] is True
    assert "hashed_password" not in data


def test_register_duplicate_email(client):
    register_user(client, "dup@example.com", "pass1234")
    resp = register_user(client, "dup@example.com", "pass5678")
    assert resp.status_code == 409


def test_register_short_password(client):
    resp = register_user(client, "short@example.com", "123")
    assert resp.status_code == 422


def test_login_success(client):
    register_user(client, "login@example.com", "secure123", role="admin")
    resp = login_user(client, "login@example.com", "secure123")
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    register_user(client, "wrongpw@example.com", "correct123")
    resp = login_user(client, "wrongpw@example.com", "wrong123")
    assert resp.status_code == 401


def test_refresh_token(client):
    register_user(client, "refresh@example.com", "pass1234")
    login_resp = login_user(client, "refresh@example.com", "pass1234")
    refresh_token = login_resp.json()["refresh_token"]

    resp = client.post("/auth/refresh", json={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_refresh_with_access_token_fails(client):
    register_user(client, "badrefresh@example.com", "pass1234")
    login_resp = login_user(client, "badrefresh@example.com", "pass1234")
    access_token = login_resp.json()["access_token"]

    resp = client.post("/auth/refresh", json={"refresh_token": access_token})
    assert resp.status_code == 401
