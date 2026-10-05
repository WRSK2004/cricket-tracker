# API tests. Firebase is never contacted: the signed-in user is faked by
# overriding get_current_user, and storage is replaced with a fake bucket.

import pytest
from fastapi.testclient import TestClient

import app as app_module
from auth import get_current_user

VALID_HEALTH = {"age": 25, "gender": "male", "height": 180, "weight": 75, "activity": "moderately active"}


class FakeBlob:
    def __init__(self, path, store):
        self.path, self.store = path, store

    def generate_signed_url(self, **kwargs):
        return f"https://signed.example/{self.path}"

    def exists(self):
        return self.path in self.store

    def delete(self):
        self.store.discard(self.path)


class FakeBucket:
    def __init__(self):
        self.store = set()

    def blob(self, path):
        return FakeBlob(path, self.store)


@pytest.fixture
def bucket(monkeypatch):
    fake = FakeBucket()
    monkeypatch.setattr(app_module, "get_bucket", lambda: fake)
    return fake


@pytest.fixture
def client():
    app_module.app.dependency_overrides[get_current_user] = lambda: "user-a"
    yield TestClient(app_module.app)
    app_module.app.dependency_overrides.clear()


@pytest.fixture
def anonymous_client():
    return TestClient(app_module.app)


def test_requests_without_sign_in_are_rejected(anonymous_client):
    response = anonymous_client.post("/health", json=VALID_HEALTH)
    assert response.status_code == 401
    assert "signed in" in response.json()["error"]


def test_health_returns_metrics(client):
    response = client.post("/health", json=VALID_HEALTH)
    assert response.status_code == 200
    assert response.json()["BMR"] == pytest.approx(1755)


@pytest.mark.parametrize("field,value", [("age", 0), ("height", -5), ("weight", 1000), ("gender", "x")])
def test_health_rejects_bad_input(client, field, value):
    response = client.post("/health", json=dict(VALID_HEALTH, **{field: value}))
    assert response.status_code == 422
    assert "error" in response.json()


def test_media_urls_for_own_files(client, bucket):
    path = "users/user-a/analyses/abc/video.mp4"
    response = client.post("/media/urls", json={"paths": [path]})
    assert response.status_code == 200
    assert response.json()["urls"][path].startswith("https://signed.example/")


@pytest.mark.parametrize("path", ["users/user-b/analyses/abc/video.mp4", "users/user-a/../user-b/x.mp4", "other.mp4"])
def test_media_urls_refuses_other_users_files(client, bucket, path):
    response = client.post("/media/urls", json={"paths": [path]})
    assert response.status_code == 403


def test_media_delete_only_own_files(client, bucket):
    bucket.store.update({"users/user-a/analyses/1/video.mp4", "users/user-b/analyses/2/video.mp4"})
    assert client.post("/media/delete", json={"paths": ["users/user-b/analyses/2/video.mp4"]}).status_code == 403
    assert client.post("/media/delete", json={"paths": ["users/user-a/analyses/1/video.mp4"]}).status_code == 200
    assert bucket.store == {"users/user-b/analyses/2/video.mp4"}


def test_analyse_rejects_non_video(client):
    response = client.post(
        "/analyse", files={"video": ("notes.txt", b"hello", "text/plain")}, data={"batting_hand": "left"}
    )
    assert response.status_code == 415


def test_analyse_requires_batting_hand(client):
    response = client.post("/analyse", files={"video": ("clip.mp4", b"x", "video/mp4")}, data={"batting_hand": "none"})
    assert response.status_code == 422


def test_analyse_rejects_oversized_upload(client, monkeypatch):
    monkeypatch.setattr(app_module, "UPLOAD_CHUNK_BYTES", 10)
    settings = app_module.get_settings()
    monkeypatch.setattr(app_module, "get_settings", lambda: type(settings)(**{**settings.__dict__, "max_upload_mb": 0}))
    response = client.post(
        "/analyse", files={"video": ("clip.mp4", b"x" * 100, "video/mp4")}, data={"batting_hand": "left"}
    )
    assert response.status_code == 413
