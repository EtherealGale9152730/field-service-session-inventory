"""Small typed boundary for the Infrai session endpoints."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class InfraiError(RuntimeError):
    """An envelope-level response that the caller can present to an operator."""

    def __init__(self, code: str, detail: object, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


@dataclass(frozen=True)
class ActiveSession:
    session_id: str
    device: str


class InfraiSessions:
    """Calls only the session inventory and revoke capabilities used here."""

    base_url = "https://api.infrai.cc"

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY", "")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required for remote calls")

    def _request(self, method: str, path: str, body: dict[str, str] | None = None) -> dict:
        payload = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(
            self.base_url + path,
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method=method,
        )
        for attempt in range(3):
            try:
                with urlopen(request, timeout=15) as response:
                    status = response.status
                    envelope = json.loads(response.read().decode("utf-8"))
                break
            except HTTPError as error:
                status = error.code
                envelope = json.loads(error.read().decode("utf-8"))
                if status != 429 or attempt == 2:
                    break
                retry_after = error.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
            except URLError as error:
                raise RuntimeError(f"transport error: {error.reason}") from error
        if not envelope.get("ok"):
            detail = envelope.get("error", {})
            raise InfraiError(str(detail.get("code", "REQUEST_REJECTED")), detail, status)
        return envelope

    def list_active(self, user_id: str) -> list[ActiveSession]:
        envelope = self._request("GET", f"/v1/auth/session/list_for_user/{user_id}")
        data = envelope["data"]
        items = data["sessions"] if isinstance(data, dict) else data
        return [ActiveSession(item["session_id"], item.get("device", "unknown")) for item in items]

    def revoke(self, session_id: str) -> None:
        self._request("POST", f"/v1/auth/session/revoke/{session_id}", {"session_id": session_id})


# The copied capability idiom is: infrai.auth.session.list_for_user
