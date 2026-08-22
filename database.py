import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from config import Config

ALLOWED_STATUSES = {"pending", "in_progress", "completed"}

def get_connection() -> sqlite3.Connection:
    """Create a thread-safe connection to the SQLite database."""
    Config.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(Config.DATABASE_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    """Initialize the tasks table in SQLite database."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT DEFAULT '',
                status TEXT NOT NULL CHECK(status IN ('pending', 'in_progress', 'completed')),
                created_at TEXT NOT NULL,
                completed_at TEXT
            )
        """)
        conn.commit()

def _row_to_dict(row: Optional[sqlite3.Row]) -> Optional[Dict[str, Any]]:
    """Helper to convert sqlite3.Row to Python dict."""
    if row is None:
        return None
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"] or "",
        "status": row["status"],
        "created_at": row["created_at"],
        "completed_at": row["completed_at"]
    }

def create_task(title: str, description: str = "", status: str = "pending") -> Dict[str, Any]:
    """
    Create a new onboarding task.
    Allowed statuses: 'pending', 'in_progress', 'completed'
    """
    title = title.strip()
    if not title:
        raise ValueError("Task title cannot be empty.")
    
    status = status.lower().strip()
    if status not in ALLOWED_STATUSES:
        status = "pending"

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    completed_at = now_iso if status == "completed" else None

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (title, description, status, created_at, completed_at)
            VALUES (?, ?, ?, ?, ?)
        """, (title, description.strip(), status, now_iso, completed_at))
        conn.commit()
        task_id = cursor.lastrowid
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return _row_to_dict(cursor.fetchone())

def list_tasks(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List onboarding tasks, optionally filtered by status ('pending', 'in_progress', 'completed').
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        if status and status.lower().strip() in ALLOWED_STATUSES:
            cursor.execute(
                "SELECT * FROM tasks WHERE status = ? ORDER BY id ASC",
                (status.lower().strip(),)
            )
        else:
            cursor.execute("SELECT * FROM tasks ORDER BY id ASC")
        rows = cursor.fetchall()
        return [_row_to_dict(r) for r in rows]

def get_task(task_id: Optional[int] = None, title_query: Optional[str] = None) -> Optional[Union[Dict[str, Any], List[Dict[str, Any]]]]:
    """
    Get a task by ID or search by title.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        if task_id is not None:
            cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
            return _row_to_dict(cursor.fetchone())
        elif title_query:
            return find_tasks_by_title(title_query)
        return None

def find_tasks_by_title(query: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search tasks with case-insensitive fuzzy/substring matching on title.
    """
    query = query.strip()
    if not query:
        return []
    
    with get_connection() as conn:
        cursor = conn.cursor()
        param = f"%{query}%"
        if status and status.lower().strip() in ALLOWED_STATUSES:
            cursor.execute(
                "SELECT * FROM tasks WHERE LOWER(title) LIKE LOWER(?) AND status = ? ORDER BY id ASC",
                (param, status.lower().strip())
            )
        else:
            cursor.execute(
                "SELECT * FROM tasks WHERE LOWER(title) LIKE LOWER(?) ORDER BY id ASC",
                (param,)
            )
        rows = cursor.fetchall()
        return [_row_to_dict(r) for r in rows]

def update_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Update task details or status.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        current = cursor.fetchone()
        if not current:
            return None
        
        new_title = title.strip() if title is not None else current["title"]
        new_desc = description.strip() if description is not None else current["description"]
        new_status = status.lower().strip() if status is not None else current["status"]
        
        if new_status not in ALLOWED_STATUSES:
            new_status = current["status"]
            
        completed_at = current["completed_at"]
        if new_status == "completed" and current["status"] != "completed":
            completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elif new_status != "completed":
            completed_at = None

        cursor.execute("""
            UPDATE tasks
            SET title = ?, description = ?, status = ?, completed_at = ?
            WHERE id = ?
        """, (new_title, new_desc, new_status, completed_at, task_id))
        conn.commit()

        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        return _row_to_dict(cursor.fetchone())

def complete_task(task_id: Optional[int] = None, title_query: Optional[str] = None) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
    """
    Mark a task as completed by ID or title match.
    If multiple tasks match title_query, returns the list of matching tasks for disambiguation.
    """
    if task_id is not None:
        return update_task(task_id, status="completed")
    
    if title_query:
        # Check active (non-completed) tasks first
        matches = find_tasks_by_title(title_query, status=None)
        # Filter pending or in_progress first
        active_matches = [m for m in matches if m["status"] != "completed"]
        
        if len(active_matches) == 1:
            return update_task(active_matches[0]["id"], status="completed")
        elif len(active_matches) > 1:
            return active_matches  # Multiple active matches need clarification
        elif len(matches) == 1:
            # Only 1 match and it's already completed
            return matches[0]
        elif len(matches) > 1:
            return matches
        return None
    return None

def delete_task(task_id: int) -> bool:
    """Delete a task by ID."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        return cursor.rowcount > 0

# Initialize DB on module load
init_db()
