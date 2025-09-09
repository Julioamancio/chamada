from __future__ import annotations

from dataclasses import dataclass, field
from typing import List
from uuid import uuid4


def new_id() -> str:
    return uuid4().hex


@dataclass
class Student:
    id: str
    name: str


@dataclass
class Classroom:
    id: str
    name: str
    students: List[Student] = field(default_factory=list)


@dataclass
class AttendanceEntry:
    student_id: str
    present: bool


@dataclass
class Session:
    id: str
    class_id: str
    date: str  # ISO date (YYYY-MM-DD)
    entries: List[AttendanceEntry] = field(default_factory=list)

