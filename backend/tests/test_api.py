import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_upload_rejects_non_pdf(client):
    r = client.post("/api/reports", files={"file": ("notes.txt", b"hello", "text/plain")})
    assert r.status_code == 400


def test_upload_review_estimate_flow(client, samples):
    pdf = (samples / "skymeasure_needs_review_oak_st.pdf").read_bytes()
    report = client.post("/api/reports", files={"file": ("oak.pdf", pdf, "application/pdf")},
                         data={"job_name": "Oak St"}).json()
    assert report["job_name"] == "Oak St"
    assert report["verification"]["status"] == "fail"

    blocked = client.post(f"/api/reports/{report['id']}/estimates", json={})
    assert blocked.status_code == 409

    fixed = client.patch(f"/api/reports/{report['id']}/measurements", json={
        "values": {"eaves_ft": 144},
        "pitch_breakdown": [{"pitch": 5, "area_sqft": 1800}, {"pitch": 3, "area_sqft": 400}],
    }).json()
    eaves = next(m for m in fixed["measurements"] if m["key"] == "eaves_ft")
    assert eaves["source"] == "manual" and eaves["value"] == 144
    assert fixed["verification"]["can_estimate"]

    est = client.post(f"/api/reports/{report['id']}/estimates", json={"assembly_code": "ARCH-STD"}).json()
    shingles = est["items"][0]
    assert shingles["ref_code"] == "SHG-ARCH" and shingles["qty"] == 73  # 2200 * 1.10 / 33.333 = 72.6 -> 73

    # Manual override survives a waste change; reset restores the formula quantity.
    est = client.patch(f"/api/line-items/{shingles['id']}", json={"qty": 80}).json()
    est = client.patch(f"/api/estimates/{est['id']}", json={"waste_pct": 15}).json()
    assert est["items"][0]["qty"] == 80 and est["items"][0]["calc_qty"] == 76  # 2200 * 1.15 / 33.333 = 75.9 -> 76
    est = client.patch(f"/api/line-items/{shingles['id']}", json={"reset": True}).json()
    assert est["items"][0]["qty"] == 76 and not est["items"][0]["overridden"]


def test_price_book_update_applies_to_new_estimates(client):
    client.patch("/api/pricebook/materials/SHG-ARCH", json={"price": 50})
    book = client.get("/api/pricebook").json()
    assert next(m for m in book["materials"] if m["sku"] == "SHG-ARCH")["price"] == 50
    client.patch("/api/pricebook/materials/SHG-ARCH", json={"price": 42.5})
