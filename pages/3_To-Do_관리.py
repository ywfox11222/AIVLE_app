"""✅ To-Do 관리 페이지

🔌 사용하는 함수: 없음 (store에서 todo CRUD)

📐 화면 구조: 필터바 + 리스트뷰 ↔ 아이젠하워 4분면 매트릭스 토글
"""
from datetime import date, timedelta
import streamlit as st

from core import store
from core.models import QUADRANT_LABELS

st.set_page_config(page_title="To-Do · 에이블", page_icon="✅", layout="wide")

# 컨테이너 일관된 높이 설정
st.markdown(
    """
    <style>
    div[data-testid="stVerticalBlock"] > div:has(> div[data-testid="stContainer"]) {
        min-height: 200px;
    }
    div[data-testid="stContainer"] {
        min-height: 200px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

store.init_state()
if not store.is_authed():
    st.warning("로그인이 필요합니다.")
    st.page_link("app.py", label="로그인 화면으로 →")
    st.stop()


def render_sidebar():
    st.markdown(
        """<style>[data-testid="stSidebarNav"] { display: none !important; }</style>""",
        unsafe_allow_html=True,
    )
    user = store.current_user()
    with st.sidebar:
        st.markdown(
            """
            <div style='padding:8px 4px 16px; border-bottom:1px solid #e5e7eb;'>
              <div style='display:flex; align-items:center; gap:10px;'>
                <div style='width:32px;height:32px;border-radius:8px;
                           background:linear-gradient(135deg,#2563EB,#60A5FA);
                           color:white;display:flex;align-items:center;justify-content:center;
                           font-weight:700;'>A</div>
                <div>
                  <div style='font-weight:700;'>에이블</div>
                  <div style='font-size:11px;color:#9ca3af;'>AI 개인비서</div>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("메인")
        st.page_link("pages/1_대시보드.py", label="대시보드", icon="📊")
        st.page_link("pages/2_회의_분석.py", label="회의 분석", icon="📝")
        st.page_link("pages/3_To-Do_관리.py", label="To-Do 관리", icon="✅")
        st.page_link("pages/4_캘린더.py", label="캘린더", icon="📅")
        st.page_link("pages/5_음성_비서.py", label="음성 비서", icon="🎤")
        st.caption("기타")
        st.page_link("pages/6_설정.py", label="설정", icon="⚙️")
        st.divider()
        st.markdown(f"**{user.name}**  \n{user.email}")
        if st.button("로그아웃", use_container_width=True):
            st.session_state.clear()
            st.switch_page("app.py")


render_sidebar()


# ===== 헤더 =====
hl, hr = st.columns([3, 1])
with hl:
    st.title("To-Do 관리")
    st.caption("회의에서 자동 추출된 업무를 아이젠하워 매트릭스로 분류하고 관리합니다.")
with hr:
    st.write("")
    if st.button("+ 직접 추가", type="primary", use_container_width=True):
        st.session_state["show_add_todo"] = True


# ===== 직접 추가 모달 =====
@st.dialog("➕ 새 To-Do 추가")
def add_todo_dialog():
    title = st.text_input("제목", "")
    due = st.date_input("마감일", value=date.today())
    quadrant = st.selectbox("중요도 (아이젠하워)",
                            ["Q1", "Q2", "Q3", "Q4"],
                            format_func=lambda q: f"{q} - {QUADRANT_LABELS[q]}")
    memo = st.text_area("메모", "")
    c1, c2 = st.columns(2)
    if c1.button("취소", use_container_width=True):
        st.session_state["show_add_todo"] = False
        st.rerun()
    if c2.button("추가", type="primary", use_container_width=True):
        if not title:
            st.error("제목은 필수입니다.")
        else:
            store.add_todo(title=title, due_date=due, quadrant=quadrant, memo=memo, source="직접 추가")
            st.session_state["show_add_todo"] = False
            st.toast("추가됨", icon="✅")
            st.rerun()


if st.session_state.get("show_add_todo"):
    add_todo_dialog()


st.write("")


# ===== 필터 바 =====
with st.container(border=True):
    f1, f2, f3, f4, f5 = st.columns([3, 2, 2, 2, 3])
    with f1:
        keyword = st.text_input("🔍 키워드 검색", placeholder="예: 제안서, 데모", label_visibility="collapsed")
    with f2:
        due_filter = st.selectbox("마감", ["전체 마감", "오늘", "3일 내", "이번주", "지연"], label_visibility="collapsed")
    with f3:
        quad_filter = st.selectbox("중요도", ["전체 중요도", "Q1 - 긴급+중요", "Q2 - 중요·여유", "Q3 - 위임", "Q4 - 나중에"], label_visibility="collapsed")
    with f4:
        status_filter = st.selectbox("상태", ["미완료만", "전체", "완료"], label_visibility="collapsed")
    with f5:
        view = st.radio("뷰", ["📋 리스트", "🟦 매트릭스"], horizontal=True, label_visibility="collapsed")


# ===== 필터 적용 =====
def apply_filters(todos):
    out = list(todos)
    if keyword:
        out = [t for t in out if keyword in t.title or keyword in (t.memo or "")]
    if due_filter == "오늘":
        out = [t for t in out if t.due_date == date.today()]
    elif due_filter == "3일 내":
        out = [t for t in out if t.due_date and t.due_date <= date.today() + timedelta(days=3)]
    elif due_filter == "이번주":
        out = [t for t in out if t.due_date and t.due_date <= date.today() + timedelta(days=7)]
    elif due_filter == "지연":
        out = [t for t in out if t.due_date and t.due_date < date.today() and not t.is_done]
    if quad_filter != "전체 중요도":
        q = quad_filter.split(" - ")[0]
        out = [t for t in out if t.quadrant == q]
    if status_filter == "미완료만":
        out = [t for t in out if not t.is_done]
    elif status_filter == "완료":
        out = [t for t in out if t.is_done]
    return out


todos = apply_filters(store.list_todos())


# ===== 본문 =====
QUADRANT_COLORS = {"Q1": "#dc2626", "Q2": "#2563eb", "Q3": "#f59e0b", "Q4": "#9ca3af"}


def d_day_label(d):
    if d is None:
        return "—"
    diff = (d - date.today()).days
    if diff == 0:
        return "D-0"
    if diff < 0:
        return f"D+{-diff} (지연)"
    return f"D-{diff}"


if view.startswith("📋"):
    # ----- 리스트 뷰 -----
    if not todos:
        st.info("조건에 맞는 업무가 없습니다.")
    for t in todos:
        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns([1, 9, 2, 1, 1])
            with c1:
                if st.checkbox("", value=t.is_done, key=f"todo_chk_{t.id}",
                               label_visibility="collapsed"):
                    if not t.is_done:
                        store.toggle_todo(t.id)
                        st.rerun()
                else:
                    if t.is_done:
                        store.toggle_todo(t.id)
                        st.rerun()
            with c2:
                style = "text-decoration:line-through;color:#9ca3af;" if t.is_done else ""
                due_str = t.due_date.strftime("%m/%d") if t.due_date else "—"
                st.markdown(
                    f"<span style='{style}'><strong>{t.title}</strong></span>  "
                    f"<span style='color:#9ca3af;font-size:12px;'>· {t.source} · 마감 {due_str}</span>",
                    unsafe_allow_html=True,
                )
            with c3:
                color = QUADRANT_COLORS[t.quadrant]
                st.markdown(
                    f"<span style='background:{color};color:white;font-size:11px;"
                    f"padding:2px 8px;border-radius:8px;'>{t.quadrant}·{QUADRANT_LABELS[t.quadrant]}</span>",
                    unsafe_allow_html=True,
                )
            with c4:
                st.markdown(
                    f"<span style='color:#6b7280;font-size:12px;'>{d_day_label(t.due_date)}</span>",
                    unsafe_allow_html=True,
                )
            with c5:
                if st.button("📅", key=f"todo_cal_{t.id}", help="캘린더에 등록"):
                    if t.due_date:
                        store.add_event(title=t.title, start=t.due_date, memo=f"To-Do 연동", linked_todo_id=t.id)
                        st.toast("캘린더 등록됨", icon="📅")
                    else:
                        st.toast("마감일이 없습니다", icon="⚠️")
else:
    # ----- 매트릭스 뷰 -----
    quadrants = {"Q1": [], "Q2": [], "Q3": [], "Q4": []}
    for t in todos:
        quadrants[t.quadrant].append(t)

    r1c1, r1c2 = st.columns(2)
    r2c1, r2c2 = st.columns(2)
    layout = [
        (r1c1, "Q1", "긴급 + 중요", "즉시 처리"),
        (r1c2, "Q2", "중요 + 여유", "계획적으로"),
        (r2c1, "Q3", "긴급 + 덜중요", "위임"),
        (r2c2, "Q4", "덜중요 + 여유", "나중에"),
    ]
    for col, q, title, sub in layout:
        with col:
            with st.container(border=True):
                tc1, tc2 = st.columns([3, 2])
                with tc1:
                    color = QUADRANT_COLORS[q]
                    st.markdown(
                        f"<div style='border-top:3px solid {color};padding-top:6px;'>"
                        f"<strong>{q}. {title}</strong></div>",
                        unsafe_allow_html=True,
                    )
                with tc2:
                    st.caption(sub)
                items = quadrants[q]
                if not items:
                    st.caption("(없음)")
                for t in items:
                    style = "text-decoration:line-through;color:#9ca3af;" if t.is_done else ""
                    due_str = d_day_label(t.due_date)
                    st.markdown(
                        f"<div style='background:#f9fafb;border:1px solid #e5e7eb;"
                        f"border-radius:6px;padding:6px 10px;margin-top:4px;'>"
                        f"<span style='{style}'><strong>{t.title}</strong></span><br/>"
                        f"<span style='color:#9ca3af;font-size:11px;'>{due_str}</span>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
