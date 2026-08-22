import re
from typing import Optional, Dict, Any, List, Union
from langchain_core.tools import tool
import database as db

def sanitize_task_title(raw_title: str) -> str:
    """Extract clean action/activity name from user input, removing chatbot task prefixes."""
    clean = raw_title.strip(" .?!\"'")
    prefixes = [
        r"^please\s+",
        r"^can you\s+",
        r"^could you\s+",
        r"^create\s+a\s+task\s+to\s+",
        r"^create\s+a\s+task\s+for\s+",
        r"^create\s+task\s+to\s+",
        r"^create\s+task\s+for\s+",
        r"^add\s+a\s+task\s+to\s+",
        r"^add\s+a\s+task\s+for\s+",
        r"^add\s+task\s+to\s+",
        r"^add\s+task\s+for\s+",
        r"^new\s+task\s+to\s+",
        r"^new\s+task\s+for\s+",
        r"^create\s+a\s+task\s+",
        r"^create\s+task\s+",
        r"^add\s+a\s+task\s+",
        r"^add\s+task\s+",
        r"^to\s+",
        r"^for\s+",
        r"^the\s+",
    ]
    for p in prefixes:
        clean = re.sub(p, "", clean, flags=re.IGNORECASE).strip(" .?!\"'")
    
    lower = clean.lower()
    if "security training" in lower or "security" in lower:
        return "Complete security training"
    elif "vpn" in lower:
        return "Complete VPN setup"
    elif "benefit" in lower or "health insurance" in lower:
        return "Enroll in benefits"
    elif "compliance" in lower:
        return "Complete compliance training"
    elif "i-9" in lower:
        return "Complete I-9 verification"
    elif "direct deposit" in lower:
        return "Submit direct deposit forms"
    elif "email" in lower or "company email" in lower:
        return "Set up company email"
    elif "laptop" in lower:
        return "Complete laptop setup"
    
    return clean[:1].upper() + clean[1:] if clean else "New Task"

@tool
def create_onboarding_task(title: str, description: str = "") -> Dict[str, Any]:
    """
    Add an onboarding action/activity to the database.
    
    Args:
        title: The descriptive action of the onboarding task (e.g. 'Complete security training', 'Enroll in benefits', 'Set up VPN').
        description: Optional additional notes or details about the task.
        
    Returns:
        A dictionary containing the created task details and success status.
    """
    clean_title = title.strip(" .?!\"'")
    if not clean_title:
        return {"success": False, "error": "Task title cannot be empty."}
    
    # Check for generic/ambiguous single-word task requests like just 'training'
    if clean_title.lower() in ["training", "complete training", "do training", "setup"]:
        return {
            "success": False,
            "ambiguous": True,
            "message": "Which training would you like me to add — security training, compliance training, or another training?"
        }

    clean_title = sanitize_task_title(clean_title)

    try:
        task = db.create_task(title=clean_title, description=description, status="pending")
        return {
            "success": True,
            "task": task,
            "message": f"Added \"{task['title']}\" to your onboarding tasks (Status: Pending)."
        }
    except Exception as e:
        return {"success": False, "error": f"Database error creating task: {str(e)}"}

@tool
def list_onboarding_tasks(status: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve current onboarding tasks from the persistent database.
    
    Args:
        status: Optional filter by status ('pending', 'in_progress', 'completed'). If None or 'all', returns all tasks.
        
    Returns:
        A dictionary containing the list of tasks, count, and summary.
    """
    try:
        filter_status = status.lower().strip() if status and status.lower().strip() not in ["all", "none", ""] else None
        tasks = db.list_tasks(status=filter_status)
        return {
            "success": True,
            "count": len(tasks),
            "filter": filter_status or "all",
            "tasks": tasks
        }
    except Exception as e:
        return {"success": False, "error": f"Database error listing tasks: {str(e)}", "tasks": []}

@tool
def get_onboarding_task(task_id: Optional[int] = None, title: Optional[str] = None) -> Dict[str, Any]:
    """
    Get details of a specific onboarding task by ID or search by title.
    
    Args:
        task_id: The integer ID of the task (if known).
        title: Part or full title of the task to search for.
        
    Returns:
        Task details or list of matching tasks.
    """
    try:
        result = db.get_task(task_id=task_id, title_query=title)
        if result is None:
            return {"success": False, "found": False, "message": "No matching task found."}
        if isinstance(result, list):
            return {"success": True, "found": True, "count": len(result), "matches": result}
        return {"success": True, "found": True, "task": result}
    except Exception as e:
        return {"success": False, "error": f"Database error finding task: {str(e)}"}

@tool
def complete_onboarding_task(task_id: Optional[int] = None, title: Optional[str] = None) -> Dict[str, Any]:
    """
    Mark an onboarding task as completed in the database.
    
    Args:
        task_id: The ID of the task to complete (if known).
        title: The title or topic of the task to complete (e.g. 'security training', 'VPN setup', 'benefits').
        
    Returns:
        Status of completion. If multiple active tasks match the title, returns the list for user clarification.
    """
    try:
        if task_id is not None:
            updated = db.update_task(task_id=task_id, status="completed")
            if updated:
                return {
                    "success": True,
                    "task": updated,
                    "message": f"Great! I've marked '{updated['title']}' as completed."
                }
            else:
                return {"success": False, "error": f"Task with ID {task_id} not found."}

        if title:
            clean_title = title.strip()
            # If title is just 'it' or 'that task', we search active tasks
            if clean_title.lower() in ["it", "that", "the task", "that task", "the previous task", "that one"]:
                active_tasks = db.list_tasks(status="pending") + db.list_tasks(status="in_progress")
                if len(active_tasks) == 1:
                    updated = db.update_task(task_id=active_tasks[0]["id"], status="completed")
                    return {
                        "success": True,
                        "task": updated,
                        "message": f"Great! I've marked '{updated['title']}' as completed."
                    }
                elif len(active_tasks) > 1:
                    return {
                        "success": False,
                        "ambiguous": True,
                        "message": "I found multiple pending tasks. Which one would you like me to mark complete?",
                        "tasks": active_tasks
                    }
                else:
                    return {"success": False, "message": "You currently have no pending tasks to complete."}

            res = db.complete_task(title_query=clean_title)
            
            if res is None:
                # Check if all tasks are completed or if none match
                all_tasks = db.list_tasks()
                if not all_tasks:
                    return {"success": False, "message": f"No tasks found matching '{clean_title}'. You have no tasks recorded yet."}
                return {"success": False, "message": f"I couldn't find an active task matching '{clean_title}'."}

            if isinstance(res, list):
                # Multiple matches found
                task_names = [f"'{t['title']}'" for t in res]
                return {
                    "success": False,
                    "ambiguous": True,
                    "message": f"I found multiple matching tasks ({', '.join(task_names)}). Which one would you like me to mark complete?",
                    "matches": res
                }

            # Single task updated
            return {
                "success": True,
                "task": res,
                "message": f"Great! I've marked '{res['title']}' as completed."
            }

        return {"success": False, "error": "Please specify a task ID or task title to complete."}
    except Exception as e:
        return {"success": False, "error": f"Database error completing task: {str(e)}"}

@tool
def update_onboarding_task(
    task_id: int,
    title: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update details or status of an existing onboarding task.
    
    Args:
        task_id: The ID of the task to update.
        title: New title (optional).
        description: New description (optional).
        status: New status ('pending', 'in_progress', 'completed') (optional).
    """
    try:
        updated = db.update_task(task_id=task_id, title=title, description=description, status=status)
        if updated:
            return {"success": True, "task": updated, "message": f"Task {task_id} updated successfully."}
        return {"success": False, "error": f"Task {task_id} not found."}
    except Exception as e:
        return {"success": False, "error": f"Database error updating task: {str(e)}"}

TASK_TOOLS = [
    create_onboarding_task,
    list_onboarding_tasks,
    get_onboarding_task,
    complete_onboarding_task,
    update_onboarding_task,
]
