
from datetime import date, timedelta
from database import get_tasks


def generate_study_plan(daily_hours=3, session_hours=2):
    """Generate a study schedule and identify deadline risks."""

    # Validate study-hour limits.
    if not 0 < daily_hours <= 24:
        raise ValueError(
            "Daily study hours must be between 0 and 24."
        )

    if not 0 < session_hours <= 24:
        raise ValueError(
            "Session hours must be between 0 and 24."
        )

    today = date.today()
    tasks = get_tasks(status="pending")

    priority_order = {
        "high": 1,
        "medium": 2,
        "low": 3
    }

    # Schedule earlier deadlines and higher priorities first.
    tasks.sort(
        key=lambda task: (
            task["due_date"] or "9999-12-31",
            priority_order.get(task["priority"], 2)
        )
    )

    daily_load = {}
    schedule = []
    conflicts = []

    # Generate the study schedule.
    for task in tasks:
        try:
            deadline = date.fromisoformat(task["due_date"])
            remaining = float(task["estimated_hours"])

        except (ValueError, TypeError):
            conflicts.append({
                "task": task["title"],
                "reason": "Invalid deadline or estimated hours."
            })
            continue

        if remaining <= 0:
            conflicts.append({
                "task": task["title"],
                "reason": "Estimated hours must be greater than zero."
            })
            continue

        # Tasks with passed deadlines cannot be scheduled normally.
        if deadline < today:
            conflicts.append({
                "task": task["title"],
                "deadline": deadline.isoformat(),
                "hours_remaining": round(remaining, 2),
                "reason": "Deadline has already passed."
            })
            continue

        study_day = today

        # Allow scheduling on the deadline date.
        while study_day <= deadline and remaining > 0:
            used = daily_load.get(study_day, 0)
            available = max(0, daily_hours - used)

            if available > 0:
                hours = min(
                    session_hours,
                    available,
                    remaining
                )

                schedule.append({
                    "date": study_day.isoformat(),
                    "task_id": task["id"],
                    "task": task["title"],
                    "priority": task["priority"],
                    "hours": round(hours, 2)
                })

                daily_load[study_day] = used + hours
                remaining = round(remaining - hours, 2)

            study_day += timedelta(days=1)

        # Record tasks that cannot fit before their deadlines.
        if remaining > 0:
            conflicts.append({
                "task": task["title"],
                "deadline": deadline.isoformat(),
                "hours_remaining": round(remaining, 2),
                "reason": (
                    "Not enough available study time before "
                    "the deadline. Consider starting earlier, "
                    "reducing other commitments, or requesting "
                    "an extension."
                )
            })

    # Group sessions by date.
    daily_plan = {}

    for session in schedule:
        day = session["date"]

        if day not in daily_plan:
            daily_plan[day] = {
                "date": day,
                "total_hours": 0,
                "sessions": []
            }

        daily_plan[day]["sessions"].append(session)
        daily_plan[day]["total_hours"] += session["hours"]

    result = []

    for day in sorted(daily_plan):
        item = daily_plan[day]
        item["total_hours"] = round(item["total_hours"], 2)
        result.append(item)

    # Build smarter deadline-risk information.
    at_risk_tasks = []
    on_track_count = 0
    conflict_task_ids = {
        conflict.get("task_id")
        for conflict in conflicts
        if conflict.get("task_id") is not None
    }

    # Match conflicts by task title as well, for compatibility
    # with conflict records created by earlier planner versions.
    conflict_titles = {
        conflict["task"]
        for conflict in conflicts
    }

    for task in tasks:
        title = task["title"]

        try:
            deadline = date.fromisoformat(task["due_date"])
            required_hours = float(task["estimated_hours"])

        except (ValueError, TypeError):
            at_risk_tasks.append({
                "task": title,
                "risk": "unknown",
                "reason": "Invalid deadline or estimated hours."
            })
            continue

        days_left = (deadline - today).days

        if deadline < today:
            at_risk_tasks.append({
                "task": title,
                "deadline": deadline.isoformat(),
                "days_left": days_left,
                "hours_required": required_hours,
                "risk": "overdue",
                "reason": "Deadline has already passed."
            })

        elif title in conflict_titles or task["id"] in conflict_task_ids:
            matching_conflicts = [
                conflict for conflict in conflicts
                if conflict["task"] == title
            ]

            reason = (
                matching_conflicts[0]["reason"]
                if matching_conflicts
                else "Insufficient study time before the deadline."
            )

            remaining_hours = (
                matching_conflicts[0].get("hours_remaining")
                if matching_conflicts
                else required_hours
            )

            at_risk_tasks.append({
                "task": title,
                "deadline": deadline.isoformat(),
                "days_left": days_left,
                "hours_required": required_hours,
                "hours_remaining": remaining_hours,
                "risk": "high",
                "reason": reason
            })

        elif days_left <= 1:
            at_risk_tasks.append({
                "task": title,
                "deadline": deadline.isoformat(),
                "days_left": days_left,
                "hours_required": required_hours,
                "risk": "medium",
                "reason": "Deadline is today or tomorrow."
            })

        else:
            on_track_count += 1

    deadline_summary = {
        "total_pending_tasks": len(tasks),
        "tasks_at_risk": len(at_risk_tasks),
        "tasks_on_track": on_track_count,
        "at_risk_tasks": at_risk_tasks
    }

    # Return the complete plan and risk summary.
    return {
        "success": True,
        "daily_study_limit": daily_hours,
        "total_sessions": len(schedule),
        "schedule": result,
        "conflicts": conflicts,
        "deadline_summary": deadline_summary
    }


if __name__ == "__main__":
    try:
        plan = generate_study_plan()

        print("\n===== CAMPUS COMPANION STUDY PLAN =====")
        print(f"Daily study limit: {plan['daily_study_limit']} hours")

        for day in plan["schedule"]:
            print(f"\nDate: {day['date']}")
            print(f"Total hours: {day['total_hours']}")

            for session in day["sessions"]:
                print(
                    f"  - {session['task']}: "
                    f"{session['hours']} hour(s) "
                    f"[{session['priority']} priority]"
                )

        if not plan["schedule"]:
            print("\nNo study sessions scheduled.")

        print("\n===== DEADLINE CONFLICTS =====")

        if plan["conflicts"]:
            for conflict in plan["conflicts"]:
                print(conflict)
        else:
            print("No deadline conflicts detected.")

        summary = plan["deadline_summary"]

        print("\n===== DEADLINE-RISK SUMMARY =====")
        print(f"Total pending tasks: {summary['total_pending_tasks']}")
        print(f"Tasks at risk: {summary['tasks_at_risk']}")
        print(f"Tasks on track: {summary['tasks_on_track']}")

        for task in summary["at_risk_tasks"]:
            print(f"\nTask: {task['task']}")
            print(f"Risk: {task['risk']}")
            print(f"Reason: {task['reason']}")

        print("\n=======================================")

    except (ValueError, TypeError) as error:
        print(f"Unable to generate study plan: {error}")
