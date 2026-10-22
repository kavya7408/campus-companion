
import re
from datetime import date, timedelta


def get_deadline(text):
    """Convert common deadline words into a date."""
    text = text.lower()
    today = date.today()

    if "day after tomorrow" in text:
        return (today + timedelta(days=2)).isoformat()

    if "tomorrow" in text:
        return (today + timedelta(days=1)).isoformat()

    if "today" in text:
        return today.isoformat()

    weekdays = {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    for day, weekday in weekdays.items():
        if re.search(rf"\b{day}\b", text):
            days_ahead = (weekday - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            return (today + timedelta(days=days_ahead)).isoformat()

    return None


def parse_tasks(message):
    """Extract basic task details from a student's message."""
    parts = re.split(r",\s*and\s+|\s+and\s+", message, flags=re.IGNORECASE)

    tasks = []

    for part in parts:
        text = part.strip()
        if not text:
            continue

        lower = text.lower()

        if "assignment" in lower:
            task_type = "assignment"
        elif "exam" in lower or "test" in lower:
            task_type = "exam"
        elif "project" in lower:
            task_type = "project"
        else:
            continue

        hours_match = re.search(
            r"(\d+(?:\.\d+)?)\s*hours?",
            lower
        )

        estimated_hours = (
            float(hours_match.group(1))
            if hours_match
            else 2.0
        )

        deadline = get_deadline(lower)

        if "dbms" in lower:
            subject = "DBMS"
        elif "java" in lower:
            subject = "Java"
        elif "python" in lower:
            subject = "Python"
        elif "math" in lower:
            subject = "Maths"
        else:
            subject = task_type.title()

        tasks.append({
            "title": f"{subject} {task_type.title()}",
            "task_type": task_type,
            "due_date": deadline,
            "estimated_hours": estimated_hours,
            "priority": "high" if deadline else "medium",
        })

    return tasks


if __name__ == "__main__":
    message = (
        "I have a DBMS assignment due tomorrow that needs 3 hours, "
        "and a Java exam on Friday that needs 2 hours."
    )

    result = parse_tasks(message)

    for task in result:
        print(task)
