from passlib.hash import bcrypt as bc

from app.models.models import Person, Role


def test_login_and_me(client, db):
    password = "demo1234"
    person = Person(
        last_name="Auth",
        first_name="Test",
        role=Role.SDO,
        username="auth.test",
        password_hash=bc.hash(password),
        is_active=True,
    )
    db.add(person)
    db.flush()

    bad = client.post("/api/auth/login", json={"username": "auth.test", "password": "wrong"})
    assert bad.status_code == 401

    ok = client.post("/api/auth/login", json={"username": "auth.test", "password": password})
    assert ok.status_code == 200
    token = ok.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["username"] == "auth.test"
    assert body["role"] == "sdo"


def test_api_requires_auth(client):
    resp = client.get("/api/persons")
    assert resp.status_code == 401


def test_audit_accessible_to_authenticated_user(client, db):
    password = "demo1234"
    pilot = Person(
        last_name="Line",
        first_name="Pilot",
        role=Role.PILOT,
        username="line.pilot",
        password_hash=bc.hash(password),
        is_active=True,
    )
    db.add(pilot)
    db.flush()

    login = client.post("/api/auth/login", json={"username": "line.pilot", "password": password})
    token = login.json()["access_token"]
    resp = client.get("/api/audit", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200