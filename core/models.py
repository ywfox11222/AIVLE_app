"""📋 데이터 형식 정의 (수정 불필요)

각 객체가 어떤 필드를 갖는지 한눈에 보이게 정리.
- User, Meeting, AnalysisResult, Todo, Event
- 아이젠하워 4분면 라벨: QUADRANT_LABELS

⚠️ 필드 이름은 절대 바꾸지 말 것 (다른 파일에서 참조됨)
"""
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Optional, List


# 아이젠하워 4분면
QUADRANT_LABELS = {
    "Q1": "긴급+중요",
    "Q2": "중요·여유",
    "Q3": "긴급·위임",
    "Q4": "나중에",
}


@dataclass
class User:
    id: str
    name: str
    email: str
    team: str = ""


@dataclass
class Meeting:
    id: str
    title: str
    date: datetime
    duration_min: int
    attendees: List[str] = field(default_factory=list)
    raw_text: str = ""


@dataclass
class AnalysisResult:
    meeting_id: str
    summary: str
    decisions: List[str] = field(default_factory=list)
    personal_impact: List[dict] = field(default_factory=list)  # {title, due, quadrant}
    open_questions: List[str] = field(default_factory=list)


@dataclass
class Todo:
    id: str
    title: str
    source: str = ""             # 어떤 회의에서 추출됐는지
    due_date: Optional[date] = None
    quadrant: str = "Q2"         # Q1~Q4
    is_done: bool = False
    memo: str = ""


@dataclass
class Event:
    id: str
    title: str
    start: datetime
    end: Optional[datetime] = None
    memo: str = ""
    linked_todo_id: Optional[str] = None
