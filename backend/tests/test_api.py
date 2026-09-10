import urllib.error
import uuid
from datetime import datetime, timedelta, timezone

import app as app_module


def auth_headers(client):
    account = f"test-{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/api/v1/auth/register",
        json={"account": account, "password": "password123", "nickname": "测试用户"},
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_auth_course_task_and_stats(client):
    headers = auth_headers(client)

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["account"].startswith("test-")

    course = client.post("/api/v1/courses", headers=headers, json={"name": "测试课程", "semester": "2026 秋"})
    assert course.status_code == 201
    course_id = course.json()["id"]

    task = client.post(
        "/api/v1/tasks",
        headers=headers,
        json={"title": "完成测试任务", "course_id": course_id, "priority": "high"},
    )
    assert task.status_code == 201
    task_id = task.json()["id"]

    tasks = client.get("/api/v1/tasks", headers=headers)
    assert tasks.status_code == 200
    assert len(tasks.json()) == 1

    updated = client.patch(f"/api/v1/tasks/{task_id}", headers=headers, json={"status": "done"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"

    overview = client.get("/api/v1/stats/overview", headers=headers)
    assert overview.status_code == 200
    assert overview.json()["completion_rate"] == 1.0

    upcoming = client.get("/api/v1/tasks/upcoming", headers=headers)
    assert upcoming.status_code == 200
    assert upcoming.json() == []


def test_duplicate_registration_is_rejected(client):
    account = f"duplicate-{uuid.uuid4().hex[:8]}"
    payload = {"account": account, "password": "password123", "nickname": "测试用户"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_invalid_course_name_is_rejected(client):
    headers = auth_headers(client)
    empty_name = client.post("/api/v1/courses", headers=headers, json={"name": ""})
    long_name = client.post("/api/v1/courses", headers=headers, json={"name": "课" * 101})
    assert empty_name.status_code == 422
    assert long_name.status_code == 422


def test_upcoming_tasks_returns_due_items(client):
    headers = auth_headers(client)
    course = client.post("/api/v1/courses", headers=headers, json={"name": "提醒测试课"})
    course_id = course.json()["id"]
    due_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    task = client.post("/api/v1/tasks", headers=headers, json={"title": "明日任务", "course_id": course_id, "due_at": due_at})
    assert task.status_code == 201
    upcoming = client.get("/api/v1/tasks/upcoming", headers=headers)
    assert upcoming.status_code == 200
    assert upcoming.json()[0]["title"] == "明日任务"


def test_task_due_at_rejects_invalid_datetime_and_normalizes_date(client):
    headers = auth_headers(client)
    course = client.post("/api/v1/courses", headers=headers, json={"name": "日期校验课"})
    course_id = course.json()["id"]

    invalid = client.post(
        "/api/v1/tasks", headers=headers, json={"title": "非法日期", "course_id": course_id, "due_at": "abc"}
    )
    assert invalid.status_code == 422

    valid = client.post(
        "/api/v1/tasks", headers=headers, json={"title": "日期任务", "course_id": course_id, "due_at": "2026-09-12"}
    )
    assert valid.status_code == 201
    assert valid.json()["due_at"] == "2026-09-12T15:59:59.999999+00:00"

    updated = client.patch(f"/api/v1/tasks/{valid.json()['id']}", headers=headers, json={"due_at": "2026-09-13T08:00:00"})
    assert updated.status_code == 200
    assert updated.json()["due_at"] == "2026-09-13T08:00:00+00:00"


def test_nonexistent_task_returns_not_found(client):
    headers = auth_headers(client)
    assert client.patch("/api/v1/tasks/999999", headers=headers, json={"status": "done"}).status_code == 404
    assert client.delete("/api/v1/tasks/999999", headers=headers).status_code == 404


def test_conversation_persists_messages(client):
    headers = auth_headers(client)
    conversation = client.post("/api/v1/conversations", headers=headers)
    assert conversation.status_code == 201
    conversation_id = conversation.json()["id"]

    message = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers,
        json={"content": "如何安排学习任务？"},
    )
    assert message.status_code == 201
    assert "学习任务" in message.json()["content"]

    messages = client.get(f"/api/v1/conversations/{conversation_id}/messages", headers=headers)
    assert messages.status_code == 200
    assert [item["role"] for item in messages.json()] == ["user", "assistant"]


def test_message_provider_rejects_non_http_base_url(client):
    headers = auth_headers(client)
    conversation = client.post("/api/v1/conversations", headers=headers)
    conversation_id = conversation.json()["id"]
    response = client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers,
        json={
            "content": "测试 API",
            "provider": {"name": "错误配置", "base_url": "ftp://example.com", "model": "demo", "api_key": "not-a-real-key"},
        },
    )
    assert response.status_code == 422


def test_ai_api_key_error_timeout_and_network_failure_are_safe(monkeypatch):
    provider = app_module.ProviderConfig(
        name="测试 API", base_url="https://example.com/v1", model="demo", api_key="fake-key"
    )

    def raise_key_error(*args, **kwargs):
        raise urllib.error.HTTPError("https://example.com", 401, "Unauthorized", {}, None)

    def raise_timeout(*args, **kwargs):
        raise TimeoutError("simulated timeout")

    def raise_network_error(*args, **kwargs):
        raise urllib.error.URLError("simulated network failure")

    for failure in (raise_key_error, raise_timeout, raise_network_error):
        monkeypatch.setattr(app_module.urllib.request, "urlopen", failure)
        assert "AI 服务暂时不可用" in app_module.assistant_reply("测试问题", provider)


def test_custom_provider_is_forwarded_to_compatible_api(monkeypatch):
    captured = {}

    class FakeResponse:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self): return '{"choices":[{"message":{"content":"本地模拟回复"}}]}'.encode("utf-8")

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["authorization"] = request.get_header("Authorization")
        captured["body"] = request.data.decode("utf-8")
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(app_module.urllib.request, "urlopen", fake_urlopen)
    provider = app_module.ProviderConfig(
        name="本地测试 API", base_url="http://127.0.0.1:9999/v1/", model="test-model", api_key="fake-key"
    )
    reply = app_module.assistant_reply("测试转发", provider)

    assert reply == "本地模拟回复"
    assert captured["url"] == "http://127.0.0.1:9999/v1/chat/completions"
    assert captured["authorization"] == "Bearer fake-key"
    assert '"model": "test-model"' in captured["body"]
    assert captured["timeout"] == 25


def test_protected_endpoint_requires_login(client):
    response = client.get("/api/v1/tasks")
    assert response.status_code == 401


def test_material_upload_list_and_delete(client):
    headers = auth_headers(client)
    course = client.post("/api/v1/courses", headers=headers, json={"name": "资料测试课"})
    course_id = course.json()["id"]
    upload = client.post(
        "/api/v1/materials",
        headers=headers,
        data={"course_id": str(course_id), "title": "第一章课件"},
        files={"file": ("chapter-1.txt", b"system design notes", "text/plain")},
    )
    assert upload.status_code == 201
    material_id = upload.json()["id"]
    assert upload.json()["parse_status"] == "queued"

    materials = client.get(f"/api/v1/courses/{course_id}/materials", headers=headers)
    assert materials.status_code == 200
    assert materials.json()[0]["filename"] == "chapter-1.txt"

    deleted = client.delete(f"/api/v1/materials/{material_id}", headers=headers)
    assert deleted.status_code == 204


def test_material_upload_rejects_unsupported_and_oversized_files(client):
    headers = auth_headers(client)
    course = client.post("/api/v1/courses", headers=headers, json={"name": "文件校验课"})
    course_id = course.json()["id"]
    unsupported = client.post(
        "/api/v1/materials", headers=headers, data={"course_id": str(course_id)},
        files={"file": ("notes.exe", b"not allowed", "application/octet-stream")},
    )
    oversized = client.post(
        "/api/v1/materials", headers=headers, data={"course_id": str(course_id)},
        files={"file": ("large.txt", b"x" * (20 * 1024 * 1024 + 1), "text/plain")},
    )
    assert unsupported.status_code == 400
    assert oversized.status_code == 400


def test_material_cannot_be_deleted_by_another_user(client):
    owner_headers = auth_headers(client)
    other_headers = auth_headers(client)
    course = client.post("/api/v1/courses", headers=owner_headers, json={"name": "权限测试课"})
    course_id = course.json()["id"]
    upload = client.post(
        "/api/v1/materials", headers=owner_headers, data={"course_id": str(course_id)},
        files={"file": ("private.txt", b"private", "text/plain")},
    )
    material_id = upload.json()["id"]
    assert client.delete(f"/api/v1/materials/{material_id}", headers=other_headers).status_code == 404
