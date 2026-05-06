"""📊 대시보드 페이지

🔌 사용하는 함수: 없음 (store에서 데이터만 읽음)

📐 화면 구조: 인사 + 통계 카드 4개 + 마감임박/최근회의 + 다가오는 일정
"""
from datetime import date
import streamlit as st

from core import store

# ===== 페이지 메타 =====
st.set_page_config(page_title="대시보드 · 에이블", page_icon="📊", layout="wide")

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

# ===== 인증 가드 =====
# 모든 보호 페이지 상단에 동일하게 둔다.
# (없으면 URL 직접 접속으로 우회 가능)
store.init_state()
if not store.is_authed():
    st.warning("로그인이 필요합니다.")
    st.page_link("app.py", label="로그인 화면으로 →")
    st.stop()


# ===== 사이드바 (모든 페이지에 공통) =====
def render_sidebar():
    st.markdown(
        """<style>[data-testid="stSidebarNav"] { display: none !important; }</style>""",
        unsafe_allow_html=True,
    )
    user = store.current_user()
    with st.sidebar:
        st.markdown(
            f"""
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


# ===== 본문 =====
user = store.current_user()
today_str = date.today().strftime("%Y년 %m월 %d일 %A")

# 페이지 헤더 — 인사말 + 우측 액션
head_l, head_r = st.columns([3, 1])
with head_l:
    st.title(f"안녕하세요, {user.name}님 👋")
    st.caption(f"{today_str} · 오늘의 업무 한눈에 보기")
with head_r:
    st.write("")  # 수직 정렬용
    if st.button("▶ 오늘의 브리핑 듣기", type="primary", use_container_width=True):
        # 음성 비서 페이지로 이동하면서 브리핑 텍스트 세팅
        store.set_briefing(
            f"{user.name}님, 좋은 아침입니다. "
            f"오늘 마감 업무는 총 {sum(1 for t in store.list_todos() if t.due_date == date.today() and not t.is_done)}건이며, "
            f"가장 시급한 것은 Q2 마케팅 제안서 초안입니다."
        )
        st.switch_page("pages/5_음성_비서.py")

st.write("")  # spacing


# ----- 통계 카드 4개 -----
todos = store.list_todos()
today_due = [t for t in todos if t.due_date == date.today() and not t.is_done]
not_done = [t for t in todos if not t.is_done]
meetings = store.list_meetings()
events = store.list_events()

c1, c2, c3, c4 = st.columns(4)
with c1:
    with st.container(border=True):
        st.caption("오늘 마감 업무")
        st.markdown(f"<h2 style='color:#dc2626;margin:0'>{len(today_due)}</h2>",
                    unsafe_allow_html=True)
        st.caption(f"전일 대비 +1")
with c2:
    with st.container(border=True):
        st.caption("미완료 업무")
        st.markdown(f"<h2 style='margin:0'>{len(not_done)}</h2>", unsafe_allow_html=True)
        st.caption(f"중요도 높음 {sum(1 for t in not_done if t.quadrant == 'Q1')}건")
with c3:
    with st.container(border=True):
        st.caption("이번주 회의")
        st.markdown(f"<h2 style='margin:0'>{len(meetings)}</h2>", unsafe_allow_html=True)
        st.caption(f"분석 완료 {len(store.list_meetings())}건")
with c4:
    with st.container(border=True):
        st.caption("캘린더 일정")
        st.markdown(f"<h2 style='margin:0'>{len(events)}</h2>", unsafe_allow_html=True)
        st.caption("이번주")

st.write("")


# ----- 마감 임박 To-Do + 최근 회의 분석 (2분할) -----
left, right = st.columns(2)

with left:
    with st.container(border=True):
        st.subheader("🔥 마감 임박 업무")
        st.caption("3일 내 마감 + 미완료")

        from datetime import timedelta
        urgent = [t for t in not_done
                  if t.due_date and t.due_date <= date.today() + timedelta(days=3)]
        urgent.sort(key=lambda t: t.due_date or date.today())

        if not urgent:
            st.info("마감 임박 업무가 없습니다 🎉")
        for t in urgent[:5]:
            tc1, tc2 = st.columns([1, 12])
            with tc1:
                if st.checkbox("", key=f"dash_chk_{t.id}", value=t.is_done):
                    if not t.is_done:
                        store.toggle_todo(t.id)
                        st.rerun()
            with tc2:
                d_day = (t.due_date - date.today()).days
                d_label = "D-0" if d_day == 0 else (f"D+{-d_day}" if d_day < 0 else f"D-{d_day}")
                st.markdown(
                    f"**{t.title}**  "
                    f"<span style='color:#9ca3af;font-size:12px;'>· {t.source} · {d_label}</span>",
                    unsafe_allow_html=True,
                )

        st.write("")
        st.page_link("pages/3_To-Do_관리.py", label="전체 보기 →")

with right:
    with st.container(border=True):
        st.subheader("📋 최근 회의 분석")
        st.caption("최근 7일")

        for m in meetings[:5]:
            with st.container(border=True):
                mc1, mc2 = st.columns([5, 1])
                with mc1:
                    st.markdown(f"**{m.title}**")
                    st.caption(f"{m.date.strftime('%Y.%m.%d')} · {m.duration_min}분")
                with mc2:
                    if st.button("열기", key=f"open_m_{m.id}"):
                        st.session_state.current_meeting_id = m.id
                        st.switch_page("pages/2_회의_분석.py")

        st.write("")
        st.page_link("pages/2_회의_분석.py", label="새 회의 분석 →")


st.write("")


# ----- 다가오는 일정 -----
with st.container(border=True):
    st.subheader("🗓 다가오는 일정")
    cols = st.columns(3)
    for i, e in enumerate(events[:3]):
        with cols[i]:
            with st.container(border=True):
                st.caption(e.start.strftime("%m월 %d일 %H:%M"))
                st.markdown(f"**{e.title}**")
                st.caption(e.memo)
