# screen_privacy/privacy_controller.py

import threading

# -------------------------------------------------
# 🔐 GLOBAL PRIVACY STATE (SINGLE SOURCE OF TRUTH)
# -------------------------------------------------

# Thread safety lock
_state_lock = threading.Lock()

# Whether screen privacy monitoring is active
_screen_guard_running = False

# Privacy decision
# Possible values: "SAFE" | "BLOCK"
_PRIVACY_STATE = "SAFE"

# 🔑 Privacy reason
# Possible values:
# "AUTHORIZED"
# "UNAUTHORIZED_USER"
# "MULTIPLE_FACES"
# "PHONE_DETECTED"
# "CAMERA_COVERED"
_PRIVACY_REASON = "AUTHORIZED"

# Allowed reasons
_VALID_REASONS = {
    "AUTHORIZED",
    "UNAUTHORIZED_USER",
    "MULTIPLE_FACES",
    "PHONE_DETECTED",
    "CAMERA_COVERED",
}


# -------------------------------------------------
# 🧠 PRIVACY DECISION LOGIC
# -------------------------------------------------

def update_privacy_state(is_authorized: bool, reason: str = None):
    """
    Updates privacy state based on authorization result.

    is_authorized = True  -> SAFE
    is_authorized = False -> BLOCK

    NOTE:
    - SAFE always implies AUTHORIZED
    - BLOCK must always have a reason
    """

    global _PRIVACY_STATE, _PRIVACY_REASON

    with _state_lock:

        if is_authorized:
            _PRIVACY_STATE = "SAFE"
            _PRIVACY_REASON = "AUTHORIZED"
            return

        # BLOCK case
        _PRIVACY_STATE = "BLOCK"

        if reason and reason in _VALID_REASONS:
            _PRIVACY_REASON = reason
        else:
            _PRIVACY_REASON = "UNAUTHORIZED_USER"


def is_privacy_blocked() -> bool:
    """
    Returns True if privacy is currently blocked.
    """

    with _state_lock:
        return _PRIVACY_STATE == "BLOCK"


def get_privacy_state() -> str:
    """
    Returns current privacy state ("SAFE" or "BLOCK").
    """

    with _state_lock:
        return _PRIVACY_STATE


def get_privacy_reason() -> str:
    """
    Returns the reason for current privacy state.
    """

    with _state_lock:
        return _PRIVACY_REASON


def get_privacy_status():
    """
    Returns full privacy status object.
    Useful for frontend dashboards.
    """

    with _state_lock:

        return {
            "state": _PRIVACY_STATE,
            "reason": _PRIVACY_REASON,
            "blocked": _PRIVACY_STATE == "BLOCK",
            "monitoring": _screen_guard_running
        }


# -------------------------------------------------
# 🎛 SCREEN GUARD CONTROL (STATE ONLY)
# -------------------------------------------------

def is_screen_guard_running() -> bool:
    """
    Returns whether screen privacy monitoring is active.
    """

    with _state_lock:
        return _screen_guard_running


def start_screen_guard():
    """
    Activates screen privacy monitoring.
    """

    global _screen_guard_running

    with _state_lock:

        if _screen_guard_running:
            return

        _screen_guard_running = True

    print("🔐 Screen Guard ACTIVATED")


def stop_screen_guard():
    """
    Deactivates screen privacy monitoring
    and resets privacy state to SAFE.
    """

    global _screen_guard_running, _PRIVACY_STATE, _PRIVACY_REASON

    with _state_lock:

        if not _screen_guard_running:
            return

        _screen_guard_running = False
        _PRIVACY_STATE = "SAFE"
        _PRIVACY_REASON = "AUTHORIZED"

    print("🟢 Screen Guard DEACTIVATED")


# -------------------------------------------------
# 🧩 SAFE HELPER (FACE COUNT ONLY)
# -------------------------------------------------

def update_privacy_from_face_count(face_count: int):
    """
    SAFE helper for face-count-based blocking ONLY.

    IMPORTANT RULES:
    - This function MUST NOT set SAFE
    - It can ONLY block if multiple faces detected
    - Final authorization is decided in screen_guard.py
    """

    if face_count > 1:

        update_privacy_state(
            is_authorized=False,
            reason="MULTIPLE_FACES"
        )