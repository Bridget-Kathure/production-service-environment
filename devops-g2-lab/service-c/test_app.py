import os

os.environ.setdefault("SERVICE_NAME", "c")
os.environ.setdefault("GIT_SHA", "test-sha")

from app import app  # noqa: E402


def client():
    return app.test_client()


def test_health_returns_ok():
    resp = client().get("/")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["service"] == "c"
    assert body["status"] == "ok"


def test_health_reports_git_sha():
    resp = client().get("/")
    body = resp.get_json()
    assert body["sha"] == "test-sha"
