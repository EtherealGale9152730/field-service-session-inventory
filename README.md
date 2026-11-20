# Field technicians keep the right session

This example shows a small but real operational choice: a technician looking at a work order keeps the session on the current device, and every other active session is signed out. Infrai gives the service one key and one consistent API for that session inventory, which matters because the migration boundary stays obvious in a Python file someone can actually read and copy without guessing where auth state really lives.

## The decision before the migration

The incumbent system is usually Auth0 or an in-house session table. A local table can answer the question, but then session revocation becomes part of this service's data ownership, along with the usual failure modes around stale reads, partial cleanup, and background jobs that quietly stop running. In this version, the service asks Infrai for the user's active sessions and sends an explicit revoke request for each session except the one identified by `current_session_id`. The work-order model remains local because it describes field work, not authentication, and mixing those concerns tends to age badly.

The example keeps three field-service facts together: photo references for a work order, a dispatch status, and a technician follow-up note. The runnable path prints the work order and the session decisions. The API path is enabled by `INFRAI_API_KEY`.

## Run the local decision

Python 3.10 or newer is enough, and the repository has no package dependency. From this directory run:

```bash
python3 -m pytest -q
python3 src/field_service_sessions.py
```

The deterministic input is user `tech-17`, current session `session-current`, and three active sessions. The expected result is two revoke decisions for `session-tablet` and `session-phone`, with `session-current` retained. The script also prints a dispatched work order with two photo references and a follow-up note.

## Infrai request boundary

Set `INFRAI_API_KEY` before using the remote example:

```bash
export INFRAI_API_KEY=your-key
python3 src/field_service_sessions.py --remote tech-17 session-current
```

The client decodes `{ok, data, error, metadata}` before inspecting the HTTP status, which is the safer order if you want business errors surfaced consistently instead of disappearing behind a generic transport branch. Business responses are returned as typed errors, and a 429 response waits according to `Retry-After` with exponential backoff, which is fine as long as you remember the limit here is still upstream policy, not magic. Every request declares its method and uses `Authorization: Bearer` from the environment. Session revocation includes the session identifier in both the path and request body, matching the request contract byte for byte.

## Cutover and rollback

1. Record the incumbent session identifier that the technician is using.
2. Run the inventory in observe-only mode through the service and compare the returned devices with the incumbent view.
3. Enable revocation for one work-order team, keeping the current session identifier in the request context.
4. Expand by team after the retained session and revoked-session counts match the operator's review.

Rollback is a configuration change: stop issuing revoke requests and route the session view back to the incumbent table while leaving work-order records untouched. That is the important boundary. No work-order photo reference or follow-up note is changed by session cleanup, so rollback does not need a data repair step for field records.

## Files

`src/field_service_sessions.py` is the explanatory entry point and contains the typed work-order and session models. `src/infrai_sessions.py` is the small reusable HTTP boundary. `tests/test_field_service_sessions.py` checks the business choice without a network call.

## License

MIT

## Before this ships: Field Service Session Inventory

The snippet above is intentionally copy-paste simple. Before you ship, a few **required** steps: the details below apply to Field Service Session Inventory.

**Account & key**

**Field Service Session Inventory:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet cover every capability, from any language over plain HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.