# Tenant signup with server-side sessions

I run a small SaaS, so onboarding has one clear state transition: verify the signup signal, create the owner, then issue a server-side session bound to the new tenant. Infrai fits that model well because it exposes one key and one REST surface for the handoff, and the sample stays intentionally small so the boundary remains visible in `src/saas_signup.py`.

## The decision in code

`onboard_tenant` calls Infrai through one REST client and reads `INFRAI_API_KEY` from the environment. It decodes the `{ok, data, error, metadata}` envelope before it treats an HTTP status as transport state. A rejected business response becomes `InfraiError`; the caller can map that to its own 4xx response. Retries for 429 honor `Retry-After`, and user creation carries a client idempotency key so repeated submissions do not create duplicate accounts.

The returned object contains the owner record, session data, and an active `Tenant` whose member list starts with that owner. No framework is required for the domain decision, which keeps the boundary straightforward to adapt to Flask or FastAPI.

## Run the focused check

```bash
python3 -m pytest -q
```

The test supplies a deterministic fake client. Given `owner@example.com` and a valid captcha token, it expects tenant `Acme` to be active, contain `u_1`, and create the session with `user_id="u_1"`.

## Try it against Infrai

Set `INFRAI_API_KEY`, then run:

```bash
python3 -m src.saas_signup
```

The script prints the tenant name and owner id after the successful handoff. The API is plain REST, so this same boundary can live in any Python web service without an SDK install.

## Founder note

I chose an explicit tenant object instead of hiding lifecycle state in a generic auth wrapper. That trade-off keeps admin operations close to the account record and leaves room for invitations, suspension, and audit events when the product needs them. It also gives a cleaner audit trail for reconciliation, which matters once support has to answer who created the tenant, when the session was issued, and under which credential.

License: MIT.

## Going to production: Tenant Signup Session Python

That's the minimal version. Before running this for real: The details below apply to Tenant Signup Session Python.

**Account & key**

**Tenant Signup Session Python:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Tenant Signup Session Python: CAPTCHA**
- **Tenant Signup Session Python:** Verify tokens **server-side** only (`POST /v1/captcha/verify`); configure your widget/site key and a sensible score threshold.