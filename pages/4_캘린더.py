"""📅 캘린더 페이지

🔌 사용하는 함수: 없음 (store에서 event CRUD)

📐 화면 구조: 월간 7×N 그리드 + 일정 추가 모달
"""
import calendar as cal_mod
from datetime import date, datetime
import streamlit as st

from core import store
from core.models import Event

st.set_page_config(page_title="캘린더 · 에이블", page_icon="📅", layout="wide")

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
    st.title("캘린더")
    st.caption("기한 있는 업무가 자동으로 등록됩니다.")
with hr:
    st.write("")
    if st.button("+ 일정 추가", type="primary", use_container_width=True):
        st.session_state["show_add_event"] = True


# ===== 모달 =====
@st.dialog("🗓 일정 추가")
def add_event_dialog():
    title = st.text_input("제목")
    d = st.date_input("날짜", value=date.today())
    t = st.time_input("시간", value=datetime.now().time().replace(second=0, microsecond=0))
    memo = st.text_area("메모")
    c1, c2 = st.columns(2)
    if c1.button("취소", use_container_width=True):
        st.session_state["show_add_event"] = False
        st.rerun()
    if c2.button("추가", type="primary", use_container_width=True):
        if not title:
            st.error("제목은 필수입니다.")
        else:
            store.add_event(title=title, start=datetime.combine(d, t), memo=memo)
            st.toast("일정 등록됨", icon="📅")
            st.session_state["show_add_event"] = False
            st.rerun()


if st.session_state.get("show_add_event"):
    add_event_dialog()


# ===== 월 이동 컨트롤 =====
if "cal_year" not in st.session_state:
    st.session_state.cal_year = date.today().year
    st.session_state.cal_month = date.today().month

navc1, navc2, navc3, navc4, navc5 = st.columns([1, 1, 3, 1, 8])
with navc1:
    if st.button("◀", use_container_width=True):
        if st.session_state.cal_month == 1:
            st.session_state.cal_month = 12
            st.session_state.cal_year -= 1
        else:
            st.session_state.cal_month -= 1
        st.rerun()
with navc2:
    if st.button("▶", use_container_width=True):
        if st.session_state.cal_month == 12:
            st.session_state.cal_month = 1
            st.session_state.cal_year += 1
        else:
            st.session_state.cal_month += 1
        st.rerun()
with navc3:
    st.markdown(
        f"### {st.session_state.cal_year}년 {st.session_state.cal_month}월",
    )
with navc4:
    if st.button("오늘", use_container_width=True):
        st.session_state.cal_year = date.today().year
        st.session_state.cal_month = date.today().month
        st.rerun()


# ===== 캘린더 그리드 =====
year, month = st.session_state.cal_year, st.session_state.cal_month
month_cal = cal_mod.Calendar(firstweekday=6).monthdayscalendar(year, month)  # 일요일 시작

# 일정 → 일자 매핑
events_by_day = {}
for e in store.list_events():
    if isinstance(e.start, datetime):
        d = e.start.date()
    else:
        d = e.start
    if d.year == year and d.month == month:
        events_by_day.setdefault(d.day, []).append(e)
# To-Do의 due도 일정처럼 표시
for t in store.list_todos():
    if t.due_date and t.due_date.year == year and t.due_date.month == month:
        events_by_day.setdefault(t.due_date.day, []).append(
            Event(id=f"todo_{t.id}", title=f"📌 {t.title}", start=t.due_date)
        )

# 요일 헤더
week_days = ["일", "월", "화", "수", "목", "금", "토"]
hdr = st.columns(7, gap="small")
for i, w in enumerate(week_days):
    with hdr[i]:
        color = "#dc2626" if w == "일" else ("#2563eb" if w == "토" else "#4b5563")
        st.markdown(
            f"<div style='text-align:center;font-weight:600;color:{color};padding:0px;"
            f"background:#f9fafb;border-bottom:1px solid #e5e7eb;'>{w}</div>",
            unsafe_allow_html=True,
        )

today = date.today()
for week in month_cal:
    week_cols = st.columns(7, gap="small")
    for i, day in enumerate(week):
        with week_cols[i]:
            if day == 0:
                st.markdown("<div style='min-height:90px;background:#fafafa;'></div>",
                            unsafe_allow_html=True)
                continue
            is_today = (year == today.year and month == today.month and day == today.day)
            day_style = (
                "background:#2563eb;color:white;border-radius:50%;"
                "width:22px;height:22px;display:inline-flex;"
                "align-items:center;justify-content:center;font-size:12px;font-weight:600;"
                if is_today
                else "font-weight:600;font-size:12px;color:#111827;"
            )
            evs = events_by_day.get(day, [])
            ev_html = ""
            for ev in evs[:3]:
                ev_html += (
                    f"<div style='background:#eff6ff;color:#2563eb;font-size:11px;"
                    f"padding:2px 6px;border-radius:4px;margin-top:2px;"
                    f"white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>"
                    f"{ev.title}</div>"
                )
            if len(evs) > 3:
                ev_html += f"<div style='font-size:10px;color:#9ca3af;margin-top:2px;'>+ {len(evs)-3}건</div>"

            st.markdown(
                f"""<div style='min-height:90px;border-bottom:1px solid #e5e7eb;
                                border-right:1px solid #e5e7eb;padding:6px;border: 1px solid #e5e7eb;
                                margin-left: -1px; margin-right: -1px;'>
                  <span style='{day_style}'>{day}</span>
                  {ev_html}
                  """,
                unsafe_allow_html=True,
            )

st.write("")
st.caption("· 회의 분석에서 ‘→ 캘린더 등록’을 누르거나, To-Do 페이지에서 📅 아이콘을 누르면 자동 등록됩니다.")
