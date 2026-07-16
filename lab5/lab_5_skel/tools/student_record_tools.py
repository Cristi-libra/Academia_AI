"""
Student Record Tools.

Two tools that give the professor persistent memory about
students: saving evaluations (grade + feedback) and reading
back a student's history with their average grade.

Records are stored in a local JSON file (see STUDENT_RECORDS_FILE
in config). The file is gitignored - it contains personal data.
"""

import datetime
import json
import os

try:
    from .tool import Tool
except ImportError:
    from tool import Tool

try:
    from config import STUDENT_RECORDS_FILE
except ImportError:
    from ..config import STUDENT_RECORDS_FILE


def _load_records() -> list[dict]:
    """Load all evaluation records, returning an empty list if none exist."""
    if not os.path.exists(STUDENT_RECORDS_FILE):
        return []
    try:
        with open(STUDENT_RECORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def save_student_evaluation(student: str, topic: str, grade: int, feedback: str) -> str:
    """
    Persist one evaluation for a student.

    Parameters:
        student (str): Student name or identifier.
        topic (str): What was evaluated (e.g. 'code review: chunking function').
        grade (int): Grade from 1 to 10.
        feedback (str): Short constructive feedback.

    Returns:
        str: Confirmation message, or an error if the grade is invalid.
    """
    try:
        grade = int(grade)
    except (TypeError, ValueError):
        return f"Invalid grade '{grade}': it must be an integer between 1 and 10."
    if not 1 <= grade <= 10:
        return f"Invalid grade {grade}: it must be between 1 and 10."

    records = _load_records()
    records.append({
        "student": student.strip(),
        "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "topic": topic,
        "grade": grade,
        "feedback": feedback
    })

    try:
        with open(STUDENT_RECORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, ensure_ascii=False, indent=4)
    except OSError as error:
        return f"Could not save the evaluation: {error}"

    return (
        f"Evaluation saved for {student}: grade {grade}/10 on '{topic}'. "
        f"Total evaluations on record: {len(records)}."
    )


def get_student_record(student: str) -> str:
    """
    Return a student's evaluation history and average grade.

    Parameters:
        student (str): Student name or identifier.

    Returns:
        str: Formatted history with the average, or a message if
             the student has no evaluations yet.
    """
    records = _load_records()
    student_records = [
        r for r in records
        if r.get("student", "").lower() == student.strip().lower()
    ]

    if not student_records:
        return f"No evaluations on record for '{student}'."

    average = sum(r["grade"] for r in student_records) / len(student_records)
    lines = [
        f"Evaluation history for {student} "
        f"({len(student_records)} entries, average {average:.2f}/10):"
    ]
    for record in student_records:
        lines.append(
            f"- [{record['date']}] {record['topic']}: {record['grade']}/10 "
            f"- {record['feedback']}"
        )
    return "\n".join(lines)


save_student_evaluation_tool = Tool(
    name="save_student_evaluation",
    description=(
        "Saves an evaluation (grade 1-10 + feedback) for a student into the "
        "persistent records file. Use it after grading code or a theoretical "
        "answer, so the student's progress can be tracked over time."
    ),
    parameters={
        "type": "object",
        "properties": {
            "student": {
                "type": "string",
                "description": "The student's name or identifier."
            },
            "topic": {
                "type": "string",
                "description": (
                    "What was evaluated, e.g. 'code review: sorting function' "
                    "or 'theory: Big-O complexity'."
                )
            },
            "grade": {
                "type": "integer",
                "description": "The grade, an integer from 1 (worst) to 10 (best)."
            },
            "feedback": {
                "type": "string",
                "description": "Short constructive feedback justifying the grade."
            }
        },
        "required": ["student", "topic", "grade", "feedback"]
    },
    callback=save_student_evaluation
)

get_student_record_tool = Tool(
    name="get_student_record",
    description=(
        "Retrieves a student's saved evaluation history and average grade. "
        "Use it when the student asks about their progress, grades, or past "
        "feedback."
    ),
    parameters={
        "type": "object",
        "properties": {
            "student": {
                "type": "string",
                "description": "The student's name or identifier."
            }
        },
        "required": ["student"]
    },
    callback=get_student_record
)
