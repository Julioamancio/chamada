from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional

from .models import Classroom, Student, Session, AttendanceEntry, new_id


DATA_PATH = Path("data/attendance.json")


def _ensure_file() -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        DATA_PATH.write_text(json.dumps({"classes": [], "sessions": []}, ensure_ascii=False, indent=2), encoding="utf-8")


def load() -> Dict:
    _ensure_file()
    return json.loads(DATA_PATH.read_text(encoding="utf-8") or "{}")


def save(data: Dict) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = DATA_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(DATA_PATH)


# Convenience helpers working on raw dict structure

def list_classes(data: Dict) -> List[Dict]:
    return list(data.get("classes", []))


def add_class(data: Dict, name: str) -> Dict:
    cls = {"id": new_id(), "name": name.strip(), "students": []}
    data.setdefault("classes", []).append(cls)
    return cls


def delete_class(data: Dict, class_id: str) -> None:
    data["classes"] = [c for c in data.get("classes", []) if c["id"] != class_id]
    # also remove sessions of this class
    data["sessions"] = [s for s in data.get("sessions", []) if s.get("class_id") != class_id]


def rename_class(data: Dict, class_id: str, new_name: str) -> None:
    for c in data.get("classes", []):
        if c["id"] == class_id:
            c["name"] = new_name.strip()
            break


def add_student(data: Dict, class_id: str, name: str) -> Dict:
    for c in data.get("classes", []):
        if c["id"] == class_id:
            st = {"id": new_id(), "name": name.strip()}
            c.setdefault("students", []).append(st)
            return st
    raise KeyError("class not found")


def remove_student(data: Dict, class_id: str, student_id: str) -> None:
    for c in data.get("classes", []):
        if c["id"] == class_id:
            c["students"] = [s for s in c.get("students", []) if s["id"] != student_id]
            # also remove from sessions entries
            for s in data.get("sessions", []):
                if s.get("class_id") == class_id:
                    s["entries"] = [e for e in s.get("entries", []) if e["student_id"] != student_id]
            return


def get_today_session(data: Dict, class_id: str) -> Dict:
    today = date.today().isoformat()
    for s in data.get("sessions", []):
        if s.get("class_id") == class_id and s.get("date") == today:
            return s
    # create if missing
    s = {"id": new_id(), "class_id": class_id, "date": today, "entries": []}
    data.setdefault("sessions", []).append(s)
    return s


def save_attendance(data: Dict, class_id: str, presence_by_student: Dict[str, bool]) -> Dict:
    session = get_today_session(data, class_id)
    # merge entries
    entries_map = {e["student_id"]: e for e in session.get("entries", [])}
    for sid, present in presence_by_student.items():
        if sid in entries_map:
            entries_map[sid]["present"] = bool(present)
        else:
            session.setdefault("entries", []).append({"student_id": sid, "present": bool(present)})
    return session


def export_class_csv(data: Dict, class_id: str, out_path: Path) -> None:
    import csv

    classes = {c["id"]: c for c in data.get("classes", [])}
    cls = classes.get(class_id)
    if not cls:
        raise KeyError("class not found")
    students = {s["id"]: s["name"] for s in cls.get("students", [])}
    sessions = [s for s in data.get("sessions", []) if s.get("class_id") == class_id]
    sessions.sort(key=lambda s: s.get("date"))

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["date", "student", "present"])
        for s in sessions:
            entries = {e["student_id"]: e.get("present", False) for e in s.get("entries", [])}
            for sid, name in students.items():
                writer.writerow([s.get("date"), name, "yes" if entries.get(sid) else "no"])

