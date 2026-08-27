from app.services.export import collect_itinerary_data, export_csv, export_xlsx, export_pdf, export_docx


def test_csv_export_deterministic(client, make_user, db_session, auth_header):
    owner = make_user("csv-owner@example.com")
    db_session.commit()
    from app.seed.tennessee import seed_tennessee
    trip = seed_tennessee(db_session, owner)
    db_session.commit()

    resp = client.get(f"/api/v1/trips/{trip.id}/export?format=csv", headers=auth_header(owner))
    assert resp.status_code == 200
    assert resp.content_type.startswith("text/csv")
    body = resp.data.decode("utf-8")
    assert "Guill-a-Gogo Itinerary Export" in body
    assert "Redding, California" in body
    assert "estimate" in body or "confirmed" in body


def test_xlsx_export_valid_workbook(client, make_user, db_session, auth_header):
    owner = make_user("xlsx-owner@example.com")
    db_session.commit()
    from app.seed.tennessee import seed_tennessee
    trip = seed_tennessee(db_session, owner)
    db_session.commit()

    resp = client.get(f"/api/v1/trips/{trip.id}/export?format=xlsx", headers=auth_header(owner))
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.content_type
    # XLSX is a ZIP archive; verify magic bytes.
    assert resp.data[:2] == b"PK"


def test_pdf_export_valid(client, make_user, db_session, auth_header):
    owner = make_user("pdf-owner@example.com")
    db_session.commit()
    from app.seed.tennessee import seed_tennessee
    trip = seed_tennessee(db_session, owner)
    db_session.commit()

    resp = client.get(f"/api/v1/trips/{trip.id}/export?format=pdf", headers=auth_header(owner))
    assert resp.status_code == 200
    assert resp.content_type == "application/pdf"
    assert resp.data[:4] == b"%PDF"


def test_docx_export_valid(client, make_user, db_session, auth_header):
    owner = make_user("docx-owner@example.com")
    db_session.commit()
    from app.seed.tennessee import seed_tennessee
    trip = seed_tennessee(db_session, owner)
    db_session.commit()

    resp = client.get(f"/api/v1/trips/{trip.id}/export?format=docx", headers=auth_header(owner))
    assert resp.status_code == 200
    assert "wordprocessingml" in resp.content_type
    assert resp.data[:2] == b"PK"


def test_export_unsupported_format(client, make_user, db_session, auth_header):
    owner = make_user("fmt-owner@example.com")
    db_session.commit()
    from app.seed.tennessee import seed_tennessee
    trip = seed_tennessee(db_session, owner)
    db_session.commit()
    resp = client.get(f"/api/v1/trips/{trip.id}/export?format=odt", headers=auth_header(owner))
    assert resp.status_code == 400


def test_drive_export_not_configured(client, make_user, db_session, auth_header):
    owner = make_user("drive-owner@example.com")
    db_session.commit()
    from app.seed.tennessee import seed_tennessee
    trip = seed_tennessee(db_session, owner)
    db_session.commit()
    resp = client.post(f"/api/v1/trips/{trip.id}/export/drive", headers=auth_header(owner))
    assert resp.status_code == 503
