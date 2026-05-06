"""OpenAI wrapper — analyze_meeting / stt / tts / chat_with_tools / chat"""
import streamlit as st
from datetime import date, timedelta, datetime
from .models import AnalysisResult


def _client():
    from openai import OpenAI
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    return OpenAI(api_key=api_key)


def _has_api_key() -> bool:
    return bool(st.secrets.get("OPENAI_API_KEY", ""))


# ───────────────────────────── 회의 분석 ─────────────────────────────
def analyze_meeting(text: str, meeting_id: str = "tmp") -> AnalysisResult:
    if not _has_api_key():
        return _mock_analysis(meeting_id)

    import json

    from datetime import date as _date
    today_str = _date.today().isoformat()  # 예: 2026-05-06

    sys_role = (
        f"You are Able, the personal assistant of Kim Daeri.\n"
        f"Today is {today_str}. All due dates must be AFTER today ({today_str}).\n"
        "Analyze the meeting content and respond ONLY in JSON format:\n"
        "{\"title\":\"brief meeting title (max 20 chars)\","
        "\"summary\":\"one paragraph summary in Korean\","
        "\"decisions\":[\"decision1\"],"
        "\"personal_impact\":[{\"title\":\"task title\",\"due\":\"YYYY-MM-DD\",\"quadrant\":\"Q1\"}],"
        "\"open_questions\":[\"question1\"]}"
        "\nquadrant: Q1=urgent+important, Q2=important+not urgent, Q3=urgent+not important, Q4=neither"
        "\nAll text must be in Korean. Due dates must use the correct current year."
    )

    response = _client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": sys_role},
            {"role": "user", "content": f"[Meeting Content]\n{text}"},
        ],
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)

    for item in data.get("personal_impact", []):
        if isinstance(item.get("due"), str):
            try:
                item["due"] = datetime.strptime(item["due"], "%Y-%m-%d").date()
            except ValueError:
                item["due"] = None

    result = AnalysisResult(
        meeting_id=meeting_id,
        summary=data.get("summary", ""),
        decisions=data.get("decisions", []),
        personal_impact=data.get("personal_impact", []),
        open_questions=data.get("open_questions", []),
    )
    result._title = data.get("title", "")
    return result


# ───────────────────────────── STT ─────────────────────────────
def stt(audio_bytes: bytes) -> str:
    if not _has_api_key():
        return "(demo) OPENAI_API_KEY를 secrets.toml에 등록하세요."

    import io
    f = io.BytesIO(audio_bytes)
    f.name = "recording.m4a"
    transcript = _client().audio.transcriptions.create(model="whisper-1", file=f)
    return transcript.text


# ───────────────────────────── TTS ─────────────────────────────
def tts(text: str, voice: str = "alloy") -> bytes:
    if not _has_api_key():
        return b""
    speech = _client().audio.speech.create(model="tts-1", voice=voice, input=text)
    return speech.read()


# ───────────────────────────── 멀티턴 채팅 ─────────────────────────────
def chat(messages: list, sys_role: str = "") -> str:
    if not _has_api_key():
        return "(demo) OPENAI_API_KEY를 등록하면 실제 AI 응답을 받을 수 있습니다."

    full_messages = []
    if sys_role:
        full_messages.append({"role": "system", "content": sys_role})
    full_messages.extend(messages)

    response = _client().chat.completions.create(
        model="gpt-4o-mini",
        messages=full_messages,
    )
    return response.choices[0].message.content or ""


# ───────────────────────────── Tool Calling ─────────────────────────────
def chat_with_tools(prompt: str, sys_role: str, tools: list, dispatcher: dict) -> str:
    if not _has_api_key():
        return "(demo) OPENAI_API_KEY를 등록하세요."

    import json as _json

    response = _client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": sys_role},
            {"role": "user", "content": prompt},
        ],
        tools=tools,
        tool_choice="auto",
    )

    message = response.choices[0].message
    tool_calls = message.tool_calls or []

    if not tool_calls:
        return message.content or ""

    tool_results = []
    for tool in tool_calls:
        args = _json.loads(tool.function.arguments)
        func = dispatcher.get(tool.function.name)
        result = func(**args) if func else {"status": "error"}
        tool_results.append({
            "tool_call_id": tool.id,
            "role": "tool",
            "name": tool.function.name,
            "content": _json.dumps(result, ensure_ascii=False),
        })

    final = _client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": sys_role},
            {"role": "user", "content": prompt},
            message,
            *tool_results,
        ],
    )
    return final.choices[0].message.content or ""


# ───────────────────────────── Mock ─────────────────────────────
def _mock_analysis(meeting_id: str) -> AnalysisResult:
    today = date.today()
    result = AnalysisResult(
        meeting_id=meeting_id,
        summary="(demo) secrets.toml에 OPENAI_API_KEY를 등록하면 실제 분석 결과가 표시됩니다.",
        decisions=["(demo) example decision"],
        personal_impact=[{"title": "(demo) example task", "due": today + timedelta(days=3), "quadrant": "Q2"}],
        open_questions=["(demo) example question"],
    )
    result._title = ""
    return result
