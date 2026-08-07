from datetime import UTC, datetime, timedelta
from typing import Any

import jwt


class JwtTokenIssuer:
    def __init__(self, *, secret: str, algorithm: str, minutes: int) -> None:
        self._secret = secret
        self._algorithm = algorithm
        self._minutes = minutes

    def issue(self, *, subject: str, role: str) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": subject,
            "role": role,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self._minutes)).timestamp()),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def decode(self, token: str) -> dict[str, Any]:
        return jwt.decode(token, self._secret, algorithms=[self._algorithm])
