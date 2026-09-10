from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
import json
import urllib.error
import urllib.request
import uuid
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator


ROOT = Path(__file__).resolve().parents[1]


def load_local_env() -> None:
    env_path = ROOT / ".env"
    if not env_path.is_file():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_local_env()
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(exist_ok=True)
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)
DB_PATH = Path(os.getenv("DATABASE_PATH", str(DATA_DIR / "app.db")))
TOKEN_SECRET = os.getenv("TOKEN_SECRET", "dev-only-change-me")
CAMPUS_TIMEZONE = timezone(timedelta(hours=8))

app = FastAPI(title="Campus AI Assistant API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500", "http://127.0.0.1:8000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
bearer = HTTPBearer(auto_error=False)


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db() -> None:
    with db() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                nickname TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'student',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                semester TEXT,
                owner_id INTEGER NOT NULL REFERENCES users(id),
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS course_members (
                course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                PRIMARY KEY(course_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                created_by INTEGER NOT NULL REFERENCES users(id),
                due_at TEXT,
                priority TEXT NOT NULL DEFAULT 'medium',
                note TEXT,
                status TEXT NOT NULL DEFAULT 'todo',
                completed_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                uploaded_by INTEGER NOT NULL REFERENCES users(id),
                filename TEXT NOT NULL,
                title TEXT,
                file_path TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                parse_status TEXT NOT NULL DEFAULT 'queued',
                parse_error TEXT,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS conversations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(tasks)").fetchall()}
        if "completed_at" not in columns:
            connection.execute("ALTER TABLE tasks ADD COLUMN completed_at TEXT")
        admin_account = os.getenv("ADMIN_ACCOUNT", "").strip()
        if admin_account:
            connection.execute("UPDATE users SET role = 'admin' WHERE account = ?", (admin_account,))


@app.on_event("startup")
def startup() -> None:
    init_db()


def password_hash(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"{salt.hex()}${digest.hex()}"


def password_matches(password: str, stored: str) -> bool:
    salt_hex, digest_hex = stored.split("$", 1)
    candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 120_000)
    return hmac.compare_digest(candidate.hex(), digest_hex)


def token_for(user_id: int) -> str:
    payload = str(user_id)
    signature = hmac.new(TOKEN_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()
    return f"{payload}.{signature}"


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> sqlite3.Row:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="请先登录")
    try:
        user_id, signature = credentials.credentials.split(".", 1)
        expected = hmac.new(TOKEN_SECRET.encode(), user_id.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            raise ValueError
        user_id = int(user_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=401, detail="登录状态无效")
    with db() as connection:
        user = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def public_user(user: sqlite3.Row) -> dict[str, Any]:
    return {"id": user["id"], "account": user["account"], "nickname": user["nickname"], "role": user["role"]}


class RegisterIn(BaseModel):
    account: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    nickname: str = Field(min_length=1, max_length=50)


class LoginIn(BaseModel):
    account: str
    password: str


class CourseIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    semester: str | None = Field(default=None, max_length=30)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("课程名称不能为空")
        return value.strip()


class CoursePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    semester: str | None = Field(default=None, max_length=30)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("课程名称不能为空")
        return value.strip() if value is not None else None


class RolePatch(BaseModel):
    role: str = Field(pattern="^(student|teacher|admin)$")


def normalize_due_at(value: str | None) -> str | None:
    if value is None:
        return None
    try:
        parsed = datetime.combine(date.fromisoformat(value), time.max, tzinfo=CAMPUS_TIMEZONE) if len(value) == 10 else datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("due_at 必须是 ISO 8601 日期或时间") from error
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat()


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    course_id: int
    due_at: str | None = None
    priority: str = Field(default="medium", pattern="^(low|medium|high)$")
    note: str | None = Field(default=None, max_length=1000)

    @field_validator("due_at")
    @classmethod
    def validate_due_at(cls, value: str | None) -> str | None:
        return normalize_due_at(value)


class TaskPatch(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    course_id: int | None = None
    due_at: str | None = None
    priority: str | None = Field(default=None, pattern="^(low|medium|high)$")
    note: str | None = Field(default=None, max_length=1000)
    status: str | None = Field(default=None, pattern="^(todo|doing|done)$")

    @field_validator("due_at")
    @classmethod
    def validate_due_at(cls, value: str | None) -> str | None:
        return normalize_due_at(value)


class ProviderConfig(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    base_url: str = Field(min_length=1, max_length=300)
    model: str = Field(min_length=1, max_length=120)
    api_key: str = Field(min_length=1, max_length=500)

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, value: str) -> str:
        normalized = value.strip().rstrip("/")
        if not normalized.startswith(("http://", "https://")):
            raise ValueError("Base URL 必须以 http:// 或 https:// 开头")
        return normalized


class MessageIn(BaseModel):
    content: str = Field(min_length=1, max_length=4000)
    provider: ProviderConfig | None = None


@app.get("/api/v1/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/auth/register", status_code=201)
def register(payload: RegisterIn) -> dict[str, Any]:
    role = "admin" if payload.account == os.getenv("ADMIN_ACCOUNT", "").strip() else "student"
    try:
        with db() as connection:
            cursor = connection.execute(
                "INSERT INTO users(account, password_hash, nickname, role, created_at) VALUES (?, ?, ?, ?, ?)",
                (payload.account, password_hash(payload.password), payload.nickname, role, now()),
            )
            user = connection.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="账号已存在")
    return {"token": token_for(user["id"]), "user": public_user(user)}


@app.post("/api/v1/auth/login")
def login(payload: LoginIn) -> dict[str, Any]:
    with db() as connection:
        user = connection.execute("SELECT * FROM users WHERE account = ?", (payload.account,)).fetchone()
    if not user or not password_matches(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="账号或密码错误")
    return {"token": token_for(user["id"]), "user": public_user(user)}


@app.get("/api/v1/auth/me")
def me(user: sqlite3.Row = Depends(current_user)) -> dict[str, Any]:
    return public_user(user)


@app.get("/api/v1/users")
def list_users(user: sqlite3.Row = Depends(current_user)) -> list[dict[str, Any]]:
    require_admin(user)
    with db() as connection:
        rows = connection.execute("SELECT * FROM users ORDER BY created_at").fetchall()
    return [public_user(row) for row in rows]


@app.patch("/api/v1/users/{user_id}/role")
def update_user_role(user_id: int, payload: RolePatch, user: sqlite3.Row = Depends(current_user)) -> dict[str, Any]:
    require_admin(user)
    if user_id == user["id"]:
        raise HTTPException(status_code=400, detail="管理员不能修改自己的角色")
    with db() as connection:
        cursor = connection.execute("UPDATE users SET role = ? WHERE id = ?", (payload.role, user_id))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="用户不存在")
        updated = connection.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return public_user(updated)


@app.get("/api/v1/courses")
def list_courses(user: sqlite3.Row = Depends(current_user)) -> list[dict[str, Any]]:
    with db() as connection:
        if user["role"] == "admin":
            rows = connection.execute(
                """SELECT c.*, COUNT(DISTINCT t.id) AS task_count
                   FROM courses c LEFT JOIN tasks t ON t.course_id = c.id
                   GROUP BY c.id ORDER BY c.created_at DESC"""
            ).fetchall()
        else:
            rows = connection.execute(
                """SELECT c.*, COUNT(DISTINCT t.id) AS task_count
                   FROM courses c JOIN course_members cm ON cm.course_id = c.id
                   LEFT JOIN tasks t ON t.course_id = c.id AND t.created_by = cm.user_id
                   WHERE cm.user_id = ? GROUP BY c.id ORDER BY c.created_at DESC""",
                (user["id"],),
            ).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/v1/courses", status_code=201)
def create_course(payload: CourseIn, user: sqlite3.Row = Depends(current_user)) -> dict[str, Any]:
    with db() as connection:
        cursor = connection.execute(
            "INSERT INTO courses(name, semester, owner_id, created_at) VALUES (?, ?, ?, ?)",
            (payload.name, payload.semester, user["id"], now()),
        )
        connection.execute("INSERT INTO course_members(course_id, user_id) VALUES (?, ?)", (cursor.lastrowid, user["id"]))
        row = connection.execute("SELECT * FROM courses WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)


def require_course_member(connection: sqlite3.Connection, course_id: int, user: sqlite3.Row) -> None:
    if user["role"] == "admin":
        if not connection.execute("SELECT 1 FROM courses WHERE id = ?", (course_id,)).fetchone():
            raise HTTPException(status_code=404, detail="课程不存在")
        return
    if not connection.execute("SELECT 1 FROM course_members WHERE course_id = ? AND user_id = ?", (course_id, user["id"])).fetchone():
        raise HTTPException(status_code=403, detail="你不是该课程成员")


def require_course_manager(connection: sqlite3.Connection, course_id: int, user: sqlite3.Row) -> sqlite3.Row:
    course = connection.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    if course["owner_id"] != user["id"] and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="仅课程所有者或管理员可执行此操作")
    return course


def require_admin(user: sqlite3.Row) -> None:
    if user["role"] != "admin":
        raise HTTPException(status_code=403, detail="仅管理员可执行此操作")


@app.get("/api/v1/courses/{course_id}")
def course_detail(course_id: int, user: sqlite3.Row = Depends(current_user)) -> dict[str, Any]:
    with db() as connection:
        require_course_member(connection, course_id, user)
        row = connection.execute(
            """SELECT c.*, COUNT(DISTINCT t.id) AS task_count, COUNT(DISTINCT m.id) AS material_count
               FROM courses c LEFT JOIN tasks t ON t.course_id = c.id
               LEFT JOIN materials m ON m.course_id = c.id WHERE c.id = ? GROUP BY c.id""",
            (course_id,),
        ).fetchone()
    return dict(row)


@app.patch("/api/v1/courses/{course_id}")
def update_course(course_id: int, payload: CoursePatch, user: sqlite3.Row = Depends(current_user)) -> dict[str, Any]:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")
    with db() as connection:
        require_course_manager(connection, course_id, user)
        assignments = ", ".join(f"{key} = ?" for key in updates)
        connection.execute(f"UPDATE courses SET {assignments} WHERE id = ?", [*updates.values(), course_id])
        row = connection.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    return dict(row)


@app.delete("/api/v1/courses/{course_id}", status_code=204)
def delete_course(course_id: int, user: sqlite3.Row = Depends(current_user)) -> None:
    with db() as connection:
        require_course_manager(connection, course_id, user)
        related = connection.execute(
            """SELECT (SELECT COUNT(*) FROM tasks WHERE course_id = ?) AS task_count,
                      (SELECT COUNT(*) FROM materials WHERE course_id = ?) AS material_count""",
            (course_id, course_id),
        ).fetchone()
        if related["task_count"] or related["material_count"]:
            raise HTTPException(status_code=409, detail="课程仍有任务或资料，请先清理后再删除")
        connection.execute("DELETE FROM courses WHERE id = ?", (course_id,))


@app.get("/api/v1/tasks")
def list_tasks(
    course_id: int | None = None,
    task_status: str | None = Query(default=None, alias="status"),
    user: sqlite3.Row = Depends(current_user),
) -> list[dict[str, Any]]:
    sql = "SELECT t.*, c.name AS course_name FROM tasks t JOIN courses c ON c.id = t.course_id WHERE 1 = 1"
    params: list[Any] = []
    if user["role"] != "admin":
        sql += " AND t.created_by = ? AND EXISTS (SELECT 1 FROM course_members cm WHERE cm.course_id = t.course_id AND cm.user_id = ?)"
        params.extend([user["id"], user["id"]])
    if course_id:
        sql += " AND t.course_id = ?"
        params.append(course_id)
    if task_status:
        sql += " AND t.status = ?"
        params.append(task_status)
    sql += " ORDER BY CASE WHEN t.status = 'done' THEN 1 ELSE 0 END, t.due_at IS NULL, t.due_at"
    with db() as connection:
        return [dict(row) for row in connection.execute(sql, params).fetchall()]


@app.post("/api/v1/tasks", status_code=201)
def create_task(payload: TaskIn, user: sqlite3.Row = Depends(current_user)) -> dict[str, Any]:
    with db() as connection:
        require_course_member(connection, payload.course_id, user)
        timestamp = now()
        cursor = connection.execute(
            """INSERT INTO tasks(title, course_id, created_by, due_at, priority, note, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (payload.title, payload.course_id, user["id"], payload.due_at, payload.priority, payload.note, timestamp, timestamp),
        )
        row = connection.execute("SELECT * FROM tasks WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)


@app.get("/api/v1/tasks/upcoming")
def upcoming_tasks(user: sqlite3.Row = Depends(current_user)) -> list[dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) + timedelta(days=7)
    with db() as connection:
        sql = """SELECT t.*, c.name AS course_name FROM tasks t JOIN courses c ON c.id = t.course_id
                 WHERE t.status != 'done' AND t.due_at IS NOT NULL"""
        params: list[Any] = []
        if user["role"] != "admin":
            sql += " AND t.created_by = ?"
            params.append(user["id"])
        rows = connection.execute(sql + " ORDER BY t.due_at ASC", params).fetchall()
    result = []
    for row in rows:
        try:
            due = datetime.fromisoformat(row["due_at"].replace("Z", "+00:00"))
        except ValueError:
            continue
        if due <= cutoff:
            item = dict(row)
            item["remaining_hours"] = round((due - datetime.now(timezone.utc)).total_seconds() / 3600, 1)
            item["urgent"] = item["remaining_hours"] <= 24
            result.append(item)
    return result


@app.patch("/api/v1/tasks/{task_id}")
def update_task(task_id: int, payload: TaskPatch, user: sqlite3.Row = Depends(current_user)) -> dict[str, Any]:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="没有需要更新的字段")
    with db() as connection:
        task = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task or (task["created_by"] != user["id"] and user["role"] != "admin"):
            raise HTTPException(status_code=404, detail="任务不存在")
        if "course_id" in updates:
            require_course_member(connection, updates["course_id"], user)
        if updates.get("status") == "done" and task["status"] != "done":
            updates["completed_at"] = now()
        elif updates.get("status") and updates["status"] != "done":
            updates["completed_at"] = None
        updates["updated_at"] = now()
        assignments = ", ".join(f"{key} = ?" for key in updates)
        connection.execute(f"UPDATE tasks SET {assignments} WHERE id = ?", [*updates.values(), task_id])
        row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row)


@app.delete("/api/v1/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, user: sqlite3.Row = Depends(current_user)) -> None:
    with db() as connection:
        if user["role"] == "admin":
            cursor = connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        else:
            cursor = connection.execute("DELETE FROM tasks WHERE id = ? AND created_by = ?", (task_id, user["id"]))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="任务不存在")


ALLOWED_MATERIAL_EXTENSIONS = {".pdf", ".ppt", ".pptx", ".doc", ".docx", ".txt", ".md"}
MAX_MATERIAL_SIZE = 20 * 1024 * 1024


@app.get("/api/v1/courses/{course_id}/materials")
def list_materials(course_id: int, user: sqlite3.Row = Depends(current_user)) -> list[dict[str, Any]]:
    with db() as connection:
        require_course_member(connection, course_id, user)
        rows = connection.execute(
            "SELECT id, course_id, filename, title, file_type, file_size, parse_status, parse_error, created_at FROM materials WHERE course_id = ? ORDER BY created_at DESC",
            (course_id,),
        ).fetchall()
    return [dict(row) for row in rows]


@app.post("/api/v1/materials", status_code=201)
async def upload_material(
    file: UploadFile = File(...),
    course_id: int = Form(...),
    title: str | None = Form(default=None),
    user: sqlite3.Row = Depends(current_user),
) -> dict[str, Any]:
    original_name = Path(file.filename or "").name
    extension = Path(original_name).suffix.lower()
    if not original_name or extension not in ALLOWED_MATERIAL_EXTENSIONS:
        raise HTTPException(status_code=400, detail="仅支持 PDF、PPT、PPTX、DOC、DOCX、TXT 或 MD 文件")

    content = await file.read(MAX_MATERIAL_SIZE + 1)
    if len(content) > MAX_MATERIAL_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 20MB")

    with db() as connection:
        require_course_member(connection, course_id, user)
        stored_name = f"{uuid.uuid4().hex}{extension}"
        target_dir = UPLOAD_DIR / str(course_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / stored_name
        target.write_bytes(content)
        cursor = connection.execute(
            """INSERT INTO materials(course_id, uploaded_by, filename, title, file_path, file_type, file_size, parse_status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, 'queued', ?)""",
            (course_id, user["id"], original_name, title or original_name, str(target.relative_to(DATA_DIR)), extension[1:], len(content), now()),
        )
        row = connection.execute("SELECT id, course_id, filename, title, file_type, file_size, parse_status, parse_error, created_at FROM materials WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)


@app.delete("/api/v1/materials/{material_id}", status_code=204)
def delete_material(material_id: int, user: sqlite3.Row = Depends(current_user)) -> None:
    with db() as connection:
        row = connection.execute(
            """SELECT m.*, c.owner_id FROM materials m JOIN courses c ON c.id = m.course_id
               WHERE m.id = ? AND (m.uploaded_by = ? OR c.owner_id = ? OR ? = 'admin')""",
            (material_id, user["id"], user["id"], user["role"]),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="资料不存在")
        target = DATA_DIR / row["file_path"]
        if target.is_file():
            target.unlink()
        connection.execute("DELETE FROM materials WHERE id = ?", (material_id,))


@app.post("/api/v1/conversations", status_code=201)
def create_conversation(user: sqlite3.Row = Depends(current_user)) -> dict[str, Any]:
    timestamp = now()
    with db() as connection:
        cursor = connection.execute("INSERT INTO conversations(user_id, title, created_at, updated_at) VALUES (?, ?, ?, ?)", (user["id"], "新学习对话", timestamp, timestamp))
        row = connection.execute("SELECT * FROM conversations WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)


@app.get("/api/v1/conversations")
def list_conversations(user: sqlite3.Row = Depends(current_user)) -> list[dict[str, Any]]:
    with db() as connection:
        if user["role"] == "admin":
            rows = connection.execute("SELECT * FROM conversations ORDER BY updated_at DESC").fetchall()
        else:
            rows = connection.execute("SELECT * FROM conversations WHERE user_id = ? ORDER BY updated_at DESC", (user["id"],)).fetchall()
        return [dict(row) for row in rows]


def assistant_reply(content: str, provider: ProviderConfig | None = None) -> str:
    api_key = provider.api_key if provider else os.getenv("LLM_API_KEY")
    if not api_key:
        return f"演示模式：我已收到你的问题“{content}”。配置 LLM_API_KEY 后可接入真实模型。你也可以先把它整理为一个学习任务。"

    base_url = provider.base_url if provider else os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1").rstrip("/")
    model = provider.model if provider else os.getenv("LLM_MODEL", "deepseek-chat")
    request_body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": "你是校园智能学习助手，请用清晰、可靠、简洁的中文回答。"},
            {"role": "user", "content": content},
        ],
        "temperature": 0.3,
    }).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=request_body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return payload["choices"][0]["message"]["content"]
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError):
        return "AI 服务暂时不可用。请稍后重试，或继续使用任务管理功能。"


@app.post("/api/v1/conversations/{conversation_id}/messages", status_code=201)
def send_message(conversation_id: int, payload: MessageIn, user: sqlite3.Row = Depends(current_user)) -> dict[str, Any]:
    with db() as connection:
        conversation = connection.execute(
            "SELECT * FROM conversations WHERE id = ? AND (user_id = ? OR ? = 'admin')",
            (conversation_id, user["id"], user["role"]),
        ).fetchone()
        if not conversation:
            raise HTTPException(status_code=404, detail="会话不存在")
        timestamp = now()
        connection.execute("INSERT INTO messages(conversation_id, role, content, created_at) VALUES (?, 'user', ?, ?)", (conversation_id, payload.content, timestamp))
        reply = assistant_reply(payload.content, payload.provider)
        cursor = connection.execute("INSERT INTO messages(conversation_id, role, content, created_at) VALUES (?, 'assistant', ?, ?)", (conversation_id, reply, now()))
        connection.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now(), conversation_id))
        row = connection.execute("SELECT * FROM messages WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return dict(row)


@app.get("/api/v1/conversations/{conversation_id}/messages")
def list_messages(conversation_id: int, user: sqlite3.Row = Depends(current_user)) -> list[dict[str, Any]]:
    with db() as connection:
        if not connection.execute(
            "SELECT 1 FROM conversations WHERE id = ? AND (user_id = ? OR ? = 'admin')",
            (conversation_id, user["id"], user["role"]),
        ).fetchone():
            raise HTTPException(status_code=404, detail="会话不存在")
        return [dict(row) for row in connection.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at", (conversation_id,)).fetchall()]


def normalize_stats_date(value: str | None, end_of_day: bool = False) -> str | None:
    if value is None:
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError as error:
        raise HTTPException(status_code=422, detail="日期筛选必须使用 YYYY-MM-DD 格式") from error
    boundary = datetime.combine(parsed, time.max if end_of_day else time.min, tzinfo=CAMPUS_TIMEZONE)
    return boundary.astimezone(timezone.utc).isoformat()


def stats_where(user: sqlite3.Row, course_id: int | None, date_from: str | None, date_to: str | None) -> tuple[str, list[Any]]:
    clauses = ["1 = 1"]
    params: list[Any] = []
    if user["role"] != "admin":
        clauses.append("t.created_by = ?")
        params.append(user["id"])
    if course_id is not None:
        clauses.append("t.course_id = ?")
        params.append(course_id)
    if date_from:
        clauses.append("t.due_at >= ?")
        params.append(normalize_stats_date(date_from))
    if date_to:
        clauses.append("t.due_at <= ?")
        params.append(normalize_stats_date(date_to, end_of_day=True))
    return " AND ".join(clauses), params


@app.get("/api/v1/stats/overview")
def stats(
    course_id: int | None = None,
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
    user: sqlite3.Row = Depends(current_user),
) -> dict[str, Any]:
    where, params = stats_where(user, course_id, date_from, date_to)
    current = now()
    with db() as connection:
        if course_id is not None:
            require_course_member(connection, course_id, user)
        row = connection.execute(
            f"""SELECT COUNT(*) AS total, SUM(t.status = 'done') AS completed,
                       SUM(t.status != 'done' AND t.due_at IS NOT NULL AND t.due_at < ?) AS overdue
                FROM tasks t WHERE {where}""",
            [current, *params],
        ).fetchone()
    total = row["total"] or 0
    completed = row["completed"] or 0
    return {
        "total": total,
        "completed": completed,
        "overdue": row["overdue"] or 0,
        "completion_rate": round(completed / total, 2) if total else 0,
        "server_time": current,
    }


@app.get("/api/v1/stats/courses")
def course_stats(
    date_from: str | None = Query(default=None, alias="from"),
    date_to: str | None = Query(default=None, alias="to"),
    user: sqlite3.Row = Depends(current_user),
) -> list[dict[str, Any]]:
    where, params = stats_where(user, None, date_from, date_to)
    membership = "1 = 1" if user["role"] == "admin" else "EXISTS (SELECT 1 FROM course_members cm WHERE cm.course_id = c.id AND cm.user_id = ?)"
    membership_params: list[Any] = [] if user["role"] == "admin" else [user["id"]]
    with db() as connection:
        rows = connection.execute(
            f"""SELECT c.id AS course_id, c.name AS course_name, COUNT(t.id) AS total,
                       COALESCE(SUM(t.status = 'done'), 0) AS completed,
                       COALESCE(SUM(t.status != 'done' AND t.due_at IS NOT NULL AND t.due_at < ?), 0) AS overdue
                FROM courses c LEFT JOIN tasks t ON t.course_id = c.id AND {where}
                WHERE {membership} GROUP BY c.id ORDER BY c.name""",
            [now(), *params, *membership_params],
        ).fetchall()
    result = []
    for row in rows:
        item = dict(row)
        item["completion_rate"] = round(item["completed"] / item["total"], 2) if item["total"] else 0
        result.append(item)
    return result
