import uuid


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


def test_protected_endpoint_requires_login(client):
    response = client.get("/api/v1/tasks")
    assert response.status_code == 401
