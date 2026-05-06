"""⚙️ 설정 페이지

🔌 사용하는 함수: 없음 (st.session_state.settings 직접 수정)

📐 화면 구조: 2×2 카드 (프로필 / 이메일 / 알림 / 보안)
"""
import streamlit as st

from core import store

st.set_page_config(page_title="설정 · 에이블", page_icon="⚙️", layout="wide")

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
st.title("설정")
st.caption("계정·이메일·음성·알림 설정을 관리합니다.")

st.write("")

user = store.current_user()
settings = st.session_state.settings


# ===== 2x2 카드 =====
r1c1, r1c2 = st.columns(2)
r2c1, r2c2 = st.columns(2)


# 프로필
with r1c1:
    with st.container(border=True):
        st.subheader("👤 프로필")
        with st.form("profile_form"):
            name = st.text_input("이름", value=user.name)
            email = st.text_input("이메일", value=user.email)
            team = st.text_input("소속", value=user.team)
            if st.form_submit_button("저장", type="primary"):
                user.name = name
                user.email = email
                user.team = team
                st.toast("프로필 저장됨", icon="✅")


# 이메일 발송
with r1c2:
    with st.container(border=True):
        st.subheader("📧 이메일 발송 기본값")
        with st.form("email_form"):
            default_to = st.text_input("기본 수신자", value=settings["default_to"])
            cc = st.text_input("참조 (CC)", value=settings["cc"])
            sig = st.text_area("서명", value=settings["signature"], height=80)
            if st.form_submit_button("저장", type="primary"):
                settings["default_to"] = default_to
                settings["cc"] = cc
                settings["signature"] = sig
                st.toast("이메일 설정 저장됨", icon="✅")


# 알림
with r2c1:
    with st.container(border=True):
        st.subheader("🔔 알림")
        notify_due = st.toggle("마감 임박 알림 (D-1)", value=settings["notify_due"])
        notify_meeting = st.toggle("회의 분석 완료 알림", value=settings["notify_meeting"])
        notify_briefing = st.toggle("매일 아침 브리핑 (09:00)", value=settings["notify_briefing"])
        settings["notify_due"] = notify_due
        settings["notify_meeting"] = notify_meeting
        settings["notify_briefing"] = notify_briefing


# 보안
with r2c2:
    with st.container(border=True):
        st.subheader("🔒 보안")
        with st.form("pw_form"):
            old = st.text_input("현재 비밀번호", type="password")
            new = st.text_input("새 비밀번호", type="password")
            new2 = st.text_input("새 비밀번호 확인", type="password")
            if st.form_submit_button("비밀번호 변경", type="primary"):
                if not old or not new:
                    st.error("입력값을 확인해주세요.")
                elif len(new) < 6:
                    st.error("새 비밀번호는 6자 이상이어야 합니다.")
                elif new != new2:
                    st.error("새 비밀번호가 서로 다릅니다.")
                else:
                    st.toast("비밀번호 변경됨 (mock)", icon="🔒")

        st.divider()
        if st.button("로그아웃", use_container_width=True):
            st.session_state.clear()
            st.switch_page("app.py")
