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

app = FastAPI(title="EduCRM Platform")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

VALID_ROLES = {"admin", "teacher", "student"}
DEFAULT_SUBJECTS = [
    {
        "slug": "english",
        "name": "English",
        "description": "Grammar, reading, vocabulary, and communication practice.",
        "color": "#d15c32",
    },
    {
        "slug": "mathematics",
        "name": "Mathematics",
        "description": "Arithmetic, algebra, geometry, and problem-solving lessons.",
        "color": "#2f6d62",
    },
    {
        "slug": "history",
        "name": "History",
        "description": "World civilizations, major events, and historical analysis.",
        "color": "#7a4c8a",
    },
    {
        "slug": "biology",
        "name": "Biology",
        "description": "Cells, human systems, plants, genetics, and ecosystems.",
        "color": "#427f45",
    },
]
DEFAULT_LESSONS = {
    "english": [
        {
            "title": "Parts of Speech Essentials",
            "summary": "A practical overview of nouns, verbs, adjectives, and adverbs.",
            "content": "Students review the eight parts of speech and build example sentences that show correct word function in context.",
        },
        {
            "title": "Reading for Main Idea",
            "summary": "Strategies for identifying topic, purpose, and supporting details.",
            "content": "The lesson trains students to scan a passage, annotate keywords, and summarize each paragraph in one sentence.",
        },
    ],
    "mathematics": [
        {
            "title": "Linear Equations",
            "summary": "Solve one-step and two-step equations with balance method logic.",
            "content": "Students isolate variables, verify solutions, and connect equations to short real-world situations.",
        },
        {
            "title": "Geometry Basics",
            "summary": "Angles, perimeter, area, and shape properties.",
            "content": "The class compares triangles, quadrilaterals, and circles while practicing formulas with guided examples.",
        },
    ],
    "history": [
        {
            "title": "Ancient Civilizations",
            "summary": "Mesopotamia, Egypt, Indus Valley, and early China.",
            "content": "Students explore how geography shaped trade, leadership, writing systems, and social structure.",
        },
        {
            "title": "Industrial Revolution",
            "summary": "Technology, urbanization, labor, and global impact.",
            "content": "This lesson highlights invention, factory systems, and the social changes caused by industrial growth.",
        },
    ],
    "biology": [
        {
            "title": "Cell Structure and Function",
            "summary": "Organelles and how cells stay alive and organized.",
            "content": "Students compare plant and animal cells and explain the role of the nucleus, membrane, and mitochondria.",
        },
        {
            "title": "Ecosystems and Food Chains",
            "summary": "Energy flow, producers, consumers, and decomposers.",
            "content": "The lesson explains how living things depend on each other and how environmental changes affect a habitat.",
        },
    ],
}
DEFAULT_QUIZZES = {
    "english": {
        "title": "English Foundations Quiz",
        "description": "Check understanding of grammar and reading skills.",
        "questions": [
            {
                "question_text": "Which word is a verb in the sentence: 'Birds fly high'?",
                "option_a": "Birds",
                "option_b": "fly",
                "option_c": "high",
                "option_d": "sentence",
                "correct_option": "B",
                "explanation": "A verb shows action. 'Fly' tells what birds do.",
            },
            {
                "question_text": "What is the main idea of a paragraph?",
                "option_a": "A random detail",
                "option_b": "The first word",
                "option_c": "The central message",
                "option_d": "The final punctuation",
                "correct_option": "C",
                "explanation": "The main idea is the core point the writer wants the reader to understand.",
            },
            {
                "question_text": "Which sentence is punctuated correctly?",
                "option_a": "I like apples oranges and bananas.",
                "option_b": "I like apples, oranges, and bananas.",
                "option_c": "I like, apples oranges and bananas.",
                "option_d": "I like apples oranges, and bananas",
                "correct_option": "B",
                "explanation": "The items in a list are separated clearly with commas.",
            },
        ],
    },
    "mathematics": {
        "title": "Mathematics Skills Quiz",
        "description": "Practice equations, numbers, and geometry.",
        "questions": [
            {
                "question_text": "Solve: 3x = 18",
                "option_a": "3",
                "option_b": "6",
                "option_c": "9",
                "option_d": "12",
                "correct_option": "B",
                "explanation": "Divide both sides by 3 to get x = 6.",
            },
            {
                "question_text": "What is the area of a rectangle with length 5 and width 4?",
                "option_a": "9",
                "option_b": "10",
                "option_c": "20",
                "option_d": "25",
                "correct_option": "C",
                "explanation": "Area = length x width = 5 x 4 = 20.",
            },
            {
                "question_text": "Which number is prime?",
                "option_a": "9",
                "option_b": "15",
                "option_c": "21",
                "option_d": "13",
                "correct_option": "D",
                "explanation": "13 has exactly two factors: 1 and 13.",
            },
        ],
    },
    "history": {
        "title": "History Knowledge Quiz",
        "description": "Review major periods and cause-effect thinking.",
        "questions": [
            {
                "question_text": "Which civilization is known for pyramids?",
                "option_a": "Ancient Egypt",
                "option_b": "Ancient Rome",
                "option_c": "Maya only",
                "option_d": "Industrial Britain",
                "correct_option": "A",
                "explanation": "Ancient Egypt is especially known for the pyramids at Giza.",
            },
            {
                "question_text": "What was one result of the Industrial Revolution?",
                "option_a": "Fewer machines",
                "option_b": "Growth of factories",
                "option_c": "End of trade",
                "option_d": "No urbanization",
                "correct_option": "B",
                "explanation": "Factories expanded and cities grew during industrialization.",
            },
            {
                "question_text": "Why do historians use primary sources?",
                "option_a": "To avoid evidence",
                "option_b": "To guess events",
                "option_c": "To study original evidence",
                "option_d": "To replace analysis",
                "correct_option": "C",
                "explanation": "Primary sources are direct records or objects from the time being studied.",
            },
        ],
    },
    "biology": {
        "title": "Biology Readiness Quiz",
        "description": "Measure understanding of cells and ecosystems.",
        "questions": [
            {
                "question_text": "Which organelle is often called the control center of the cell?",
                "option_a": "Nucleus",
                "option_b": "Cell wall",
                "option_c": "Chlorophyll",
                "option_d": "Rib cage",
                "correct_option": "A",
                "explanation": "The nucleus stores DNA and directs many cell activities.",
            },
            {
                "question_text": "What do producers make in a food chain?",
                "option_a": "Metal",
                "option_b": "Their own food",
                "option_c": "Only oxygen",
                "option_d": "Predators",
                "correct_option": "B",
                "explanation": "Producers create their own food, usually by photosynthesis.",
            },
            {
                "question_text": "Which is a characteristic of living things?",
                "option_a": "They never change",
                "option_b": "They do not need energy",
                "option_c": "They grow and respond",
                "option_d": "They cannot reproduce",
                "correct_option": "C",
                "explanation": "Living organisms grow, respond to stimuli, and use energy.",
            },
        ],
    },
}


class UserRegister(BaseModel):
    full_name: str = Field(min_length=3, max_length=120)
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=4, max_length=128)
    role: str = Field(default="student")

    @field_validator("full_name")
    @classmethod
    def clean_full_name(cls, value: str) -> str:
        return " ".join(value.split())

    @field_validator("username")
    @classmethod
    def clean_username(cls, value: str) -> str:
        cleaned = value.strip().lower()
        if not cleaned.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must contain only letters, numbers, '_' or '-'.")
        return cleaned

    @field_validator("role")
    @classmethod
    def validate_role(cls, value: str) -> str:
        role = value.strip().lower()
        if role not in VALID_ROLES:
            raise ValueError("Invalid role.")
        return role


class UserLogin(BaseModel):
    username: str
    password: str
    role: str

    @field_validator("role")
    @classmethod
    def validate_login_role(cls, value: str) -> str:
        role = value.strip().lower()
        if role not in VALID_ROLES:
            raise ValueError("Invalid role.")
        return role


class AnnouncementCreate(BaseModel):
    title: str = Field(min_length=3, max_length=120)
    body: str = Field(min_length=6, max_length=2000)
    audience: str = Field(default="all")

    @field_validator("audience")
    @classmethod
    def validate_audience(cls, value: str) -> str:
        audience = value.strip().lower()
        if audience not in {"all", "teacher", "student"}:
            raise ValueError("Invalid audience.")
        return audience


class LessonCreate(BaseModel):
    subject_id: int
    title: str = Field(min_length=3, max_length=120)
    summary: str = Field(min_length=6, max_length=250)
    content: str = Field(min_length=20, max_length=4000)


class QuizSubmission(BaseModel):
    answers: dict[int, str]


def get_db() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def hash_password(password: str, salt: str) -> str:
    value = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return value.hex()


def create_password_record(password: str) -> str:
    salt = secrets.token_hex(16)
    return f"{salt}${hash_password(password, salt)}"


def verify_password(password: str, password_record: str) -> bool:
    try:
        salt, hashed = password_record.split("$", 1)
    except ValueError:
        return False
    return hash_password(password, salt) == hashed


def create_default_user(
    conn: sqlite3.Connection, username: str, full_name: str, role: str, password: str
) -> int:
    existing = conn.execute(
        "SELECT id FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    if existing:
        return int(existing["id"])

    cursor = conn.execute(
        """
        INSERT INTO users (full_name, username, password_hash, role)
        VALUES (?, ?, ?, ?)
        """,
        (full_name, username, create_password_record(password), role),
    )
    return int(cursor.lastrowid)


def init_db() -> None:
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        user_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()
        }
        if "full_name" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN full_name TEXT NOT NULL DEFAULT ''")
        if "role" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT NOT NULL DEFAULT 'student'")
        conn.execute(
            """
            UPDATE users
            SET
                full_name = CASE
                    WHEN full_name IS NULL OR TRIM(full_name) = '' THEN username
                    ELSE full_name
                END,
                role = CASE
                    WHEN role IS NULL OR TRIM(role) = '' THEN 'student'
                    ELSE LOWER(role)
                END
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
            CREATE TABLE IF NOT EXISTS subjects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                slug TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                color TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS teacher_subjects (
                teacher_id INTEGER NOT NULL,
                subject_id INTEGER NOT NULL,
                PRIMARY KEY (teacher_id, subject_id),
                FOREIGN KEY (teacher_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS lessons (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                content TEXT NOT NULL,
                created_by INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quizzes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                created_by INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                option_a TEXT NOT NULL,
                option_b TEXT NOT NULL,
                option_c TEXT NOT NULL,
                option_d TEXT NOT NULL,
                correct_option TEXT NOT NULL,
                explanation TEXT NOT NULL,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quiz_id INTEGER NOT NULL,
                student_id INTEGER NOT NULL,
                score INTEGER NOT NULL,
                total_questions INTEGER NOT NULL,
                submitted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS quiz_answers (
                attempt_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                selected_option TEXT NOT NULL,
                is_correct INTEGER NOT NULL,
                PRIMARY KEY (attempt_id, question_id),
                FOREIGN KEY (attempt_id) REFERENCES quiz_attempts(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES quiz_questions(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                audience TEXT NOT NULL DEFAULT 'all',
                created_by INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )

        admin_id = create_default_user(conn, "admin", "System Administrator", "admin", "admin123")
        english_teacher_id = create_default_user(
            conn, "teacher_english", "Emma Carter", "teacher", "teacher123"
        )
        science_teacher_id = create_default_user(
            conn, "teacher_science", "Daniel Brown", "teacher", "teacher123"
        )
        create_default_user(conn, "student_demo", "Alex Johnson", "student", "student123")

        subject_ids: dict[str, int] = {}
        for subject in DEFAULT_SUBJECTS:
            existing = conn.execute(
                "SELECT id FROM subjects WHERE slug = ?",
                (subject["slug"],),
            ).fetchone()
            if existing:
                subject_ids[subject["slug"]] = int(existing["id"])
                continue

            cursor = conn.execute(
                """
                INSERT INTO subjects (slug, name, description, color)
                VALUES (?, ?, ?, ?)
                """,
                (
                    subject["slug"],
                    subject["name"],
                    subject["description"],
                    subject["color"],
                ),
            )
            subject_ids[subject["slug"]] = int(cursor.lastrowid)

        teacher_pairs = [
            (english_teacher_id, subject_ids["english"]),
            (english_teacher_id, subject_ids["history"]),
            (science_teacher_id, subject_ids["mathematics"]),
            (science_teacher_id, subject_ids["biology"]),
        ]
        for teacher_id, subject_id in teacher_pairs:
            conn.execute(
                """
                INSERT OR IGNORE INTO teacher_subjects (teacher_id, subject_id)
                VALUES (?, ?)
                """,
                (teacher_id, subject_id),
            )

        for slug, lessons in DEFAULT_LESSONS.items():
            subject_id = subject_ids[slug]
            lesson_count = conn.execute(
                "SELECT COUNT(*) AS count FROM lessons WHERE subject_id = ?",
                (subject_id,),
            ).fetchone()["count"]
            if lesson_count:
                continue
            for lesson in lessons:
                conn.execute(
                    """
                    INSERT INTO lessons (subject_id, title, summary, content, created_by)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        subject_id,
                        lesson["title"],
                        lesson["summary"],
                        lesson["content"],
                        admin_id,
                    ),
                )

        for slug, quiz in DEFAULT_QUIZZES.items():
            subject_id = subject_ids[slug]
            existing = conn.execute(
                "SELECT id FROM quizzes WHERE subject_id = ? LIMIT 1",
                (subject_id,),
            ).fetchone()
            if existing:
                continue
            cursor = conn.execute(
                """
                INSERT INTO quizzes (subject_id, title, description, created_by)
                VALUES (?, ?, ?, ?)
                """,
                (subject_id, quiz["title"], quiz["description"], admin_id),
            )
            quiz_id = int(cursor.lastrowid)
            for question in quiz["questions"]:
                conn.execute(
                    """
                    INSERT INTO quiz_questions (
                        quiz_id, question_text, option_a, option_b, option_c, option_d,
                        correct_option, explanation
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        quiz_id,
                        question["question_text"],
                        question["option_a"],
                        question["option_b"],
                        question["option_c"],
                        question["option_d"],
                        question["correct_option"],
                        question["explanation"],
                    ),
                )

        announcement_count = conn.execute(
            "SELECT COUNT(*) AS count FROM announcements"
        ).fetchone()["count"]
        if not announcement_count:
            conn.execute(
                """
                INSERT INTO announcements (title, body, audience, created_by)
                VALUES (?, ?, ?, ?)
                """,
                (
                    "Welcome to EduCRM",
                    "Use the admin panel to manage users, the teacher panel to publish lessons, and the student panel to study and take quizzes.",
                    "all",
                    admin_id,
                ),
            )

        conn.commit()


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/register")
def register_redirect() -> RedirectResponse:
    return RedirectResponse(url="/", status_code=307)


@app.get("/tasks")
def tasks_redirect() -> RedirectResponse:
    return RedirectResponse(url="/dashboard", status_code=307)


@app.get("/index.html")
def old_index_redirect() -> RedirectResponse:
    return RedirectResponse(url="/dashboard", status_code=307)


def get_current_user(authorization: str | None = Header(default=None)) -> sqlite3.Row:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication token is missing.")
    token = authorization[7:].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Authentication token is invalid.")

    with get_db() as conn:
        user = conn.execute(
            """
            SELECT users.id, users.full_name, users.username, users.role
            FROM sessions
            JOIN users ON users.id = sessions.user_id
            WHERE sessions.token = ?
            """,
            (token,),
        ).fetchone()
    if not user:
        raise HTTPException(status_code=401, detail="Session not found.")
    return user


def require_role(user: sqlite3.Row, *roles: str) -> None:
    if user["role"] not in roles:
        raise HTTPException(status_code=403, detail="You do not have access to this area.")


def fetch_subject_cards(conn: sqlite3.Connection) -> list[dict]:
    subjects = conn.execute(
        """
        SELECT
            s.id,
            s.slug,
            s.name,
            s.description,
            s.color,
            COUNT(DISTINCT l.id) AS lesson_count,
            COUNT(DISTINCT q.id) AS quiz_count
        FROM subjects s
        LEFT JOIN lessons l ON l.subject_id = s.id
        LEFT JOIN quizzes q ON q.subject_id = s.id
        GROUP BY s.id
        ORDER BY s.name
        """
    ).fetchall()
    return [
        {
            "id": row["id"],
            "slug": row["slug"],
            "name": row["name"],
            "description": row["description"],
            "color": row["color"],
            "lesson_count": row["lesson_count"],
            "quiz_count": row["quiz_count"],
        }
        for row in subjects
    ]


def fetch_lessons(conn: sqlite3.Connection, teacher_id: int | None = None) -> list[dict]:
    params: tuple = ()
    query = """
        SELECT
            l.id,
            l.title,
            l.summary,
            l.content,
            l.created_at,
            s.id AS subject_id,
            s.name AS subject_name,
            s.color AS subject_color,
            u.full_name AS teacher_name
        FROM lessons l
        JOIN subjects s ON s.id = l.subject_id
        JOIN users u ON u.id = l.created_by
    """
    if teacher_id is not None:
        query += " WHERE l.created_by = ?"
        params = (teacher_id,)
    query += " ORDER BY l.created_at DESC, l.id DESC"

    rows = conn.execute(query, params).fetchall()
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "summary": row["summary"],
            "content": row["content"],
            "created_at": row["created_at"],
            "subject": {
                "id": row["subject_id"],
                "name": row["subject_name"],
                "color": row["subject_color"],
            },
            "teacher_name": row["teacher_name"],
        }
        for row in rows
    ]


def fetch_announcements(conn: sqlite3.Connection, role: str | None = None) -> list[dict]:
    params: tuple = ()
    query = """
        SELECT
            a.id,
            a.title,
            a.body,
            a.audience,
            a.created_at,
            u.full_name AS author_name
        FROM announcements a
        JOIN users u ON u.id = a.created_by
    """
    if role and role in {"teacher", "student"}:
        query += " WHERE a.audience IN ('all', ?)"
        params = (role,)
    query += " ORDER BY a.created_at DESC, a.id DESC"
    rows = conn.execute(query, params).fetchall()
    return [
        {
            "id": row["id"],
            "title": row["title"],
            "body": row["body"],
            "audience": row["audience"],
            "created_at": row["created_at"],
            "author_name": row["author_name"],
        }
        for row in rows
    ]


def fetch_quizzes(conn: sqlite3.Connection, include_answers: bool = False) -> list[dict]:
    quizzes = conn.execute(
        """
        SELECT
            q.id,
            q.title,
            q.description,
            q.created_at,
            s.id AS subject_id,
            s.name AS subject_name,
            s.color AS subject_color,
            u.full_name AS teacher_name,
            COUNT(qq.id) AS question_count
        FROM quizzes q
        JOIN subjects s ON s.id = q.subject_id
        JOIN users u ON u.id = q.created_by
        LEFT JOIN quiz_questions qq ON qq.quiz_id = q.id
        GROUP BY q.id
        ORDER BY q.created_at DESC, q.id DESC
        """
    ).fetchall()

    question_rows = conn.execute(
        """
        SELECT
            id,
            quiz_id,
            question_text,
            option_a,
            option_b,
            option_c,
            option_d,
            correct_option,
            explanation
        FROM quiz_questions
        ORDER BY id
        """
    ).fetchall()

    question_map: dict[int, list[dict]] = {}
    for row in question_rows:
        payload = {
            "id": row["id"],
            "question_text": row["question_text"],
            "options": {
                "A": row["option_a"],
                "B": row["option_b"],
                "C": row["option_c"],
                "D": row["option_d"],
            },
            "explanation": row["explanation"],
        }
        if include_answers:
            payload["correct_option"] = row["correct_option"]
        question_map.setdefault(int(row["quiz_id"]), []).append(payload)

    return [
        {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "created_at": row["created_at"],
            "subject": {
                "id": row["subject_id"],
                "name": row["subject_name"],
                "color": row["subject_color"],
            },
            "teacher_name": row["teacher_name"],
            "question_count": row["question_count"],
            "questions": question_map.get(int(row["id"]), []),
        }
        for row in quizzes
    ]


@app.post("/api/register", status_code=201)
def register_user(payload: UserRegister) -> dict:
    with get_db() as conn:
        exists = conn.execute(
            "SELECT id FROM users WHERE username = ?",
            (payload.username,),
        ).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="This username is already taken.")

        conn.execute(
            """
            INSERT INTO users (full_name, username, password_hash, role)
            VALUES (?, ?, ?, ?)
            """,
            (
                payload.full_name,
                payload.username,
                create_password_record(payload.password),
                payload.role,
            ),
        )
        conn.commit()
    return {"message": "Registration completed successfully."}


@app.post("/api/login")
def login_user(payload: UserLogin) -> dict:
    username = payload.username.strip().lower()
    with get_db() as conn:
        user = conn.execute(
            """
            SELECT id, username, full_name, password_hash, role
            FROM users
            WHERE username = ? AND role = ?
            """,
            (username, payload.role),
        ).fetchone()
        if not user or not verify_password(payload.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Incorrect login credentials.")

        token = secrets.token_urlsafe(32)
        conn.execute(
            "INSERT INTO sessions (token, user_id) VALUES (?, ?)",
            (token, user["id"]),
        )
        conn.commit()

    return {
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"],
        },
    }


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


@app.get("/api/bootstrap")
def bootstrap(user: sqlite3.Row = Depends(get_current_user)) -> dict:
    with get_db() as conn:
        subjects = fetch_subject_cards(conn)
        announcements = fetch_announcements(conn, role=user["role"])
        lessons = fetch_lessons(conn, teacher_id=int(user["id"]) if user["role"] == "teacher" else None)
        quizzes = fetch_quizzes(conn, include_answers=user["role"] in {"admin", "teacher"})
        teacher_subjects = []
        if user["role"] == "teacher":
            teacher_subjects = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT s.id, s.name, s.color
                    FROM teacher_subjects ts
                    JOIN subjects s ON s.id = ts.subject_id
                    WHERE ts.teacher_id = ?
                    ORDER BY s.name
                    """,
                    (user["id"],),
                ).fetchall()
            ]

        stats = {
            "users": conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"],
            "students": conn.execute(
                "SELECT COUNT(*) AS count FROM users WHERE role = 'student'"
            ).fetchone()["count"],
            "teachers": conn.execute(
                "SELECT COUNT(*) AS count FROM users WHERE role = 'teacher'"
            ).fetchone()["count"],
            "quizzes": conn.execute("SELECT COUNT(*) AS count FROM quizzes").fetchone()["count"],
            "attempts": conn.execute(
                "SELECT COUNT(*) AS count FROM quiz_attempts"
            ).fetchone()["count"],
        }

        users = []
        results = []
        if user["role"] == "admin":
            users = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT id, full_name, username, role, created_at
                    FROM users
                    ORDER BY created_at DESC, id DESC
                    """
                ).fetchall()
            ]
            results = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT
                        qa.id,
                        qa.score,
                        qa.total_questions,
                        qa.submitted_at,
                        u.full_name AS student_name,
                        s.name AS subject_name,
                        q.title AS quiz_title
                    FROM quiz_attempts qa
                    JOIN users u ON u.id = qa.student_id
                    JOIN quizzes q ON q.id = qa.quiz_id
                    JOIN subjects s ON s.id = q.subject_id
                    ORDER BY qa.submitted_at DESC, qa.id DESC
                    """
                ).fetchall()
            ]
        elif user["role"] == "teacher":
            results = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT
                        qa.id,
                        qa.score,
                        qa.total_questions,
                        qa.submitted_at,
                        u.full_name AS student_name,
                        s.name AS subject_name,
                        q.title AS quiz_title
                    FROM quiz_attempts qa
                    JOIN users u ON u.id = qa.student_id
                    JOIN quizzes q ON q.id = qa.quiz_id
                    JOIN subjects s ON s.id = q.subject_id
                    WHERE q.subject_id IN (
                        SELECT subject_id FROM teacher_subjects WHERE teacher_id = ?
                    )
                    ORDER BY qa.submitted_at DESC, qa.id DESC
                    """,
                    (user["id"],),
                ).fetchall()
            ]
        else:
            results = [
                dict(row)
                for row in conn.execute(
                    """
                    SELECT
                        qa.id,
                        qa.score,
                        qa.total_questions,
                        qa.submitted_at,
                        s.name AS subject_name,
                        q.title AS quiz_title
                    FROM quiz_attempts qa
                    JOIN quizzes q ON q.id = qa.quiz_id
                    JOIN subjects s ON s.id = q.subject_id
                    WHERE qa.student_id = ?
                    ORDER BY qa.submitted_at DESC, qa.id DESC
                    """,
                    (user["id"],),
                ).fetchall()
            ]

    return {
        "user": {
            "id": user["id"],
            "full_name": user["full_name"],
            "username": user["username"],
            "role": user["role"],
        },
        "stats": stats,
        "subjects": subjects,
        "lessons": lessons,
        "quizzes": quizzes,
        "announcements": announcements,
        "teacher_subjects": teacher_subjects,
        "users": users,
        "results": results,
        "demo_credentials": [
            {"role": "admin", "username": "admin", "password": "admin123"},
            {"role": "teacher", "username": "teacher_english", "password": "teacher123"},
            {"role": "student", "username": "student_demo", "password": "student123"},
        ],
    }


@app.post("/api/announcements", status_code=201)
def create_announcement(
    payload: AnnouncementCreate,
    user: sqlite3.Row = Depends(get_current_user),
) -> dict:
    require_role(user, "admin")
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO announcements (title, body, audience, created_by)
            VALUES (?, ?, ?, ?)
            """,
            (payload.title.strip(), payload.body.strip(), payload.audience, user["id"]),
        )
        conn.commit()
        announcement = conn.execute(
            """
            SELECT
                a.id,
                a.title,
                a.body,
                a.audience,
                a.created_at,
                u.full_name AS author_name
            FROM announcements a
            JOIN users u ON u.id = a.created_by
            WHERE a.id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return dict(announcement)


@app.post("/api/lessons", status_code=201)
def create_lesson(payload: LessonCreate, user: sqlite3.Row = Depends(get_current_user)) -> dict:
    require_role(user, "teacher", "admin")
    with get_db() as conn:
        subject = conn.execute(
            "SELECT id, name, color FROM subjects WHERE id = ?",
            (payload.subject_id,),
        ).fetchone()
        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found.")

        if user["role"] == "teacher":
            assigned = conn.execute(
                """
                SELECT 1
                FROM teacher_subjects
                WHERE teacher_id = ? AND subject_id = ?
                """,
                (user["id"], payload.subject_id),
            ).fetchone()
            if not assigned:
                raise HTTPException(
                    status_code=403,
                    detail="You can only publish lessons for your assigned subjects.",
                )

        cursor = conn.execute(
            """
            INSERT INTO lessons (subject_id, title, summary, content, created_by)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                payload.subject_id,
                payload.title.strip(),
                payload.summary.strip(),
                payload.content.strip(),
                user["id"],
            ),
        )
        conn.commit()
        row = conn.execute(
            """
            SELECT
                l.id,
                l.title,
                l.summary,
                l.content,
                l.created_at,
                s.id AS subject_id,
                s.name AS subject_name,
                s.color AS subject_color,
                u.full_name AS teacher_name
            FROM lessons l
            JOIN subjects s ON s.id = l.subject_id
            JOIN users u ON u.id = l.created_by
            WHERE l.id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()
    return {
        "id": row["id"],
        "title": row["title"],
        "summary": row["summary"],
        "content": row["content"],
        "created_at": row["created_at"],
        "subject": {
            "id": row["subject_id"],
            "name": row["subject_name"],
            "color": row["subject_color"],
        },
        "teacher_name": row["teacher_name"],
    }


@app.post("/api/quizzes/{quiz_id}/submit")
def submit_quiz(
    quiz_id: int, payload: QuizSubmission, user: sqlite3.Row = Depends(get_current_user)
) -> dict:
    require_role(user, "student")
    with get_db() as conn:
        quiz = conn.execute(
            """
            SELECT q.id, q.title, s.name AS subject_name
            FROM quizzes q
            JOIN subjects s ON s.id = q.subject_id
            WHERE q.id = ?
            """,
            (quiz_id,),
        ).fetchone()
        if not quiz:
            raise HTTPException(status_code=404, detail="Quiz not found.")

        questions = conn.execute(
            """
            SELECT id, question_text, correct_option, explanation
            FROM quiz_questions
            WHERE quiz_id = ?
            ORDER BY id
            """,
            (quiz_id,),
        ).fetchall()
        if not questions:
            raise HTTPException(status_code=400, detail="Quiz has no questions.")

        total_questions = len(questions)
        score = 0
        per_question = []
        for question in questions:
            selected = payload.answers.get(int(question["id"]), "").strip().upper()
            if selected not in {"A", "B", "C", "D"}:
                raise HTTPException(
                    status_code=400,
                    detail="Every question must have an answer from A to D.",
                )
            is_correct = selected == question["correct_option"]
            if is_correct:
                score += 1
            per_question.append((question["id"], selected, 1 if is_correct else 0, question))

        cursor = conn.execute(
            """
            INSERT INTO quiz_attempts (quiz_id, student_id, score, total_questions)
            VALUES (?, ?, ?, ?)
            """,
            (quiz_id, user["id"], score, total_questions),
        )
        attempt_id = int(cursor.lastrowid)
        for question_id, selected, is_correct, _question in per_question:
            conn.execute(
                """
                INSERT INTO quiz_answers (attempt_id, question_id, selected_option, is_correct)
                VALUES (?, ?, ?, ?)
                """,
                (attempt_id, question_id, selected, is_correct),
            )
        conn.commit()

    return {
        "attempt_id": attempt_id,
        "quiz_title": quiz["title"],
        "subject_name": quiz["subject_name"],
        "score": score,
        "total_questions": total_questions,
        "percentage": round((score / total_questions) * 100),
    }
