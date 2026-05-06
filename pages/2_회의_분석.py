"""📝 회의 분석 페이지

🔌 사용하는 함수 (core/llm.py):
   - llm.analyze_meeting(text)  ← 노트북 미션 3 (회의 요약·결정·개인영향·질문)
   - llm.stt(audio_bytes)        ← 노트북 미션 4 (Whisper 음성→텍스트)

📐 화면 구조: 좌측 입력 패널 + 우측 결과 4분할 + 하단 액션바
"""
from datetime import date, datetime
import uuid
import streamlit as st

from core import store, llm, email_sender
from core.models import Meeting

st.set_page_config(page_title="회의 분석 · 에이블", page_icon="📝", layout="wide")

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

# 인증 가드
store.init_state()
if not store.is_authed():
    st.warning("로그인이 필요합니다.")
    st.page_link("app.py", label="로그인 화면으로 →")
    st.stop()


# ===== 사이드바 =====
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
st.title("회의 분석")
st.caption("음성·텍스트로 회의를 입력하면 요약·결정사항·개인 영향·확인 질문까지 자동 정리합니다.")

st.write("")


# ===== 본문: 좌측 입력 + 우측 결과 =====
left, right = st.columns([1, 2], gap="large")


# ---------- 좌측: 입력 ----------
with left:
    with st.container(border=True):
        st.subheader("① 회의 내용 입력")

        tab_rec, tab_file, tab_text = st.tabs(["🎙 녹음", "📎 파일", "⌨ 텍스트"])

        file_text = ""     # 파일 업로드에서 읽은 텍스트
        audio_data = None

        with tab_rec:
            # st.audio_input은 Streamlit 1.31+ 기본 위젯
            audio_data = st.audio_input("회의 녹음")
            st.caption("녹음 후 STT(Whisper)로 자동 변환됩니다.")

        with tab_file:
            uploaded = st.file_uploader(
                "오디오 또는 텍스트 파일",
                type=["m4a", "wav", "mp3", "txt"],
                help="음성 파일은 STT 변환, 텍스트는 그대로 사용",
            )
            if uploaded is not None:
                if uploaded.name.endswith(".txt"):
                    file_text = uploaded.read().decode("utf-8", errors="ignore")
                    st.success(f"텍스트 {len(file_text)}자 로드됨")
                else:
                    audio_data = uploaded.read()

        with tab_text:
            typed_text = st.text_area(
                "회의록을 직접 붙여넣으세요",
                height=180,
                placeholder="[발언자 1] 다음 분기 마케팅 방향성에 대해 …",
                key="meeting_text_input",
            )

        # 파일 텍스트 우선, 없으면 직접 입력 사용
        meeting_text = file_text or typed_text

        st.divider()

        st.markdown("**분석 옵션**")
        opt_personal = st.checkbox("김 대리 본인 영향만 강조", value=True)
        opt_extract = st.checkbox("To-Do 자동 추출", value=True)
        opt_voice = st.checkbox("분석 후 음성 브리핑으로 듣기", value=False)

        run = st.button("▶ 분석 시작", type="primary", use_container_width=True)


# ---------- 우측: 결과 ----------
def render_result(meeting_id: str):
    """저장된 분석 결과를 카드로 출력"""
    m = store.get_meeting(meeting_id)
    a = store.get_analysis(meeting_id)
    if a is None:
        with right:
            st.info("좌측에서 회의 내용을 입력하고 ‘분석 시작’을 눌러주세요.")
        return

    with right:
        # 메타 카드
        with st.container(border=True):
            mc1, mc2 = st.columns([4, 1])
            with mc1:
                st.markdown(f"### {m.title if m else '신규 회의'}")
                if m:
                    st.caption(f"{m.date.strftime('%Y.%m.%d %H:%M')} · {m.duration_min}분 · 참석자 {len(m.attendees)}명")
            with mc2:
                st.button("↻ 재분석", use_container_width=True, key="re_analyze")

        # 결과 4분할
        rc1, rc2 = st.columns(2)
        with rc1:
            with st.container(border=True):
                st.markdown("#### 📝 회의 요약")
                st.write(a.summary)
            with st.container(border=True):
                st.markdown("#### 👤 김 대리 개인 영향")
                for item in a.personal_impact:
                    due = item.get("due")
                    due_label = due.strftime("%m/%d") if due else "마감 미정"
                    quad = item.get("quadrant", "Q2")
                    badge_color = {"Q1": "#dc2626", "Q2": "#2563eb", "Q3": "#f59e0b", "Q4": "#9ca3af"}[quad]
                    st.markdown(
                        f"- **{item['title']}** "
                        f"<span style='background:{badge_color};color:white;"
                        f"font-size:10px;padding:2px 6px;border-radius:8px;'>{quad}</span> "
                        f"<span style='color:#9ca3af;font-size:11px;'>· 마감 {due_label}</span>",
                        unsafe_allow_html=True,
                    )

        with rc2:
            with st.container(border=True):
                st.markdown("#### ✅ 주요 결정사항")
                for d in a.decisions:
                    st.markdown(f"- {d}")
            with st.container(border=True):
                st.markdown("#### ❓ 추가 확인 필요 질문")
                for q in a.open_questions:
                    st.markdown(f"- {q}")

        st.write("")

        # 액션 바
        with st.container(border=True):
            ac1, ac2, ac3, ac4 = st.columns(4)
            with ac1:
                if st.button("→ To-Do로 보내기", type="primary", use_container_width=True):
                    n = store.add_todos_from_impact(a.personal_impact, source=(m.title if m else "회의 분석"))
                    st.toast(f"To-Do {n}건 추가됨", icon="✅")
            with ac2:
                if st.button("→ 캘린더 등록", use_container_width=True):
                    # 방금 추출된 To-Do 중 due 있는 것을 일정으로 등록
                    new_todos = [t for t in store.list_todos() if t.source == (m.title if m else "회의 분석") and t.due_date]
                    n = store.add_events_from_todos(new_todos)
                    st.toast(f"일정 {n}건 등록됨", icon="📅")
            with ac3:
                if st.button("→ 이메일 전송", use_container_width=True):
                    st.session_state["show_email_modal"] = True
            with ac4:
                if st.button("▶ 음성 브리핑", use_container_width=True):
                    store.set_briefing(a.summary)
                    st.switch_page("pages/5_음성_비서.py")


# ===== 분석 실행 =====
if run:
    # 텍스트가 비어 있으면 음성/파일에서 STT 변환
    if not meeting_text and audio_data is not None:
        with st.spinner("음성 인식 중 (Whisper STT)..."):
            audio_bytes = audio_data.getvalue() if hasattr(audio_data, "getvalue") else audio_data
            meeting_text = llm.stt(audio_bytes)

        # ── Step 3: STT 결과 화면 표시 (PDF 62쪽 핵심 기능) ──
        with left:
            st.info(f"🎙 **음성 인식 결과** (총 {len(meeting_text)}자)\n\n{meeting_text}")
        st.toast("음성 → 텍스트 변환 완료", icon="🎙")

    if not meeting_text:
        st.error("회의 내용을 입력하거나 녹음/업로드해주세요.")
    else:
        # STT가 아닌 텍스트 직접 입력일 때도 입력 내용 확인 표시
        if audio_data is None:
            with left:
                st.info(f"📄 **입력된 텍스트** (총 {len(meeting_text)}자)\n\n{meeting_text[:300]}{'…' if len(meeting_text) > 300 else ''}")

        with st.spinner("LLM이 회의를 분석 중입니다..."):
            new_id = str(uuid.uuid4())[:8]
            result = llm.analyze_meeting(meeting_text, meeting_id=new_id)
            store.save_analysis(result)
            st.session_state.current_meeting_id = new_id

            # Meeting 객체 생성 및 저장 (음성비서 컨텍스트용, 최대 10건)
            auto_title = getattr(result, "_title", "") or meeting_text[:30].replace("\n", " ") + "…"
            new_meeting = Meeting(
                id=new_id,
                title=auto_title,
                date=datetime.now(),
                duration_min=0,
                attendees=[],
                raw_text=meeting_text,
            )
            store.save_meeting(new_meeting)

        st.toast("분석 완료 ✨", icon="✨")
        if opt_voice:
            store.set_briefing(result.summary)
            st.switch_page("pages/5_음성_비서.py")
        st.rerun()


# 결과 렌더 — 분석 결과가 있을 때만 표시
current_mid = st.session_state.get("current_meeting_id")
if current_mid:
    render_result(current_mid)
else:
    with right:
        st.info("👈 좌측에서 회의 내용을 입력하고 '분석 시작'을 눌러주세요.")


# ===== 이메일 모달 =====
@st.dialog("📧 이메일 전송")
def email_dialog():
    a = store.get_analysis(st.session_state.get("current_meeting_id", "m1"))
    m = store.get_meeting(st.session_state.get("current_meeting_id", "m1"))
    settings = st.session_state.settings

    to = st.text_input("받는 사람", value=settings["default_to"])
    subject = st.text_input("제목", value=f"[에이블] {m.title if m else '회의'} 요약")
    default_body = (
        f"{store.current_user().name}님,\n\n"
        f"오늘 회의에서 결정된 사항과 배정된 업무를 정리하여 송부드립니다.\n\n"
        f"[요약]\n{a.summary if a else ''}\n\n"
        f"[결정사항]\n" + "\n".join(f"- {d}" for d in (a.decisions if a else [])) + "\n\n"
        f"{settings['signature']}"
    )
    body = st.text_area("본문", value=default_body, height=240)

    c1, c2 = st.columns(2)
    if c1.button("취소", use_container_width=True):
        st.session_state["show_email_modal"] = False
        st.rerun()
    if c2.button("전송", type="primary", use_container_width=True):
        result = email_sender.send_email(to, subject, body)
        if result["status"] in ("success", "mock"):
            st.toast("이메일 전송 완료 (또는 mock)", icon="📧")
        else:
            st.toast(f"전송 실패: {result.get('error','')}", icon="⚠️")
        st.session_state["show_email_modal"] = False
        st.rerun()


if st.session_state.get("show_email_modal"):
    email_dialog()
