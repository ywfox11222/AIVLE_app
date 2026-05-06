"""🚪 에이블 — 진입점 (로그인 화면)

흐름:
   1. session_state 초기화 (한 번만)
   2. 이미 로그인된 상태면 → 바로 대시보드로
   3. 아니면 → 로그인 폼 표시 → 인증 성공 시 대시보드로

📍 다음 단계 페이지: pages/1_대시보드.py
"""
import streamlit as st

from core import store, auth


# ===== 페이지 메타 =====
st.set_page_config(
    page_title="에이블 · AI 개인비서",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed",  # 로그인 화면에서는 사이드바 숨김
)

# 로그인 화면 전용 — 사이드바 + 입력칸 안내문구 숨김
st.markdown(
    """
    <style>
      [data-testid="stSidebar"] { display: none !important; }
      [data-testid="stSidebarCollapsedControl"] { display: none !important; }
      [data-testid="InputInstructions"] { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# 1) 상태 초기화
store.init_state()

# 2) 이미 로그인돼 있으면 바로 대시보드로 이동
if store.is_authed():
    st.switch_page("pages/1_대시보드.py")


# ===== 로그인 화면 =====
# 가운데 정렬을 위해 columns로 양옆 여백
left, center, right = st.columns([1, 2, 1])

with center:
    st.markdown("<br>", unsafe_allow_html=True)

    # 로고 + 타이틀
    st.markdown(
        """
        <div style='display:flex; flex-direction:column; align-items:center;'>
          <div style='width:64px; height:64px;
                      border-radius:14px;
                      background: linear-gradient(135deg, #2563EB, #60A5FA);
                      color:white; font-size:28px; font-weight:700;
                      margin-bottom:12px;
                      display:flex; align-items:center; justify-content:center;'>A</div>
          <div style='font-size: 2.2rem; font-weight: 700; ...'>에이블</div>
          <p style='color:#6b7280; margin-top:4px; text-align:center;'>AI 개인비서</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # 로그인 폼
    # st.form 으로 묶으면 엔터키로 submit 가능
    with st.form("login_form"):
        username = st.text_input("아이디", value="kim.daeri")
        password = st.text_input("비밀번호", type="password", value="demopass")
        submitted = st.form_submit_button("로그인", use_container_width=True, type="primary")

        if submitted:
            user = auth.authenticate(username, password)
            if user is None:
                st.error("아이디 또는 비밀번호가 일치하지 않습니다.")
            else:
                store.set_user(user)
                st.success(f"환영합니다, {user.name}님 ✨")
                # 사이드바를 다시 열고 대시보드로 이동
                st.switch_page("pages/1_대시보드.py")

    st.caption("AIVLE 3차 미프 /  DX 02반 4조")
