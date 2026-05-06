"""🔐 로그인 검증 (데모용)

데모 사용자는 아래 _USERS dict에 직접 정의.
실서비스라면 DB + 비밀번호 해시(bcrypt 등)로 교체해야 함.

➕ 새 데모 사용자 추가하고 싶으면 _USERS 에 한 줄 추가.
"""
from .models import User


# 데모 사용자 (실제로는 DB에서 조회)
_USERS = {
    "kim.daeri": {
        "password": "demopass",
        "name": "김 대리",
        "email": "kim@company.com",
        "team": "마케팅팀",
    },
}


def authenticate(username: str, password: str) -> User | None:
    """성공 시 User 객체, 실패 시 None"""
    if not username or not password:
        return None
    info = _USERS.get(username.strip())
    if info is None or info["password"] != password:
        return None
    return User(
        id=username,
        name=info["name"],
        email=info["email"],
        team=info["team"],
    )
