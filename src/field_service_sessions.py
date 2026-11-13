"""Field-service workflow: keep the active device and sign out the others."""

from __future__ import annotations

import argparse
from dataclasses import dataclass

try:
    from .infrai_sessions import ActiveSession, InfraiSessions
except ImportError:
    from infrai_sessions import ActiveSession, InfraiSessions


@dataclass(frozen=True)
class WorkOrder:
    work_order_id: str
    photo_refs: tuple[str, ...]
    dispatch_status: str
    technician_follow_up: str


def sessions_to_revoke(sessions: list[ActiveSession], current_session_id: str) -> list[str]:
    """Return every active session except the device handling this work order."""
    return [session.session_id for session in sessions if session.session_id != current_session_id]


def example_work_order() -> WorkOrder:
    return WorkOrder(
        work_order_id="wo-1042",
        photo_refs=("photo-before-1042", "photo-after-1042"),
        dispatch_status="en_route",
        technician_follow_up="Replace the cracked connector on the next visit.",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Review a field technician's sessions")
    parser.add_argument("--remote", nargs=2, metavar=("USER_ID", "CURRENT_SESSION_ID"))
    args = parser.parse_args()
    order = example_work_order()
    print(order)
    if args.remote:
        user_id, current_session_id = args.remote
        client = InfraiSessions()
        for session_id in sessions_to_revoke(client.list_active(user_id), current_session_id):
            client.revoke(session_id)
            print(f"revoked {session_id}")
        print(f"retained {current_session_id}")
        return
    sample = [
        ActiveSession("session-current", "vehicle tablet"),
        ActiveSession("session-tablet", "shop tablet"),
        ActiveSession("session-phone", "phone"),
    ]
    print({"retained": "session-current", "revoke": sessions_to_revoke(sample, "session-current")})


if __name__ == "__main__":
    main()
