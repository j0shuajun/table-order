"""End-to-end API flow against the real startup path (create_all + seed)."""

import re

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Real engine uses a relative sqlite path; run in a temp cwd so the DB and
    # seed land in an isolated file and startup exercises the real code path.
    monkeypatch.chdir(tmp_path)
    from app.main import app

    with TestClient(app) as c:
        yield c


def _table_token(client) -> str:
    resp = client.post(
        "/api/table/auth",
        json={"store_id": "store001", "table_number": "T1", "password": "0000"},
    )
    assert resp.status_code == 200
    return resp.json()["token"]


def _admin_token(client) -> str:
    resp = client.post(
        "/api/admin/login",
        json={"store_id": "store001", "username": "admin", "password": "admin1234"},
    )
    assert resp.status_code == 200
    return resp.json()["token"]


def test_full_customer_and_admin_flow(client):
    table_auth = {"Authorization": f"Bearer {_table_token(client)}"}

    menu = client.get("/api/menu", headers=table_auth).json()
    assert menu["categories"]
    first_menu = menu["categories"][0]["menus"][0]

    created = client.post(
        "/api/orders",
        headers=table_auth,
        json={"items": [{"menu_id": first_menu["id"], "quantity": 2}]},
    )
    assert created.status_code == 201
    body = created.json()
    assert re.fullmatch(r"\d{8}-\d{4}-\d{4}", body["order_number"])
    assert body["total_amount"] == first_menu["price"] * 2
    order_id = body["order_id"]

    current = client.get("/api/orders/current", headers=table_auth).json()
    assert current["session_total"] == first_menu["price"] * 2

    admin_auth = {"Authorization": f"Bearer {_admin_token(client)}"}
    tables = client.get("/api/admin/tables", headers=admin_auth).json()["tables"]
    t1 = [t for t in tables if t["table_number"] == "T1"][0]
    assert t1["current_total"] == first_menu["price"] * 2

    status = client.post(
        f"/api/admin/orders/{order_id}/status",
        headers=admin_auth,
        json={"status": "preparing"},
    )
    assert status.status_code == 200 and status.json()["status"] == "preparing"

    deleted = client.delete(f"/api/admin/orders/{order_id}", headers=admin_auth)
    assert deleted.status_code == 200 and deleted.json()["current_total"] == 0

    completed = client.post(
        f"/api/admin/tables/{t1['table_id']}/complete", headers=admin_auth
    )
    assert completed.status_code == 200


def test_auth_guards(client):
    # missing token -> 401
    assert client.get("/api/menu").status_code == 401
    # table token on admin endpoint -> 403
    table_auth = {"Authorization": f"Bearer {_table_token(client)}"}
    assert client.get("/api/admin/tables", headers=table_auth).status_code == 403


def test_order_validation_errors(client):
    table_auth = {"Authorization": f"Bearer {_table_token(client)}"}
    assert (
        client.post("/api/orders", headers=table_auth, json={"items": []}).status_code
        == 400
    )
    assert (
        client.post(
            "/api/orders",
            headers=table_auth,
            json={"items": [{"menu_id": 999999, "quantity": 1}]},
        ).status_code
        == 404
    )
