from __future__ import annotations

from datetime import date
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db, login_manager


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="teacher")  # 'admin' | 'teacher'

    classrooms = db.relationship("Classroom", backref="owner", lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id: str):
    return User.query.get(int(user_id))


class Classroom(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    students = db.relationship("Student", backref="classroom", cascade="all, delete-orphan")
    sessions = db.relationship("Session", backref="classroom", cascade="all, delete-orphan")


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey("classroom.id"), nullable=False)


class Session(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    class_id = db.Column(db.Integer, db.ForeignKey("classroom.id"), nullable=False)

    entries = db.relationship("AttendanceEntry", backref="session", cascade="all, delete-orphan")


class AttendanceEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("session.id"), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    present = db.Column(db.Boolean, default=False)

    student = db.relationship("Student")


def get_or_create_today_session(classroom: Classroom) -> Session:
    today = date.today().isoformat()
    s = Session.query.filter_by(class_id=classroom.id, date=today).first()
    if s:
        return s
    s = Session(date=today, class_id=classroom.id)
    db.session.add(s)
    db.session.commit()
    return s


def get_or_create_session(classroom: Classroom, dt: str) -> Session:
    s = Session.query.filter_by(class_id=classroom.id, date=dt).first()
    if s:
        return s
    s = Session(date=dt, class_id=classroom.id)
    db.session.add(s)
    db.session.commit()
    return s


class Stage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    class_id = db.Column(db.Integer, db.ForeignKey("classroom.id"), nullable=False)
    name = db.Column(db.String(255), nullable=False)
    start = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    end = db.Column(db.String(10), nullable=False)    # YYYY-MM-DD
    weekdays = db.Column(db.String(32), nullable=False)  # comma separated 0..6


class GlobalStage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    start = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD
    end = db.Column(db.String(10), nullable=False)    # YYYY-MM-DD
    weekdays = db.Column(db.String(32), nullable=False)  # comma separated 0..6


class StageSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("session.id"), unique=True, nullable=False)
    stage_id = db.Column(db.Integer, db.ForeignKey("stage.id"), nullable=False)
