PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
    b"\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xcf\xc0\x00\x00\x03\x01\x01\x00\xc9\xfe\x92\xef"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_upload_single_image_creates_file_artifact(client):
    response = client.post(
        "/api/v1/artifacts/images",
        files=[("files", ("input.png", PNG, "image/png"))],
    )

    assert response.status_code == 201
    body = response.json()
    assert body["kind"] == "image"
    assert body["path_type"] == "file"
    assert body["display_name"] == "input.png"
    assert body["content_url"].endswith(f"/{body['id']}/content")
    assert client.get(body["content_url"]).content == PNG


def test_upload_multiple_images_creates_one_directory_artifact(client):
    response = client.post(
        "/api/v1/artifacts/images",
        files=[
            ("files", ("one.png", PNG, "image/png")),
            ("files", ("two.png", PNG, "image/png")),
        ],
    )

    assert response.status_code == 201
    body = response.json()
    assert body["path_type"] == "directory"
    artifact_path = client.app.state.storage.resolve("uploads", body["id"])
    assert not (artifact_path / ".manifest.json").exists()
    listing = client.get(body["content_url"])
    assert listing.status_code == 200
    assert {item["display_name"] for item in listing.json()["items"]} == {"one.png", "two.png"}
