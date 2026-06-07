"""
Day 1 Tests — Scaffold, Auth, Image Upload & Storage

Run:  pytest backend/tests/test_day1_auth_upload.py -v

Covers:
  - GET  /health
  - POST /auth/signup
  - POST /auth/signin
  - POST /auth/signout
  - backend/services/storage.py  (file type, size, upload path)
"""
from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

from backend.main import app
from backend.tests.conftest import IMAGE_URL, make_upload_file


# ── Scaffold ──────────────────────────────────────────────────────────────────

async def test_health_returns_ok():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_unknown_route_returns_404():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.get("/does-not-exist")
    assert r.status_code == 404


# ── Signup ────────────────────────────────────────────────────────────────────

async def test_signup_success():
    mock_user = MagicMock()
    mock_user.id = "new-user-id"
    mock_resp = MagicMock()
    mock_resp.user = mock_user

    with patch("backend.routes.auth.supabase") as sb:
        sb.auth.sign_up.return_value = mock_resp
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.post("/auth/signup", json={
                "email": "new@example.com",
                "password": "strongpass99",
                "full_name": "New User",
            })

    assert r.status_code == 200
    assert r.json()["user_id"] == "new-user-id"
    assert "message" in r.json()


async def test_signup_missing_password_is_422():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.post("/auth/signup", json={
            "email": "user@example.com",
            "full_name": "No Pass",
        })
    assert r.status_code == 422


async def test_signup_missing_full_name_is_422():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.post("/auth/signup", json={
            "email": "user@example.com",
            "password": "pass123",
        })
    assert r.status_code == 422


async def test_signup_invalid_email_format_is_422():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.post("/auth/signup", json={
            "email": "not-an-email",
            "password": "pass123",
            "full_name": "Bad Email",
        })
    assert r.status_code == 422


async def test_signup_supabase_error_returns_400():
    with patch("backend.routes.auth.supabase") as sb:
        sb.auth.sign_up.side_effect = Exception("Email already registered")
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.post("/auth/signup", json={
                "email": "dup@example.com",
                "password": "pass123",
                "full_name": "Dup User",
            })
    assert r.status_code == 400


async def test_signup_empty_body_is_422():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.post("/auth/signup", json={})
    assert r.status_code == 422


# ── Signin ────────────────────────────────────────────────────────────────────

async def test_signin_success():
    mock_session = MagicMock()
    mock_session.access_token = "access-abc"
    mock_session.refresh_token = "refresh-xyz"
    mock_user = MagicMock()
    mock_user.id = "user-123"
    mock_resp = MagicMock()
    mock_resp.session = mock_session
    mock_resp.user = mock_user

    with patch("backend.routes.auth.supabase") as sb:
        sb.auth.sign_in_with_password.return_value = mock_resp
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.post("/auth/signin", json={
                "email": "user@example.com",
                "password": "correctpass",
            })

    assert r.status_code == 200
    data = r.json()
    assert data["access_token"] == "access-abc"
    assert data["refresh_token"] == "refresh-xyz"
    assert data["user_id"] == "user-123"


async def test_signin_wrong_password_returns_401():
    with patch("backend.routes.auth.supabase") as sb:
        sb.auth.sign_in_with_password.side_effect = Exception("Invalid credentials")
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.post("/auth/signin", json={
                "email": "user@example.com",
                "password": "wrong",
            })
    assert r.status_code == 401
    assert "Invalid credentials" in r.json()["detail"]


async def test_signin_missing_email_is_422():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.post("/auth/signin", json={"password": "pass"})
    assert r.status_code == 422


async def test_signin_missing_password_is_422():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.post("/auth/signin", json={"email": "user@example.com"})
    assert r.status_code == 422


# ── Signout ───────────────────────────────────────────────────────────────────

async def test_signout_success():
    with patch("backend.routes.auth.supabase") as sb:
        sb.auth.sign_out.return_value = None
        async with AsyncClient(app=app, base_url="http://test") as client:
            r = await client.post(
                "/auth/signout",
                headers={"Authorization": "Bearer some-token"},
            )
    assert r.status_code == 200
    assert r.json()["message"] == "Signed out"


async def test_signout_missing_auth_header_is_422():
    async with AsyncClient(app=app, base_url="http://test") as client:
        r = await client.post("/auth/signout")
    assert r.status_code == 422


# ── Storage: file validation (unit tests) ────────────────────────────────────

async def test_storage_rejects_pdf():
    from backend.services.storage import upload_image

    file = make_upload_file("doc.pdf", b"fake-pdf", "application/pdf")
    with pytest.raises(Exception) as exc:
        await upload_image(file, "user-123")
    assert exc.value.status_code == 400
    assert "allowed" in exc.value.detail.lower() or "JPEG" in exc.value.detail


async def test_storage_rejects_gif():
    from backend.services.storage import upload_image

    file = make_upload_file("anim.gif", b"GIF89a", "image/gif")
    with pytest.raises(Exception) as exc:
        await upload_image(file, "user-123")
    assert exc.value.status_code == 400


async def test_storage_rejects_oversized_image():
    from backend.services.storage import MAX_SIZE_BYTES, upload_image

    big = b"x" * (MAX_SIZE_BYTES + 1)
    file = make_upload_file("big.jpg", big, "image/jpeg")
    with pytest.raises(Exception) as exc:
        await upload_image(file, "user-123")
    assert exc.value.status_code == 400
    assert "10 MB" in exc.value.detail


async def test_storage_accepts_jpeg_and_returns_url():
    from backend.services.storage import upload_image

    file = make_upload_file("photo.jpg", b"fake-jpeg-bytes", "image/jpeg")
    with patch("backend.services.storage.supabase") as sb:
        sb.storage.from_.return_value.upload.return_value = MagicMock()
        sb.storage.from_.return_value.get_public_url.return_value = IMAGE_URL
        result = await upload_image(file, "user-123")

    assert result == IMAGE_URL


async def test_storage_accepts_png():
    from backend.services.storage import upload_image

    file = make_upload_file("img.png", b"fake-png-bytes", "image/png")
    with patch("backend.services.storage.supabase") as sb:
        sb.storage.from_.return_value.upload.return_value = MagicMock()
        sb.storage.from_.return_value.get_public_url.return_value = IMAGE_URL
        result = await upload_image(file, "user-123")

    assert result == IMAGE_URL


async def test_storage_accepts_webp():
    from backend.services.storage import upload_image

    file = make_upload_file("img.webp", b"fake-webp-bytes", "image/webp")
    with patch("backend.services.storage.supabase") as sb:
        sb.storage.from_.return_value.upload.return_value = MagicMock()
        sb.storage.from_.return_value.get_public_url.return_value = IMAGE_URL
        result = await upload_image(file, "user-123")

    assert result == IMAGE_URL


async def test_storage_path_includes_user_id():
    from backend.services.storage import upload_image

    file = make_upload_file("photo.jpg", b"bytes", "image/jpeg")
    captured_path = {}

    with patch("backend.services.storage.supabase") as sb:
        def capture_upload(path, **kwargs):
            captured_path["path"] = path
            return MagicMock()

        sb.storage.from_.return_value.upload.side_effect = lambda path, file, file_options: capture_upload(path)
        sb.storage.from_.return_value.get_public_url.return_value = IMAGE_URL
        await upload_image(file, "user-abc-123")

    assert "user-abc-123" in captured_path.get("path", "")
