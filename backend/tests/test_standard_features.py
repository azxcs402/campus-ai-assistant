import uuid
from datetime import datetime, timedelta, timezone

import app as app_module
from offline_eval import CASES, score_output


def register(client, prefix="user"):
    account = f"{prefix}-{uuid.uuid4().hex[:8]}"
    response = client.post(
        "/api/v1/auth/register",
        json={"account": account, "password": "password123", "nickname": prefix},
    )
    assert response.status_code == 201
    return response.json(), {"Authorization": f"Bearer {response.json()['token']}"}


def create_course(client, headers, name="系统设计"):
    response = client.post("/api/v1/courses", headers=headers, json={"name": name, "semester": "2026 秋"})
    assert response.status_code == 201
    return response.json()


def test_task_can_edit_all_fields_and_tracks_completion(client):
    _, headers = register(client)
    first = create_course(client, headers, "课程 A")
    second = create_course(client, headers, "课程 B")
    task = client.post("/api/v1/tasks", headers=headers, json={"title": "旧标题", "course_id": first["id"]}).json()

    updated = client.patch(
        f"/api/v1/tasks/{task['id']}",
        headers=headers,
        json={"title": "新标题", "course_id": second["id"], "due_at": "2026-09-20", "priority": "high", "note": "完成实验", "status": "done"},
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == "新标题"
    assert updated.json()["course_id"] == second["id"]
    assert updated.json()["note"] == "完成实验"
    assert updated.json()["completed_at"] is not None

    restored = client.patch(f"/api/v1/tasks/{task['id']}", headers=headers, json={"status": "todo"})
    assert restored.json()["completed_at"] is None


def test_course_details_update_and_safe_delete(client):
    _, headers = register(client)
    course = create_course(client, headers)
    detail = client.get(f"/api/v1/courses/{course['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["task_count"] == 0

    renamed = client.patch(f"/api/v1/courses/{course['id']}", headers=headers, json={"name": "软件工程"})
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "软件工程"

    client.post("/api/v1/tasks", headers=headers, json={"title": "关联任务", "course_id": course["id"]})
    assert client.delete(f"/api/v1/courses/{course['id']}", headers=headers).status_code == 409

    empty = create_course(client, headers, "空课程")
    assert client.delete(f"/api/v1/courses/{empty['id']}", headers=headers).status_code == 204


def test_admin_role_management_and_cross_user_permissions(client, monkeypatch):
    admin_account = f"admin-{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv("ADMIN_ACCOUNT", admin_account)
    admin_response = client.post(
        "/api/v1/auth/register",
        json={"account": admin_account, "password": "password123", "nickname": "管理员"},
    )
    admin_headers = {"Authorization": f"Bearer {admin_response.json()['token']}"}
    member, member_headers = register(client, "member")
    outsider, outsider_headers = register(client, "outsider")
    course = create_course(client, member_headers, "权限课程")
    task = client.post("/api/v1/tasks", headers=member_headers, json={"title": "私有任务", "course_id": course["id"]}).json()

    assert client.get("/api/v1/users", headers=member_headers).status_code == 403
    changed = client.patch(f"/api/v1/users/{outsider['user']['id']}/role", headers=admin_headers, json={"role": "teacher"})
    assert changed.status_code == 200
    assert changed.json()["role"] == "teacher"
    assert client.get(f"/api/v1/courses/{course['id']}", headers=outsider_headers).status_code == 403
    assert client.patch(f"/api/v1/tasks/{task['id']}", headers=outsider_headers, json={"title": "越权"}).status_code == 404
    assert client.patch(f"/api/v1/tasks/{task['id']}", headers=admin_headers, json={"title": "管理员修正"}).status_code == 200


def test_course_date_and_overdue_statistics(client):
    _, headers = register(client)
    first = create_course(client, headers, "统计 A")
    second = create_course(client, headers, "统计 B")
    past = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    client.post("/api/v1/tasks", headers=headers, json={"title": "逾期", "course_id": first["id"], "due_at": past})
    done = client.post("/api/v1/tasks", headers=headers, json={"title": "完成", "course_id": first["id"], "due_at": future}).json()
    client.patch(f"/api/v1/tasks/{done['id']}", headers=headers, json={"status": "done"})
    client.post("/api/v1/tasks", headers=headers, json={"title": "其他课程", "course_id": second["id"], "due_at": future})

    overview = client.get(f"/api/v1/stats/overview?course_id={first['id']}", headers=headers)
    assert overview.status_code == 200
    assert overview.json()["total"] == 2
    assert overview.json()["completed"] == 1
    assert overview.json()["overdue"] == 1
    assert overview.json()["completion_rate"] == 0.5

    grouped = client.get("/api/v1/stats/courses", headers=headers)
    assert grouped.status_code == 200
    by_name = {row["course_name"]: row for row in grouped.json()}
    assert by_name["统计 A"]["overdue"] == 1
    assert by_name["统计 B"]["total"] == 1
    today = datetime.now(timezone.utc).date().isoformat()
    filtered = client.get(f"/api/v1/stats/overview?from={today}&to={today}", headers=headers)
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 0
    assert client.get("/api/v1/stats/overview?from=not-a-date", headers=headers).status_code == 422
    reversed_range = client.get("/api/v1/stats/overview?from=2026-09-12&to=2026-09-10", headers=headers)
    assert reversed_range.status_code == 422
    assert reversed_range.json()["detail"] == "开始日期不能晚于结束日期"


def test_conversation_is_private_but_admin_can_review(client, monkeypatch):
    owner, owner_headers = register(client, "chat-owner")
    _, outsider_headers = register(client, "chat-outsider")
    conversation = client.post("/api/v1/conversations", headers=owner_headers).json()
    assert client.get(f"/api/v1/conversations/{conversation['id']}/messages", headers=outsider_headers).status_code == 404

    admin_account = f"reviewer-{uuid.uuid4().hex[:8]}"
    monkeypatch.setenv("ADMIN_ACCOUNT", admin_account)
    admin = client.post(
        "/api/v1/auth/register",
        json={"account": admin_account, "password": "password123", "nickname": "审核员"},
    ).json()
    admin_headers = {"Authorization": f"Bearer {admin['token']}"}
    assert client.get(f"/api/v1/conversations/{conversation['id']}/messages", headers=admin_headers).status_code == 200


def test_offline_ai_evaluation_set_uses_mock_provider_and_persists(client, monkeypatch):
    assert len(CASES) >= 5
    outputs = {
        "E-01": "第一步明确报告要求；第二步拆分步骤；下一步开始报告提纲。",
        "E-02": "第1天复习概念，第2天练习，第3天复盘。",
        "E-03": "首先检查截止时间，再按影响确定优先级。",
        "E-04": "先比较两门课程所需时间，再分配课程时段。",
        "E-05": "首先检查 API Key 和地址，然后重试。",
        "E-06": "先检查资料范围，下一步列出行动清单。",
    }
    by_prompt = {case.prompt: outputs[case.case_id] for case in CASES}
    monkeypatch.setattr(app_module, "assistant_reply", lambda content, provider=None: by_prompt[content])
    _, headers = register(client, "eval")
    conversation = client.post("/api/v1/conversations", headers=headers).json()

    for case in CASES:
        response = client.post(
            f"/api/v1/conversations/{conversation['id']}/messages",
            headers=headers,
            json={"content": case.prompt},
        )
        assert response.status_code == 201
        score = score_output(case, response.json()["content"])
        assert score["not_empty"] is True
        assert score["required_terms"] == score["required_terms_total"]
        assert score["has_action_structure"] is True
        assert score["no_service_error"] is True

    messages = client.get(f"/api/v1/conversations/{conversation['id']}/messages", headers=headers).json()
    assert len(messages) == len(CASES) * 2
