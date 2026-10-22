
import sqlite3
from pathlib import Path

# Store the database in the same folder as this file.
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "campus.db"


def get_connection():
    """Create a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the tasks table if it does not already exist."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                task_type TEXT NOT NULL
                    CHECK (task_type IN ('assignment', 'exam', 'project', 'other')),
                due_date TEXT NOT NULL,
                estimated_hours REAL NOT NULL
                    CHECK (estimated_hours > 0),
                priority TEXT NOT NULL DEFAULT 'medium'
                    CHECK (priority IN ('low', 'medium', 'high')),
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'completed')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)


def add_task(title, task_type, due_date, estimated_hours,
             description="", priority="medium"):
    """Save a new task and return its ID."""
    with get_connection() as conn:
        cursor = conn.execute("""
            INSERT INTO tasks
                (title, description, task_type, due_date,
                 estimated_hours, priority)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            title, description, task_type, due_date,
            estimated_hours, priority
        ))
        return cursor.lastrowid


def get_tasks(status=None):
    """Retrieve all tasks, optionally filtered by status."""
    with get_connection() as conn:
        if status is None:
            rows = conn.execute("""
                SELECT * FROM tasks
                ORDER BY due_date ASC, id ASC
            """).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM tasks
                WHERE status = ?
                ORDER BY due_date ASC, id ASC
            """, (status,)).fetchall()

        return [dict(row) for row in rows]


def get_task(task_id):
    """Retrieve one task by its ID."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ?",
            (task_id,)
        ).fetchone()

        return dict(row) if row else None


def update_task(task_id, **fields):
    """Update selected fields of an existing task."""
    allowed_fields = {
        "title", "description", "task_type", "due_date",
        "estimated_hours", "priority", "status"
    }

    if not fields:
        raise ValueError("Provide at least one field to update.")

    if not set(fields).issubset(allowed_fields):
        raise ValueError("One or more fields cannot be updated.")

    columns = ", ".join(f"{key} = ?" for key in fields)
    values = list(fields.values())

    with get_connection() as conn:
        cursor = conn.execute(
            f"UPDATE tasks SET {columns} WHERE id = ?",
            values + [task_id]
        )
        return cursor.rowcount > 0


def delete_task(task_id):
    """Delete a task by its ID."""
    with get_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM tasks WHERE id = ?",
            (task_id,)
        )
        return cursor.rowcount > 0


# Create the database and table when this module is imported.
init_db()
