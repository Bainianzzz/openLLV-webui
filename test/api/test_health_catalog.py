def test_health_live_does_not_require_dependencies(client):
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_ready_reports_fixed_worker_slots(client):
    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "workers": {
            "enhancement": "idle",
            "training": "idle",
            "dataset_download": "idle",
        },
    }


def test_catalog_combines_openllv_metadata_with_explicit_forms(client):
    response = client.get("/api/v1/catalog")

    assert response.status_code == 200
    body = response.json()
    assert body["algorithms"] == [{"name": "Gamma", "aliases": ["gamma"]}]
    assert body["models"] == [{"name": "ZeroDCE", "aliases": ["zero_dce"]}]
    assert body["devices"][0:3] == ["auto", "cpu", "mps"]
    assert body["forms"]["enhancement"]["traditional_params"]["gamma"]["default"] == 0.6
