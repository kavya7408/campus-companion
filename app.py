
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import sqlite3
from task_parser import parse_tasks
from study_planner import generate_study_plan

from database import (
    add_task,
    get_tasks,
    get_task,
    update_task,
    delete_task
)

app = Flask(__name__)
CORS(app)


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "message": "Campus Companion API is ready"
    })


# CREATE: Add a task
@app.route("/api/tasks", methods=["POST"])
def create_task():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Send a JSON object."}), 400

    required = [
        "title", "task_type", "due_date", "estimated_hours"
    ]

    missing = [
        field for field in required
        if field not in data or data[field] is None
        or data[field] == ""
    ]

    if missing:
        return jsonify({
            "error": "Missing required fields.",
            "fields": missing
        }), 400

    if not isinstance(data["title"], str) or not data["title"].strip():
        return jsonify({"error": "Title cannot be empty."}), 400

    try:
        hours = float(data["estimated_hours"])

        if not 0 < hours <= 1000:
            raise ValueError

        task_id = add_task(
            title=data["title"].strip(),
            task_type=data["task_type"],
            due_date=data["due_date"],
            estimated_hours=hours,
            description=data.get("description", ""),
            priority=data.get("priority", "medium")
        )

        return jsonify({
            "success": True,
            "message": "Task created successfully.",
            "task": get_task(task_id)
        }), 201

    except (ValueError, TypeError):
        return jsonify({
            "error": "Estimated hours must be a number greater than 0 and at most 1000."
        }), 400
    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Invalid task type, priority, status, or task data."
        }), 400


# READ: Get all tasks, optionally filter by status
@app.route("/api/tasks", methods=["GET"])
def list_tasks():
    status = request.args.get("status")

    if status and status not in ("pending", "completed"):
        return jsonify({
            "error": "Status must be pending or completed."
        }), 400

    tasks = get_tasks(status)
    return jsonify({
        "success": True,
        "count": len(tasks),
        "tasks": tasks
    })


# READ: Get one task
@app.route("/api/tasks/<int:task_id>", methods=["GET"])
def retrieve_task(task_id):
    task = get_task(task_id)

    if task is None:
        return jsonify({"error": "Task not found."}), 404

    return jsonify({"success": True, "task": task})


# UPDATE: Change task details or mark as completed
@app.route("/api/tasks/<int:task_id>", methods=["PATCH"])
def edit_task(task_id):
    data = request.get_json(silent=True)

    if not isinstance(data, dict) or not data:
        return jsonify({
            "error": "Send a non-empty JSON object."
        }), 400

    allowed = {
        "title", "description", "task_type", "due_date",
        "estimated_hours", "priority", "status"
    }

    if not set(data).issubset(allowed):
        return jsonify({
            "error": "One or more fields cannot be updated."
        }), 400

    if "title" in data:
        if not isinstance(data["title"], str) or not data["title"].strip():
            return jsonify({"error": "Title cannot be empty."}), 400
        data["title"] = data["title"].strip()

    if "estimated_hours" in data:
        try:
            data["estimated_hours"] = float(data["estimated_hours"])
            if not 0 < data["estimated_hours"] <= 1000:
                raise ValueError
        except (ValueError, TypeError):
            return jsonify({
                "error": "Estimated hours must be greater than 0 and at most 1000."
            }), 400

    try:
        updated = update_task(task_id, **data)

        if not updated:
            return jsonify({"error": "Task not found."}), 404

        return jsonify({
            "success": True,
            "message": "Task updated successfully.",
            "task": get_task(task_id)
        })

    except sqlite3.IntegrityError:
        return jsonify({
            "error": "Invalid task type, priority, status, or task data."
        }), 400


# DELETE: Remove a task
@app.route("/api/tasks/<int:task_id>", methods=["DELETE"])
def remove_task(task_id):
    deleted = delete_task(task_id)

    if not deleted:
        return jsonify({"error": "Task not found."}), 404

    return jsonify({
        "success": True,
        "message": "Task deleted successfully."
    })


@app.route("/api/parse-message", methods=["POST"])
def parse_message():
    data = request.get_json(silent=True) or {}
    message = data.get("message", "").strip()

    if not message:
        return jsonify({
            "success": False,
            "error": "Please provide a message."
        }), 400

    parsed_tasks = parse_tasks(message)

    if not parsed_tasks:
        return jsonify({
            "success": False,
            "error": "No supported tasks found in the message."
        }), 400

    saved_tasks = []

    for task in parsed_tasks:
        if not task["due_date"]:
            return jsonify({
                "success": False,
                "error": "Could not identify a deadline for: " + task["title"]
            }), 400

        task_id = add_task(
            title=task["title"],
            task_type=task["task_type"],
            due_date=task["due_date"],
            estimated_hours=task["estimated_hours"],
            priority=task["priority"]
        )

        saved_tasks.append(get_task(task_id))

    return jsonify({
        "success": True,
        "count": len(saved_tasks),
        "tasks": saved_tasks
    }), 201


@app.route("/api/study-plan", methods=["GET"])
def get_study_plan():
    try:
        daily_hours = float(
            request.args.get("daily_hours", 3)
        )
        session_hours = float(
            request.args.get("session_hours", 2)
        )

        if daily_hours <= 0 or session_hours <= 0:
            return jsonify({
                "success": False,
                "error": "Study hours must be greater than zero."
            }), 400

        if daily_hours > 24 or session_hours > 24:
            return jsonify({
                "success": False,
                "error": "Study hours cannot exceed 24."
            }), 400

        plan = generate_study_plan(
            daily_hours=daily_hours,
            session_hours=session_hours
        )

        return jsonify(plan), 200

    except (ValueError, TypeError):
        return jsonify({
            "success": False,
            "error": "Please provide valid study-hour values."
        }), 400

if __name__ == "__main__":
    app.run(debug=True)
