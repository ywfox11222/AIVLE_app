"""Data store - single source of truth for all pages."""
import uuid
import streamlit as st
from datetime import date
from typing import List, Optional

from .models import Todo, Meeting, AnalysisResult, Event, User
from . import demo_data


def init_state():
    ss = st.session_state
    if "_inited" in ss:
        return
    ss._inited = True
    ss.user = None
    ss.meetings = demo_data.seed_meetings()
    ss.analyses = demo_data.seed_analysis()
    ss.todos = demo_data.seed_todos()
    ss.events = demo_data.seed_events()
    ss.current_meeting_id = None
    ss.current_briefing = None
    ss.settings = {
        "default_to": "kim@company.com",
        "cc": "",
        "signature": "- Kim Daeri (Marketing) / Able AI Assistant",
        "voice": "alloy",
        "default_rate": 1.0,
        "notify_due": True,
        "notify_meeting": True,
        "notify_briefing": True,
    }


def set_user(user: User):
    st.session_state.user = user

def current_user() -> Optional[User]:
    return st.session_state.get("user")

def is_authed() -> bool:
    return current_user() is not None


def list_meetings() -> List[Meeting]:
    return st.session_state.meetings

def get_meeting(meeting_id: str) -> Optional[Meeting]:
    return next((m for m in list_meetings() if m.id == meeting_id), None)

def save_meeting(meeting: Meeting):
    """회의를 저장. 동일 ID면 교체, 없으면 추가. 최대 10건 유지."""
    meetings = st.session_state.meetings
    # 동일 ID 교체
    for i, m in enumerate(meetings):
        if m.id == meeting.id:
            meetings[i] = meeting
            return
    meetings.append(meeting)
    # 10건 초과 시 가장 오래된 항목 제거
    if len(meetings) > 10:
        meetings.pop(0)

def get_analysis(meeting_id: str) -> Optional[AnalysisResult]:
    return st.session_state.analyses.get(meeting_id)

def save_analysis(result: AnalysisResult):
    st.session_state.analyses[result.meeting_id] = result


def list_todos() -> List[Todo]:
    return st.session_state.todos

def add_todo(title: str, source: str = "", due_date: Optional[date] = None,
             quadrant: str = "Q2", memo: str = "") -> Todo:
    t = Todo(id=str(uuid.uuid4())[:8], title=title, source=source,
             due_date=due_date, quadrant=quadrant, memo=memo)
    st.session_state.todos.append(t)
    return t

def add_todos_from_impact(impact_list: List[dict], source: str) -> int:
    cnt = 0
    for item in impact_list:
        add_todo(
            title=item["title"],
            source=source,
            due_date=item.get("due"),
            quadrant=item.get("quadrant", "Q2"),
        )
        cnt += 1
    return cnt

def toggle_todo(todo_id: str):
    for t in st.session_state.todos:
        if t.id == todo_id:
            t.is_done = not t.is_done
            return


def list_events() -> List[Event]:
    return st.session_state.events

def add_event(title: str, start, memo: str = "", linked_todo_id: Optional[str] = None) -> Event:
    e = Event(id=str(uuid.uuid4())[:8], title=title, start=start,
              memo=memo, linked_todo_id=linked_todo_id)
    st.session_state.events.append(e)
    return e

def add_events_from_todos(todos_with_due: List[Todo]) -> int:
    cnt = 0
    for t in todos_with_due:
        if t.due_date is None:
            continue
        add_event(
            title=t.title,
            start=t.due_date,
            memo=f"[auto] source: {t.source}",
            linked_todo_id=t.id,
        )
        cnt += 1
    return cnt


def set_briefing(text: str):
    st.session_state.current_briefing = text

def get_briefing() -> Optional[str]:
    return st.session_state.get("current_briefing")
