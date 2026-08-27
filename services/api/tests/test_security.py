def test_security_headers_present(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    headers = resp.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert "default-src 'none'" in (headers.get("Content-Security-Policy") or "")
    assert headers.get("Referrer-Policy") == "no-referrer"


def test_provider_status_shape(client):
    resp = client.get("/api/v1/provider-status")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "providers" in data
    assert data["providers"]["ai"] is None  # AI_PROVIDER=none
    assert "google_maps" in data["providers"]
