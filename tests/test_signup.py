from src.saas_signup import onboard_tenant


class FakeClient:
    def __init__(self):
        self.calls = []

    def post(self, path, body):
        self.calls.append((path, body))
        if path.endswith("captcha/verify"):
            return {"ok": True, "data": {}}
        if path.endswith("auth/user/create"):
            return {"ok": True, "data": {"id": "u_1", "email": body["email"]}}
        return {"ok": True, "data": {"id": "s_1"}}


def test_onboarding_links_owner_to_active_tenant():
    client = FakeClient()
    result = onboard_tenant(client, "owner@example.com", "pw", "Acme", "widget_1", "token")
    assert result["tenant"].active is True
    assert result["tenant"].members == ["u_1"]
    assert client.calls[0] == (
        "/v1/captcha/verify",
        {"widget_record_id": "widget_1", "token": "token", "action": "signup"},
    )
    assert client.calls[1][1]["idempotency_key"]
    assert client.calls[2][1]["user_id"] == "u_1"
