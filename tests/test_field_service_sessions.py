from src.field_service_sessions import sessions_to_revoke
from src.infrai_sessions import ActiveSession


def test_current_device_is_retained_while_other_devices_are_revoked():
    sessions = [
        ActiveSession("session-current", "vehicle tablet"),
        ActiveSession("session-tablet", "shop tablet"),
        ActiveSession("session-phone", "phone"),
    ]

    assert sessions_to_revoke(sessions, "session-current") == ["session-tablet", "session-phone"]
