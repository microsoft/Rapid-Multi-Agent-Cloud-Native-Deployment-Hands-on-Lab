import uuid

from fastapi.testclient import TestClient

from backend.app.main import OUTPUT_DIR, app


def test_download_is_png_attachment() -> None:
    image_id = uuid.uuid4().hex
    image_path = OUTPUT_DIR / f"{image_id}.png"
    image_path.write_bytes(b"\x89PNG\r\n\x1a\nfake-png")
    try:
        response = TestClient(app).get(f"/api/downloads/moodframe-{image_id}.png")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["content-disposition"].startswith("attachment;")
        assert f"moodframe-{image_id}.png" in response.headers["content-disposition"]
        assert response.content.startswith(b"\x89PNG\r\n\x1a\n")
    finally:
        image_path.unlink(missing_ok=True)
