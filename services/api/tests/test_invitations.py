def test_create_invitation_requires_auth(client):
    resp = client.post("/api/v1/invitations", json={"email": "x@y.com", "role": "editor"})
    assert resp.status_code == 401


def test_create_and_fetch_invitation(client, owner_auth_headers, db_session):
    resp = client.post(
        "/api/v1/invitations",
        headers=owner_auth_headers,
        json={"email": "friend@example.com", "role": "traveler"},
    )
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["token"]
    assert data["link"]
    assert data["role"] == "traveler"

    # Fetch by token
    det = client.get(f"/api/v1/invitations/{data['token']}")
    assert det.status_code == 200
    assert det.get_json()["email"] == "friend@example.com"

    # Unknown token -> 404 (do not reveal existence)
    assert client.get("/api/v1/invitations/nope").status_code == 404


def test_invalid_role_rejected(client, owner_auth_headers):
    resp = client.post(
        "/api/v1/invitations",
        headers=owner_auth_headers,
        json={"email": "x@y.com", "role": "wizard"},
    )
    assert resp.status_code == 400
