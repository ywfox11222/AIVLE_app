"""이메일 발송 — 노트북 미션 1.

═══════════════════════════════════════════════════════════════
🧑‍💻 담당: ____________
═══════════════════════════════════════════════════════════════
✅ 이 파일은 노트북 미션 1 코드를 이미 적용해뒀습니다.
   → 따로 수정할 필요 없음. (단, 검증은 필요)

📌 검증 방법
  1. .streamlit/secrets.toml 에 SENDGRID_API_KEY, EMAIL_ADDRESS 입력
  2. streamlit run app.py 로 실행
  3. 음성 비서 페이지 → '📧 이메일로 발송' 버튼 → 본인 이메일로 받기
  4. 받으면 OK!

🛠 노트북 코드와 다른 점
  - api_key, sender를 노트북에서는 os.environ에서 읽었지만
    여기서는 st.secrets 를 사용합니다 (Streamlit Cloud 표준)
═══════════════════════════════════════════════════════════════
"""
import requests
import streamlit as st


def send_email(to: str, subject: str, body: str) -> dict:
    """이메일 발송. 키가 없으면 콘솔 출력만 (mock)."""
    api_key = st.secrets.get("SENDGRID_API_KEY", "")
    sender = st.secrets.get("EMAIL_ADDRESS", "")

    # API 키 없으면 mock (UI 데모용)
    if not api_key or not sender:
        print(f"[MOCK EMAIL] to={to} subject={subject!r}\n{body[:200]}…")
        return {"status": "mock", "to": to, "subject": subject}

    # ════════════════════════════════════════════════════════
    # 노트북 미션 1과 동일 (수정 불필요)
    # ════════════════════════════════════════════════════════
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "personalizations": [{"to": [{"email": to}], "subject": subject}],
        "from": {"email": sender},
        "content": [{"type": "text/plain", "value": body}],
    }
    resp = requests.post(url, headers=headers, json=data)
    if resp.status_code == 202:
        return {"status": "success"}
    return {"status": "failed", "error": resp.text}
