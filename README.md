# 에이블 (Able) — AI 개인비서

> 1일차 노트북 코드를 Streamlit 앱에 끼워 넣어 완성하는 프로젝트.

---

## 🚀 빠른 시작 (처음 받았을 때 한 번만)

```bash
# 1) 패키지 설치
pip install -r requirements.txt

# 2) API 키 등록
# .streamlit/secrets.toml.example 을 복사해서 .streamlit/secrets.toml 로 이름 바꾸고
# 안에 OPENAI_API_KEY = "sk-..." 입력

# 3) 실행
streamlit run app.py
```

기본 로그인 — 아이디 `kim.daeri` / 비번 `demopass`

---

## 📁 폴더 구조

```
AIVLE_app/
├── app.py                  ← 진입점 (로그인 화면)
│
├── pages/                  ← 사이드바 메뉴 (이 폴더 안 .py 가 자동으로 메뉴됨)
│   ├── 1_대시보드.py
│   ├── 2_회의_분석.py     ← 미션 3·4 사용
│   ├── 3_To-Do_관리.py
│   ├── 4_캘린더.py
│   ├── 5_음성_비서.py     ← 미션 5·1 사용
│   └── 6_설정.py
│
├── core/                   ← 공통 로직 (페이지에서 import)
│   ├── llm.py             ⭐ 노트북 미션 3·4·5·7 — 팀원이 채우는 파일
│   ├── email_sender.py    ⭐ 노트북 미션 1 — 이미 완료
│   ├── store.py           — 데이터 저장 (수정 불필요)
│   ├── models.py          — 데이터 형식 정의 (수정 불필요)
│   ├── auth.py            — 로그인 검증
│   └── demo_data.py       — 데모 시드 데이터
│
├── .streamlit/
│   ├── config.toml        — 테마 설정
│   └── secrets.toml       — API 키 (직접 만들기, git 제외)
│
├── requirements.txt
├── README.md              ← 지금 읽고 있는 파일
└── 2단계_연동가이드.md     — OpenAI 연동 상세 가이드
```

---

## 🎯 어디를 만지면 되나

| 만질 파일 | 무엇을 | 노트북 미션 |
|---|---|---|
| **`core/llm.py`** | `analyze_meeting()`, `stt()`, `tts()`, `chat_with_tools()` 채우기 | 3, 4, 5, 7 |
| `core/email_sender.py` | (이미 완료, 검증만) | 1 |

**원칙**: `pages/` 폴더 파일은 함부로 손대지 마세요. 화면 디자인이 깨지면 다른 사람 작업과 충돌납니다.

---

## ✅ 본인 코드 동작 확인

`streamlit run app.py` 로 실행 후:

| 함수 | 검증 페이지 | 시나리오 |
|---|---|---|
| `analyze_meeting()` | 회의 분석 | 텍스트 탭에 회의록 붙여넣고 ‘분석 시작’ |
| `stt()` | 회의 분석 (녹음 탭) | 마이크 녹음 후 ‘분석 시작’ — 한국어 인식되는지 |
| `tts()` | 음성 비서 | ‘▶ 재생’ — 음성이 들리는지 |
| `send_email()` | 음성 비서 | ‘📧 이메일로 발송’ — 본인 이메일로 도착하는지 |

---

## 🆘 자주 막히는 점

| 증상 | 원인 / 해결 |
|---|---|
| `ModuleNotFoundError` | `pip install -r requirements.txt` 다시 |
| `KeyError: 'OPENAI_API_KEY'` | `.streamlit/secrets.toml` 위치/내용 확인 |
| 녹음 안 됨 | 브라우저 마이크 권한 허용 |
| 코드 수정했는데 화면 그대로 | 브라우저 `Ctrl+Shift+R` |

상세 — [`2단계_연동가이드.md`](./2단계_연동가이드.md)
