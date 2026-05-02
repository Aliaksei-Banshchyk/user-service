"""
test_users.py – UserService
Place at the ROOT of the user-service repo.
Run with: pytest test_users.py -v
"""
import pytest
from fastapi.testclient import TestClient


# ── /health ───────────────────────────────────────────────────────────────────

def test_health(client):
    c, _ = client
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── POST /api/register ────────────────────────────────────────────────────────

def test_register_success(client):
    c, _ = client
    r = c.post("/api/register", json={
        "login": "alice", "password": "secure1", "name": "Alice"
    })
    assert r.status_code == 201
    data = r.json()
    assert data["login"] == "alice"
    assert data["name"] == "Alice"
    assert "id" in data
    assert "password" not in data


def test_register_duplicate_login(client):
    c, _ = client
    payload = {"login": "bob123", "password": "secure1", "name": "Bob"}
    c.post("/api/register", json=payload)
    r = c.post("/api/register", json=payload)
    assert r.status_code == 409


def test_register_login_too_short(client):
    c, _ = client
    r = c.post("/api/register", json={
        "login": "ab", "password": "secure1", "name": "Short"
    })
    assert r.status_code == 422


def test_register_login_invalid_chars(client):
    c, _ = client
    r = c.post("/api/register", json={
        "login": "bad login!", "password": "secure1", "name": "Bad"
    })
    assert r.status_code == 422


def test_register_password_too_short(client):
    c, _ = client
    r = c.post("/api/register", json={
        "login": "validuser", "password": "abc", "name": "Weak"
    })
    assert r.status_code == 422


# ── POST /api/login ───────────────────────────────────────────────────────────

def test_login_success(client):
    c, _ = client
    c.post("/api/register", json={
        "login": "carol123", "password": "mypassword", "name": "Carol"
    })
    r = c.post("/api/login", json={"login": "carol123", "password": "mypassword"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    c, _ = client
    c.post("/api/register", json={
        "login": "dave123", "password": "rightpass", "name": "Dave"
    })
    r = c.post("/api/login", json={"login": "dave123", "password": "wrongpass"})
    assert r.status_code == 401


def test_login_unknown_user(client):
    c, _ = client
    r = c.post("/api/login", json={"login": "nobody", "password": "x"})
    assert r.status_code == 401


# ── GET /api/users/me ─────────────────────────────────────────────────────────

def test_get_me(client):
    c, test_user = client
    r = c.get("/api/users/me")
    assert r.status_code == 200
    assert r.json()["login"] == test_user.login


# ── PATCH /api/users/me ───────────────────────────────────────────────────────

def test_update_name(client):
    c, _ = client
    r = c.patch("/api/users/me", json={"name": "Updated Name"})
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Name"


def test_update_password(client):
    c, _ = client
    r = c.patch("/api/users/me", json={"password": "newpassword"})
    assert r.status_code == 200


def test_update_no_fields(client):
    c, _ = client
    r = c.patch("/api/users/me", json={})
    assert r.status_code == 200
