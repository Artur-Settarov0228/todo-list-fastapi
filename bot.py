import hashlib
import secrets
import sqlite3
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, field_validator
from starlette.requests import Request

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "todos.db"

app = FastAPI(title="Todo List App")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


class TodoCreate(BaseModel):
    text: str = Field(min_length=1, max_length=200)
    status: str = Field(default="open")


class TodoUpdate(BaseModel):
    status: str


class UserRegister(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=4, max_length=128)

    @field_validator("username")
    @classmethod
    def username_chars(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username faqat harf, raqam, '_' yoki '-' bo'lishi kerak")
        return cleaned


class UserLogin(BaseModel):
    username: str
    password: str


ALLOWED_STATUSES = {"open", "in_progress", "done"}


def normalize_status(raw: str) -> str:
    status = raw.strip().lower()
    if status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="Noto'g'ri status")
    return status


def get_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def hash_password(password: str, salt: str) -> str:
    value = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return value.hex()


def create_password_record(password: str) -> str:
    salt = secrets.token_hex(16)
    hashed = hash_password(password, salt)
    return f"{salt}${hashed}"


def verify_password(password: str, password_record: str) -> bool:
    try:
        salt, hashed = password_record.split("$", 1)
    except ValueError:
        return False
    return hash_password(password, salt) == hashed


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS todos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                text TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(todos)").fetchall()
        }
        if "status" not in columns:
            conn.execute("ALTER TABLE todos ADD COLUMN status TEXT NOT NULL DEFAULT 'open'")
        if "user_id" not in columns:
            conn.execute("ALTER TABLE todos ADD COLUMN user_id INTEGER")
        if "done" in columns:
            conn.execute(
                "UPDATE todos SET status = CASE WHEN done = 1 THEN 'done' ELSE 'open' END WHERE status IS NULL OR status = ''"
            )
        conn.commit()


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("register.html", {"request": request})


@app.get("/tasks", response_class=HTMLResponse)
def tasks_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("tasks.html", {"request": request})


@app.get("/index.html")
def old_index_redirect() -> RedirectResponse:
    return RedirectResponse(url="/tasks", status_code=307)


def get_current_user_id(authorization: str | None = Header(default=None)) -> int:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token topilmadi")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Token yaroqsiz")

    with get_db() as conn:
        row = conn.execute(
            """
            SELECT users.id
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ?
            """,
            (token,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=401, detail="Session topilmadi")
    return int(row["id"])


@app.post("/api/register", status_code=201)
def register_user(payload: UserRegister) -> dict:
    with get_db() as conn:
        exists = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (payload.username,),
        ).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="Bu username band")

        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (payload.username, create_password_record(payload.password)),
        )
        conn.commit()
    return {"message": "Registratsiya muvaffaqiyatli"}


@app.post("/api/login")
def login_user(payload: UserLogin) -> dict:
    username = payload.username.strip().lower()
    with get_db() as conn:
        user = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if not user or not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Login yoki parol xato")

        token = secrets.token_urlsafe(32)
        conn.execute("INSERT INTO sessions (token, user_id) VALUES (?, ?)", (token, user["id"]))
        conn.commit()

    return {"token": token, "username": user["username"]}


@app.post("/api/logout", status_code=204)
def logout_user(authorization: str | None = Header(default=None)) -> None:
    if not authorization or not authorization.startswith("Bearer "):
        return
    token = authorization[7:].strip()
    if not token:
        return
    with get_db() as conn:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()


@app.get("/api/me")
def me(user_id: int = Depends(get_current_user_id)) -> dict:
    with get_db() as conn:
        user = conn.execute(
            "SELECT id, username FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    return {"id": user["id"], "username": user["username"]}


@app.get("/api/todos")
def list_todos(user_id: int = Depends(get_current_user_id)) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, text, status, created_at FROM todos WHERE user_id = ? ORDER BY id DESC",
            (user_id,),
        ).fetchall()
    return [
        {
            "id": row["id"],
            "text": row["text"],
            "status": row["status"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]


@app.post("/api/todos", status_code=201)
def create_todo(payload: TodoCreate, user_id: int = Depends(get_current_user_id)) -> dict:
    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Todo text cannot be empty")
    status = normalize_status(payload.status)

    with get_db() as conn:
        cursor = conn.execute(
            "INSERT INTO todos (user_id, text, status) VALUES (?, ?, ?)",
            (user_id, text, status),
        )
        conn.commit()
        todo_id = cursor.lastrowid
        row = conn.execute(
            "SELECT id, text, status, created_at FROM todos WHERE id = ? AND user_id = ?",
            (todo_id, user_id),
        ).fetchone()

    return {
        "id": row["id"],
        "text": row["text"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


@app.patch("/api/todos/{todo_id}")
def update_todo(todo_id: int, payload: TodoUpdate, user_id: int = Depends(get_current_user_id)) -> dict:
    status = normalize_status(payload.status)
    with get_db() as conn:
        exists = conn.execute(
            "SELECT id FROM todos WHERE id = ? AND user_id = ?",
            (todo_id, user_id),
        ).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Todo not found")

        conn.execute(
            "UPDATE todos SET status = ? WHERE id = ? AND user_id = ?",
            (status, todo_id, user_id),
        )
        conn.commit()
        row = conn.execute(
            "SELECT id, text, status, created_at FROM todos WHERE id = ? AND user_id = ?",
            (todo_id, user_id),
        ).fetchone()

    return {
        "id": row["id"],
        "text": row["text"],
        "status": row["status"],
        "created_at": row["created_at"],
    }


@app.delete("/api/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, user_id: int = Depends(get_current_user_id)) -> None:
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM todos WHERE id = ? AND user_id = ?",
            (todo_id, user_id),
        )
        conn.commit()

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Todo not found")
