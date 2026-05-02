"""
Tests for UserService – users.py
Covers: register, login, get_me, update_me
"""


def test_register_success(client):
    c, _ = client
    resp = c.post("/api/register", json={"login": "newuser", "password": "secret99", "name": "New User"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["login"] == "newuser"
    assert data["name"] == "New User"
    assert "id" in data
    assert "password" not in data


def test_register_duplicate_login(client):
    c, _ = client
    c.post("/api/register", json={"login": "dupuser", "password": "secret99", "name": "Dup"})
    resp = c.post("/api/register", json={"login": "dupuser", "password": "secret99", "name": "Dup2"})
    assert resp.status_code == 409


def test_register_short_login(client):
    c, _ = client
    resp = c.post("/api/register", json={"login": "ab", "password": "secret99", "name": "X"})
    assert resp.status_code == 422


def test_register_weak_password(client):
    c, _ = client
    resp = c.post("/api/register", json={"login": "validlogin", "password": "123", "name": "X"})
    assert resp.status_code == 422


def test_login_success(client, db):
    import models, auth
    c, _ = client
    db.add(models.User(id=99, login="logintest", password=auth.hash_password("mypassword"), name="Login Test"))
    db.commit()
    resp = c.post("/api/login", json={"login": "logintest", "password": "mypassword"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client, db):
    import models, auth
    c, _ = client
    db.add(models.User(id=100, login="wrongpw", password=auth.hash_password("correct"), name="WP"))
    db.commit()
    resp = c.post("/api/login", json={"login": "wrongpw", "password": "wrong"})
    assert resp.status_code == 401


def test_login_unknown_user(client):
    c, _ = client
    resp = c.post("/api/login", json={"login": "nobody", "password": "whatever"})
    assert resp.status_code == 401


def test_get_me(client):
    c, test_user = client
    resp = c.get("/api/users/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == test_user.id
    assert data["login"] == test_user.login
    assert data["name"] == test_user.name


def test_update_me_name(client):
    c, _ = client
    resp = c.patch("/api/users/me", json={"name": "Updated Name"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


def test_update_me_password(client):
    c, _ = client
    resp = c.patch("/api/users/me", json={"password": "newpassword99"})
    assert resp.status_code == 200


def test_health(client):
    c, _ = client
    resp = c.get("/health")
    assert resp.status_code == 200
    assert resp.json()["service"] == "UserService"
