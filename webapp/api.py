from __future__ import annotations

from dataclasses import asdict
from datetime import date
from typing import Any, Dict, List, Optional

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from . import db
from .models import AttendanceEntry, Classroom, Session, Student, get_or_create_today_session

bp = Blueprint("api", __name__)


def _owner_guard(classroom: Classroom) -> Optional[Any]:
    if classroom.owner_id != current_user.id and current_user.role != "admin":
        return jsonify({"error": "forbidden"}), 403
    return None


@bp.get("/me")
@login_required
def me():
    u = current_user
    return jsonify({"id": u.id, "email": u.email, "name": u.name, "role": u.role})


# Classes
@bp.get("/classes")
@login_required
def list_classes():
    classes = Classroom.query.filter_by(owner_id=current_user.id).order_by(Classroom.name).all()
    return jsonify([{"id": c.id, "name": c.name} for c in classes])


@bp.post("/classes")
@login_required
def create_class():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    c = Classroom(name=name, owner_id=current_user.id)
    db.session.add(c)
    db.session.commit()
    return jsonify({"id": c.id, "name": c.name}), 201


@bp.patch("/classes/<int:class_id>")
@login_required
def rename_class(class_id: int):
    c = Classroom.query.get_or_404(class_id)
    guard = _owner_guard(c)
    if guard:
        return guard
    data = request.get_json(silent=True) or {}
    new_name = (data.get("name") or "").strip()
    if not new_name:
        return jsonify({"error": "name required"}), 400
    c.name = new_name
    db.session.commit()
    return jsonify({"id": c.id, "name": c.name})


@bp.delete("/classes/<int:class_id>")
@login_required
def delete_class(class_id: int):
    c = Classroom.query.get_or_404(class_id)
    guard = _owner_guard(c)
    if guard:
        return guard
    db.session.delete(c)
    db.session.commit()
    return jsonify({"ok": True})


# Students
@bp.get("/classes/<int:class_id>/students")
@login_required
def list_students(class_id: int):
    c = Classroom.query.get_or_404(class_id)
    guard = _owner_guard(c)
    if guard:
        return guard
    sts = Student.query.filter_by(class_id=c.id).order_by(Student.name).all()
    return jsonify([{"id": s.id, "name": s.name} for s in sts])


@bp.post("/classes/<int:class_id>/students")
@login_required
def add_students(class_id: int):
    c = Classroom.query.get_or_404(class_id)
    guard = _owner_guard(c)
    if guard:
        return guard
    data = request.get_json(silent=True) or {}
    # Accept {name: str} or {names: [str]}
    names: List[str] = []
    if isinstance(data.get("names"), list):
        names = [str(x).strip() for x in data.get("names")]
    elif data.get("name"):
        names = [str(data.get("name")).strip()]
    names = [n for n in names if n]
    if not names:
        return jsonify({"error": "name(s) required"}), 400
    created = []
    for n in names:
        if not Student.query.filter_by(class_id=c.id, name=n).first():
            st = Student(name=n, class_id=c.id)
            db.session.add(st)
            db.session.flush()
            created.append({"id": st.id, "name": st.name})
    db.session.commit()
    return jsonify({"created": created, "count": len(created)})


@bp.patch("/students/<int:student_id>")
@login_required
def rename_student(student_id: int):
    st = Student.query.get_or_404(student_id)
    c = Classroom.query.get_or_404(st.class_id)
    guard = _owner_guard(c)
    if guard:
        return guard
    data = request.get_json(silent=True) or {}
    new_name = (data.get("name") or "").strip()
    if not new_name:
        return jsonify({"error": "name required"}), 400
    st.name = new_name
    db.session.commit()
    return jsonify({"id": st.id, "name": st.name})


@bp.delete("/students/<int:student_id>")
@login_required
def delete_student(student_id: int):
    st = Student.query.get_or_404(student_id)
    c = Classroom.query.get_or_404(st.class_id)
    guard = _owner_guard(c)
    if guard:
        return guard
    db.session.delete(st)
    db.session.commit()
    return jsonify({"ok": True})


# Attendance
@bp.get("/classes/<int:class_id>/attendance")
@login_required
def get_attendance(class_id: int):
    c = Classroom.query.get_or_404(class_id)
    guard = _owner_guard(c)
    if guard:
        return guard
    dt = (request.args.get("date") or date.today().isoformat())
    s = Session.query.filter_by(class_id=c.id, date=dt).first()
    if not s:
        return jsonify({"date": dt, "entries": []})
    return jsonify({
        "date": s.date,
        "entries": [{"student_id": e.student_id, "present": bool(e.present)} for e in s.entries],
    })


@bp.put("/classes/<int:class_id>/attendance")
@login_required
def put_attendance(class_id: int):
    c = Classroom.query.get_or_404(class_id)
    guard = _owner_guard(c)
    if guard:
        return guard
    data = request.get_json(silent=True) or {}
    dt = (data.get("date") or date.today().isoformat())
    present_ids = set(int(x) for x in (data.get("present_ids") or []))
    s = Session.query.filter_by(class_id=c.id, date=dt).first()
    if not s:
        s = Session(class_id=c.id, date=dt)
        db.session.add(s)
        db.session.flush()
    # Merge entries
    entries_map = {e.student_id: e for e in s.entries}
    for st in Student.query.filter_by(class_id=c.id).all():
        val = st.id in present_ids
        e = entries_map.get(st.id)
        if e:
            e.present = val
        else:
            db.session.add(AttendanceEntry(session_id=s.id, student_id=st.id, present=val))
    db.session.commit()
    return jsonify({"ok": True, "date": s.date})

