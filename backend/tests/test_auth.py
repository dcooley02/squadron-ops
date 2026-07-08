from passlib.hash import bcrypt as bc

from app.core.config import get_settings
from app.models.models import Person, Role


def _login(client, username: str, password: str = "demo1234") -> str:
    resp = client.post("/api/auth/login", json={"username": username, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


def _person(db, *, role: Role, username: str) -> Person:
    person = Person(
        last_name="Auth",
        first_name=role.value.title(),
        role=role,
        username=username,
        password_hash=bc.hash("demo1234"),
        is_active=True,
    )
    db.add(person)
    db.flush()
    return person


def test_login_and_me(client, db):
    _person(db, role=Role.SDO, username="auth.test")

    bad = client.post("/api/auth/login", json={"username": "auth.test", "password": "wrong"})
    assert bad.status_code == 401

    token = _login(client, "auth.test")
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    body = me.json()
    assert body["username"] == "auth.test"
    assert body["role"] == "sdo"


def test_api_requires_auth(client):
    resp = client.get("/api/persons")
    assert resp.status_code == 401


def test_audit_forbidden_for_pilot_when_rbac_enforced(client, db, monkeypatch):
    monkeypatch.setenv("DEMO_OPEN_RBAC", "false")
    get_settings.cache_clear()
    try:
        _person(db, role=Role.PILOT, username="line.pilot")
        token = _login(client, "line.pilot")
        resp = client.get("/api/audit", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 403
        assert "Insufficient role" in resp.json()["detail"]
    finally:
        get_settings.cache_clear()


def test_audit_allowed_for_admin(client, db, monkeypatch):
    monkeypatch.setenv("DEMO_OPEN_RBAC", "false")
    get_settings.cache_clear()
    try:
        _person(db, role=Role.ADMIN, username="admin.user")
        token = _login(client, "admin.user")
        resp = client.get("/api/audit", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
    finally:
        get_settings.cache_clear()


def test_audit_allowed_for_pilot_when_demo_open_rbac(client, db, monkeypatch):
    monkeypatch.setenv("DEMO_OPEN_RBAC", "true")
    get_settings.cache_clear()
    try:
        _person(db, role=Role.PILOT, username="open.pilot")
        token = _login(client, "open.pilot")
        resp = client.get("/api/audit", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
    finally:
        get_settings.cache_clear()


def test_maint_write_forbidden_for_pilot(client, db, aircraft, monkeypatch):
    monkeypatch.setenv("DEMO_OPEN_RBAC", "false")
    get_settings.cache_clear()
    try:
        _person(db, role=Role.PILOT, username="maint.pilot")
        token = _login(client, "maint.pilot")
        resp = client.post(
            f"/api/maintenance/aircraft/{aircraft.id}/discrepancies",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "description": "chip light",
                "severity": "MINOR",
                "type_wo_code": "DM",
            },
        )
        assert resp.status_code == 403
    finally:
        get_settings.cache_clear()
