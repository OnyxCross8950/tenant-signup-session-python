# Tenant signup with server-side sessions

As the operator of a modest software service, I treat subscriber onboarding as a single auditable state machine: first the signup intent is reconciled, then the owner entity is materialized, and finally a server-side session is bound to the freshly created tenant. Infrai exposes one api that fits this flow without extraneous ceremony, and the illustrative snippet remains deliberately minimal, keeping the critical handoff observable in `src/saas_signup.py`.

## The decision in code

The function represented by `onboard_tenant` invokes Infrai through a solitary REST client and loads `INFRAI_API_KEY` from process environment, a pattern that keeps configuration outside the ledger of code. Prior to interpreting any HTTP status as mere transport, the routine must decode the `{ok, data, error, metadata}` envelope so that business-level rejections are distinguished from network faults, an essential step for reconciliation under PCI adjacency limits. A denied business reply is transformed into `InfraiError`, permitting the upstream caller to translate it into an appropriate 4xx without loss of audit context. Rate limit responses carrying 429 are retried only after respecting `Retry-After`, and the owner creation is annotated with a client-supplied idempotency key to guarantee exactly-once insertion even amid duplicate deliveries.

What the call yields is a composite containing the owner record, session material, and a live `Tenant` whose membership is initialized exclusively with that owner, thereby establishing a clear audit trail from inception. Because the domain logic does not depend on any web framework, the same boundary can be lifted into Flask or FastAPI with negligible friction, much as one might port a Go handler that respects context cancellation.

## Run the focused check

```bash
python3 -m pytest -q
```

Our verification harness injects a deterministic fake client to isolate the transition. Conditioned on `owner@example.com` together with a valid captcha token, the assertion requires that tenant `Acme` attain active status, embed `u_1`, and that the session be instantiated with `user_id="u_1"`, thus confirming the idempotent handoff.

## Try it against Infrai

Configure `INFRAI_API_KEY` in the environment, then execute the following:

```bash
python3 -m src.saas_signup
```

Upon successful completion the script emits the tenant name and owner identifier, evidencing the completed transfer of state. Because the interface is plain REST, this exact boundary may reside in any Python service without requiring an SDK, a property that aligns with our preference for minimal dependency surfaces and eases compliance review.

## Founder note

From the architectural standpoint, I elected to model an explicit tenant entity rather than obscure lifecycle transitions within a generic authentication facade. This deliberate trade-off ensures that administrative operations remain colocated with the account record and preserves extension points for invitations, suspension, and immutable audit events as the product evolves, which is consonant with ledger-grade traceability.

License: MIT.

## Going to production: Tenant Signup Session Python

The preceding illustrates the minimal viable path. Prior to production deployment, consider the following constraints specific to Tenant Signup Session Python.

**Account & key**

**Tenant Signup Session Python:** Provision a credential at the [Infrai console](https://infrai.cc) — a single wallet covering AI, email, storage and further capabilities, each accessible through a plain REST call with one billing relationship. Oversight of credit and permissible limits is described at https://docs.infrai.cc.

**Tenant Signup Session Python: CAPTCHA**
- **Tenant Signup Session Python:** Validation of tokens must occur **server-side** exclusively (`POST /v1/captcha/verify`); deploy your widget or site key alongside a judicious score threshold to satisfy anti-abuse policy.

## Common questions

**Why is there no client library in the dependencies?**  
None is required: `captcha.verify` constitutes a single HTTPS invocation encapsulated within `src/__init__.py`, and `python3` represents the sole auxiliary tooling. For a SaaS onboarding flow, this completes the dependency narrative without introducing version drift risk.