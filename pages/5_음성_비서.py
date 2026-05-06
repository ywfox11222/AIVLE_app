"""🎤 음성 비서 페이지 (미니 GPT 스타일 대화 UI)

🔌 사용하는 함수:
   - llm.tts(text, voice)
   - llm.stt(audio_bytes)
   - llm.chat(messages, sys_role)
   - email_sender.send_email(...)
"""
from datetime import date, timedelta
import streamlit as st

from core import store, llm, email_sender

st.set_page_config(page_title="음성 비서 · 에이블", page_icon="🎤", layout="wide")

store.init_state()
if not store.is_authed():
    st.warning("로그인이 필요합니다.")
    st.page_link("app.py", label="로그인 화면으로 →")
    st.stop()

if "voice_history" not in st.session_state:
    st.session_state["voice_history"] = []
if "voice_response_audio" not in st.session_state:
    st.session_state["voice_response_audio"] = None

# ───────────────────────────── CSS ─────────────────────────────
st.markdown("""
<style>
[data-testid="stSidebarNav"] { display: none !important; }

/* 채팅 컨테이너 최소 높이 */
.chat-area {
    min-height: 320px;
}

/* 컨텍스트 뱃지 */
.ctx-badge {
    display: inline-block;
    background: #eff6ff;
    color: #2563eb;
    border: 1px solid #bfdbfe;
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 12px;
    margin: 2px 3px;
}

/* 에이블 헤더 */
.able-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 16px 20px;
    background: linear-gradient(135deg, #1e3a8a, #2563eb);
    border-radius: 14px;
    color: white;
    margin-bottom: 8px;
}
.able-avatar {
    width: 44px; height: 44px;
    border-radius: 12px;
    background: rgba(255,255,255,0.2);
    display: flex; align-items: center; justify-content: center;
    font-size: 22px;
}
.able-name { font-weight: 700; font-size: 17px; }
.able-desc { font-size: 12px; opacity: .8; }
</style>
""", unsafe_allow_html=True)


# ───────────────────────────── 사이드바 ─────────────────────────────
def render_sidebar():
    user = store.current_user()
    with st.sidebar:
        st.markdown("""
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
        """, unsafe_allow_html=True)
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


# ───────────────────────────── 컨텍스트 빌더 ─────────────────────────────
def build_system_prompt() -> tuple[str, dict]:
    """에이블의 시스템 프롬프트 + 컨텍스트 요약 반환"""
    user = store.current_user()
    today = date.today()

    # 회의 분석 수집 (최대 10건, 결정사항·개인영향·질문 포함)
    meetings_ctx = ""
    meeting_count = 0
    for m in store.list_meetings()[-10:]:
        a = store.get_analysis(m.id)
        if a:
            decisions_str = "\n  - ".join(a.decisions) if a.decisions else "없음"
            impact_str = "\n  - ".join(
                f"{it['title']} ({it.get('quadrant','Q2')})" for it in a.personal_impact
            ) if a.personal_impact else "없음"
            questions_str = "\n  - ".join(a.open_questions) if a.open_questions else "없음"
            meetings_ctx += (
                f"\n[회의: {m.title} | {m.date.strftime('%Y.%m.%d %H:%M')}]"
                f"\n 요약: {a.summary}"
                f"\n 결정사항:\n  - {decisions_str}"
                f"\n 개인 할일:\n  - {impact_str}"
                f"\n 미확인 질문:\n  - {questions_str}\n"
            )
            meeting_count += 1

    # To-Do 수집
    todos_ctx = ""
    todo_list = store.list_todos()
    pending = [t for t in todo_list if not t.is_done]
    done_count = len([t for t in todo_list if t.is_done])
    for t in pending[:8]:
        due = t.due_date.strftime("%m/%d") if t.due_date else "마감 미정"
        overdue = " ⚠️ 기한초과" if (t.due_date and t.due_date < today) else ""
        todos_ctx += f"\n- [{t.quadrant}] {t.title} (마감: {due}){overdue}"

    # 캘린더 이벤트 수집 (7일 이내)
    events_ctx = ""
    event_count = 0
    for e in store.list_events():
        start = e.start if isinstance(e.start, date) else e.start.date()
        if today <= start <= today + timedelta(days=7):
            events_ctx += f"\n- {start.strftime('%m/%d')} {e.title}"
            event_count += 1

    # 시스템 프롬프트 조합
    sys_role = (
        f"당신은 에이블(Able), {user.name}님의 AI 개인비서입니다. 오늘은 {today.strftime('%Y년 %m월 %d일')}입니다.\n"
        "친절하고 간결하게 한국어로 답변하세요. 특별한 이유가 없으면 3문장 이내로 답하세요.\n"
        "아래는 당신이 알고 있는 {user.name}님의 업무 현황입니다.\n"
    )
    if meetings_ctx:
        sys_role += f"\n=== 최근 회의 분석 ===\n{meetings_ctx}"
    if todos_ctx:
        sys_role += f"\n=== 현재 할 일 (미완료 {len(pending)}건, 완료 {done_count}건) ==={todos_ctx}\n"
    if events_ctx:
        sys_role += f"\n=== 향후 7일 일정 (총 {event_count}건) ==={events_ctx}\n"
    if not meetings_ctx and not todos_ctx and not events_ctx:
        sys_role += "\n(현재 등록된 회의, 할 일, 일정이 없습니다. 회의 분석이나 To-Do를 먼저 추가해보세요.)"

    ctx_summary = {
        "meetings": meeting_count,
        "todos_pending": len(pending),
        "events": event_count,
    }
    return sys_role, ctx_summary


# ───────────────────────────── 레이아웃: 좌(채팅) + 우(컨트롤) ─────────────────────────────
col_chat, col_ctrl = st.columns([3, 1], gap="large")


with col_ctrl:
    # 에이블 프로필 카드
    st.markdown("""
    <div class="able-header">
      <div class="able-avatar">🤖</div>
      <div>
        <div class="able-name">에이블</div>
        <div class="able-desc">AI 개인비서</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # 컨텍스트 현황
    _, ctx = build_system_prompt()
    st.markdown("**📚 알고 있는 정보**")
    st.markdown(
        f'''<span class="ctx-badge">📝 회의 {ctx["meetings"]}건</span>
<span class="ctx-badge">✅ 할일 {ctx["todos_pending"]}건</span>
<span class="ctx-badge">📅 일정 {ctx["events"]}건</span>''',
        unsafe_allow_html=True,
    )
    st.caption("회의 분석·To-Do·캘린더의 실제 데이터를 기반으로 답합니다.")
    st.write("")

    # 음성 설정
    st.markdown("**🔊 음성 설정**")
    voice = st.selectbox("TTS 음성", ["alloy", "nova", "onyx"],
                         index=["alloy", "nova", "onyx"].index(
                             st.session_state.settings.get("voice", "alloy")))
    st.session_state.settings["voice"] = voice

    tts_on = st.toggle("응답 자동 음성 재생", value=True)

    st.write("")

    # 오늘의 브리핑
    with st.expander("📢 오늘의 브리핑", expanded=False):
        briefing = store.get_briefing() or (
            f"{store.current_user().name}님, 좋은 아침입니다. "
            "오늘의 일정과 마감 임박 업무를 안내드립니다."
        )
        st.write(briefing)
        if st.button("▶ 브리핑 듣기", use_container_width=True):
            with st.spinner("TTS 합성 중..."):
                ab = llm.tts(briefing, voice=voice)
                st.session_state["voice_response_audio"] = ab
            st.rerun()

    st.write("")

    # 듣기 큐
    with st.expander("🎧 듣기 큐", expanded=False):
        queue = []
        for m in store.list_meetings()[:3]:
            a = store.get_analysis(m.id)
            if a:
                queue.append({"title": m.title, "text": a.summary})
        urgent = [t for t in store.list_todos()
                  if not t.is_done and t.due_date and t.due_date <= date.today()]
        if urgent:
            queue.append({
                "title": "오늘 마감 To-Do",
                "text": "오늘 마감인 업무는 " + ", ".join(t.title for t in urgent) + " 입니다.",
            })
        if not queue:
            st.caption("큐가 비어있습니다.")
        for i, item in enumerate(queue):
            c1, c2 = st.columns([3, 1])
            c1.caption(item["title"])
            if c2.button("▶", key=f"q_{i}"):
                store.set_briefing(item["text"])
                st.rerun()

    st.write("")

    # 초기화 + 이메일
    if st.button("🗑 대화 초기화", use_container_width=True):
        st.session_state["voice_history"] = []
        st.session_state["voice_response_audio"] = None
        st.rerun()
    if st.button("📧 브리핑 이메일 발송", use_container_width=True):
        st.session_state["voice_show_email"] = True


# ───────────────────────────── 채팅 영역 ─────────────────────────────
with col_chat:
    st.markdown("### 💬 에이블과 대화하기")
    st.caption(f"오늘 {date.today().strftime('%Y.%m.%d')} · 회의 분석·할 일·캘린더 정보를 바탕으로 답합니다.")
    st.divider()

    # 대화 히스토리 렌더링 (st.chat_message 사용)
    history = st.session_state["voice_history"]

    if not history:
        with st.chat_message("assistant"):
            st.markdown(
                f"안녕하세요, **{store.current_user().name}**님! 저는 에이블이에요. 🙂\n\n"
                "회의 내용 요약, 할 일 현황, 일정 확인 등 무엇이든 물어보세요. "
                "오른쪽에서 음성으로도 대화할 수 있어요."
            )
    else:
        for msg in history:
            with st.chat_message("user" if msg["role"] == "user" else "assistant"):
                st.markdown(msg["content"])

    # 마지막 응답 오디오 재생
    if st.session_state.get("voice_response_audio") and tts_on:
        st.audio(st.session_state["voice_response_audio"], format="audio/mp3", autoplay=True)

    # ── 음성 입력 ──
    st.write("")
    with st.container(border=True):
        st.markdown("**🎤 음성으로 질문**")
        v1, v2 = st.columns([4, 1])
        with v1:
            audio_input = st.audio_input("마이크를 눌러 녹음", key="voice_mic", label_visibility="collapsed")
        with v2:
            send_voice = st.button("전송", key="send_voice_btn", use_container_width=True, type="primary")

    # ── 텍스트 입력 (st.chat_input — 하단 고정) ──
    text_prompt = st.chat_input("텍스트로 질문하기...")


# ───────────────────────────── 메시지 처리 ─────────────────────────────
user_prompt = ""

# 음성 → STT
if send_voice and audio_input is not None:
    with st.spinner("🎙 음성 인식 중..."):
        audio_bytes = audio_input.getvalue()
        user_prompt = llm.stt(audio_bytes)
    if user_prompt:
        with col_chat:
            st.info(f"🎙 **인식된 내용:** {user_prompt}")

# 텍스트 입력
if text_prompt and text_prompt.strip():
    user_prompt = text_prompt.strip()

# LLM 응답
if user_prompt:
    sys_role, _ = build_system_prompt()
    history = st.session_state["voice_history"]
    history.append({"role": "user", "content": user_prompt})

    # 최대 20개 메시지 유지
    if len(history) > 20:
        history = history[-20:]

    with st.spinner("🤖 에이블이 생각 중..."):
        response_text = llm.chat(history, sys_role=sys_role)

    history.append({"role": "assistant", "content": response_text})
    st.session_state["voice_history"] = history

    # TTS
    if tts_on:
        with st.spinner("🔊 음성 합성 중..."):
            voice_setting = st.session_state.settings.get("voice", "alloy")
            response_audio = llm.tts(response_text, voice=voice_setting)
            st.session_state["voice_response_audio"] = response_audio
    else:
        st.session_state["voice_response_audio"] = None

    st.rerun()


# ───────────────────────────── 이메일 모달 ─────────────────────────────
briefing_text = store.get_briefing() or (
    f"{store.current_user().name}님, 좋은 아침입니다. 오늘의 일정을 안내드립니다."
)

@st.dialog("📧 음성 브리핑 이메일 발송")
def voice_email_dialog():
    settings = st.session_state.settings
    to = st.text_input("받는 사람", value=settings["default_to"])
    subject = st.text_input("제목", value="[에이블] 오늘의 브리핑")
    body = st.text_area("본문", value=f"{briefing_text}\n\n{settings['signature']}", height=200)
    c1, c2 = st.columns(2)
    if c1.button("취소", use_container_width=True):
        st.session_state["voice_show_email"] = False
        st.rerun()
    if c2.button("전송", type="primary", use_container_width=True):
        result = email_sender.send_email(to, subject, body)
        if result["status"] in ("success", "mock"):
            st.toast("이메일 전송 완료", icon="📧")
        else:
            st.toast(f"전송 실패: {result.get('error','')}", icon="⚠️")
        st.session_state["voice_show_email"] = False
        st.rerun()

if st.session_state.get("voice_show_email"):
    voice_email_dialog()
