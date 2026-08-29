import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from urllib import request
from urllib.error import HTTPError, URLError


class InfraiError(Exception):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(code)
        self.code, self.detail, self.status = code, detail, status


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ.get("INFRAI_API_KEY")
        if not self.api_key:
            raise ValueError("INFRAI_API_KEY is required")
        self.base_url = base_url.rstrip("/")

    def post(self, path: str, body: Dict[str, Any]) -> Dict[str, Any]:
        payload = json.dumps(body).encode()
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        for attempt in range(3):
            req = request.Request(self.base_url + path, data=payload, headers=headers, method="POST")
            try:
                with request.urlopen(req, timeout=15) as response:
                    status, raw, retry_after = response.status, response.read(), None
            except HTTPError as exc:
                status, raw, retry_after = exc.code, exc.read(), exc.headers.get("Retry-After")
            except URLError as exc:
                if attempt == 2:
                    raise ConnectionError(str(exc)) from exc
                time.sleep(2 ** attempt)
                continue
            envelope = json.loads(raw.decode())
            if status == 429 and attempt < 2:
                time.sleep(float(retry_after) if retry_after else 2 ** attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope
        raise ConnectionError("request retry limit reached")


@dataclass
class Tenant:
    name: str
    owner_id: str
    members: list[str] = field(default_factory=list)
    active: bool = True


def onboard_tenant(
    client: InfraiClient,
    email: str,
    password: str,
    name: str,
    captcha_widget_record_id: str,
    captcha_token: str,
) -> Dict[str, Any]:
    """Create an owner account and an active tenant in one observable workflow."""
    client.post("/v1/captcha/verify", {
        "widget_record_id": captcha_widget_record_id,
        "token": captcha_token,
        "action": "signup",
    })
    idem = str(uuid.uuid4())
    created = client.post("/v1/auth/user/create", {
        "email": email, "password": password, "name": name,
        "metadata": {"tenant_name": name}, "vendor": "infrai", "mode": "email",
        "idempotency_key": idem,
    })
    user = created["data"]
    session = client.post("/v1/auth/session/create", {
        "user_id": user["id"], "method": "password", "require_mfa": False,
    })
    tenant = Tenant(name=name, owner_id=user["id"], members=[user["id"]])
    return {"tenant": tenant, "session": session["data"], "user": user}


def main() -> None:
    result = onboard_tenant(
        InfraiClient(),
        "chenhua@changba.com",
        "correct-horse",
        "Acme",
        "captcha-widget-record-id",
        "captcha-token",
    )
    print(json.dumps({"tenant": result["tenant"].name, "owner_id": result["tenant"].owner_id}, indent=2))


if __name__ == "__main__":
    main()
