"""
auth.py – Role-Based Access Control helpers for SentinelEdge.

Roles
-----
admin           : Full access – thresholds, delete logs, AI reports, all tabs.
floor_supervisor: Read + log violations only; cannot delete logs or edit thresholds.

Password storage
----------------
Passwords are stored as SHA-256 hashes inside users.json so plain-text secrets
never live in memory beyond the moment the user types them.

Password reset
--------------
A token-based self-service reset flow is provided:
  1. User clicks "Forgot Password?" and enters their username.
  2. A one-time 6-digit token (valid 15 min) is generated and displayed
     on-screen (in a real deployment this would be emailed / SMS'd).
  3. User enters the token + their new password to complete the reset.
Tokens are persisted in reset_tokens.json and cleaned up on use or expiry.
"""
import hashlib
import json
import os
import secrets
import time
from datetime import datetime

import streamlit as st

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
_DIR = os.path.dirname(os.path.abspath(__file__))
_USERS_FILE = os.path.join(_DIR, "users.json")
_TOKENS_FILE = os.path.join(_DIR, "reset_tokens.json")
_TOKEN_TTL_SECONDS = 15 * 60  # 15 minutes

# ---------------------------------------------------------------------------
# Permissions granted to each role
# ---------------------------------------------------------------------------
_ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": {
        "log_violations",
        "view_analytics",
        "view_audit_logs",
        "delete_audit_logs",
        "edit_thresholds",
        "generate_ai_report",
    },
    "floor_supervisor": {
        "log_violations",
        "view_analytics",
        "view_audit_logs",
    },
}

# ---------------------------------------------------------------------------
# Fallback in-memory defaults (used if users.json is missing)
# ---------------------------------------------------------------------------
_DEFAULT_USERS: dict[str, dict] = {
    "admin": {
        "password_hash": hashlib.sha256("Admin@123".encode()).hexdigest(),
        "role": "admin",
        "display": "Administrator",
    },
    "supervisor1": {
        "password_hash": hashlib.sha256("Super@456".encode()).hexdigest(),
        "role": "floor_supervisor",
        "display": "Floor Supervisor",
    },
}


# ---------------------------------------------------------------------------
# User store helpers
# ---------------------------------------------------------------------------

def _load_users() -> dict:
    """Load users from users.json; fall back to defaults and seed the file."""
    if os.path.exists(_USERS_FILE):
        try:
            with open(_USERS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    # Seed the file with defaults on first run or after corruption
    _save_users(_DEFAULT_USERS)
    return dict(_DEFAULT_USERS)


def _save_users(users: dict) -> None:
    with open(_USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def _load_tokens() -> dict:
    if os.path.exists(_TOKENS_FILE):
        try:
            with open(_TOKENS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def _save_tokens(tokens: dict) -> None:
    with open(_TOKENS_FILE, "w", encoding="utf-8") as f:
        json.dump(tokens, f, indent=2)


def _purge_expired_tokens(tokens: dict) -> dict:
    """Remove tokens that have passed their TTL."""
    now = time.time()
    return {t: v for t, v in tokens.items() if now < v["expires_at"]}


# ---------------------------------------------------------------------------
# Core auth helpers
# ---------------------------------------------------------------------------

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def authenticate(username: str, password: str) -> dict | None:
    """Return the user record if credentials are valid, else None."""
    users = _load_users()
    user = users.get(username.strip().lower())
    if user and user["password_hash"] == _hash(password):
        return user
    return None


def has_permission(permission: str) -> bool:
    """Check whether the currently logged-in user has a given permission."""
    role = st.session_state.get("role", "")
    return permission in _ROLE_PERMISSIONS.get(role, set())


def is_logged_in() -> bool:
    return st.session_state.get("logged_in", False)


def logout() -> None:
    for key in ("logged_in", "username", "role", "display_name"):
        st.session_state.pop(key, None)


# ---------------------------------------------------------------------------
# Password reset helpers
# ---------------------------------------------------------------------------

def generate_reset_token(username: str) -> str | None:
    """
    Generate a 6-digit reset token for *username* (must exist).
    Saves it to reset_tokens.json with a 15-min expiry.
    Returns the token string, or None if the username is unknown.
    """
    users = _load_users()
    if username.strip().lower() not in users:
        return None

    token = str(secrets.randbelow(900000) + 100000)   # 100000–999999
    tokens = _purge_expired_tokens(_load_tokens())
    tokens[token] = {
        "username": username.strip().lower(),
        "expires_at": time.time() + _TOKEN_TTL_SECONDS,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    _save_tokens(tokens)
    return token


def validate_reset_token(token: str) -> str | None:
    """
    Validate *token*. Returns the associated username if valid and unexpired,
    else None.
    """
    tokens = _purge_expired_tokens(_load_tokens())
    entry = tokens.get(token.strip())
    if entry:
        return entry["username"]
    return None


def reset_password(token: str, new_password: str) -> bool:
    """
    Apply *new_password* to the user linked to *token*.
    Deletes the token after use. Returns True on success.
    """
    username = validate_reset_token(token)
    if not username:
        return False

    users = _load_users()
    if username not in users:
        return False

    users[username]["password_hash"] = _hash(new_password)
    _save_users(users)

    # Consume the token so it cannot be reused
    tokens = _load_tokens()
    tokens.pop(token.strip(), None)
    _save_tokens(tokens)
    return True


def _password_is_strong(pw: str) -> tuple[bool, str]:
    """Return (ok, reason). Enforces basic strength rules."""
    if len(pw) < 8:
        return False, "Password must be at least 8 characters."
    if not any(c.isupper() for c in pw):
        return False, "Password must contain at least one uppercase letter."
    if not any(c.isdigit() for c in pw):
        return False, "Password must contain at least one digit."
    return True, ""


# ---------------------------------------------------------------------------
# Sidebar UI
# ---------------------------------------------------------------------------

def render_login_sidebar() -> None:
    """
    Render the login / forgot-password / reset-password UI in the sidebar.
    Must be called before any permission-gated content is shown.
    """
    if is_logged_in():
        role_label = (
            "🔑 Administrator" if st.session_state["role"] == "admin"
            else "👷 Floor Supervisor"
        )
        st.sidebar.success(f"Logged in as **{st.session_state['display_name']}**")
        st.sidebar.caption(role_label)
        if st.sidebar.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()
        return

    # Sidebar view state: "login" | "forgot" | "reset"
    st.session_state.setdefault("auth_view", "login")

    # ── LOGIN ────────────────────────────────────────────────────────────────
    if st.session_state["auth_view"] == "login":
        st.sidebar.header("🔐 Secure Login")
        st.sidebar.caption("Access is restricted to authorised personnel only.")

        with st.sidebar.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", placeholder="e.g. admin")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            user = authenticate(username, password)
            if user:
                st.session_state["logged_in"] = True
                st.session_state["username"] = username.strip().lower()
                st.session_state["role"] = user["role"]
                st.session_state["display_name"] = user["display"]
                st.session_state["auth_view"] = "login"
                st.rerun()
            else:
                st.sidebar.error("❌ Invalid username or password.")

        st.sidebar.markdown("---")
        if st.sidebar.button("🔑 Forgot Password?", use_container_width=True):
            st.session_state["auth_view"] = "forgot"
            st.rerun()

    # ── FORGOT PASSWORD (Step 1 – enter username) ────────────────────────────
    elif st.session_state["auth_view"] == "forgot":
        st.sidebar.header("🔑 Forgot Password")
        st.sidebar.caption("Enter your username to receive a reset token.")

        with st.sidebar.form("forgot_form", clear_on_submit=False):
            uname = st.text_input("Username", placeholder="Your username")
            send = st.form_submit_button("Generate Reset Token", use_container_width=True)

        if send:
            token = generate_reset_token(uname)
            if token:
                expires_min = _TOKEN_TTL_SECONDS // 60
                st.sidebar.success("✅ Reset token generated!")
                st.sidebar.info(
                    f"**Your one-time reset token:**\n\n"
                    f"```\n{token}\n```\n\n"
                    f"⏱️ Valid for **{expires_min} minutes**.\n\n"
                    f"_(In production this would be sent to your registered email.)_"
                )
                st.session_state["reset_username_hint"] = uname.strip().lower()
                st.session_state["auth_view"] = "reset"
            else:
                st.sidebar.error("❌ Username not found.")

        st.sidebar.markdown("---")
        if st.sidebar.button("← Back to Login", use_container_width=True):
            st.session_state["auth_view"] = "login"
            st.rerun()

    # ── RESET PASSWORD (Step 2 – enter token + new password) ─────────────────
    elif st.session_state["auth_view"] == "reset":
        st.sidebar.header("🔒 Reset Password")
        st.sidebar.caption("Enter the token you received and choose a new password.")

        with st.sidebar.form("reset_form", clear_on_submit=False):
            token_input = st.text_input("Reset Token", placeholder="6-digit token")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            apply = st.form_submit_button("Reset Password", use_container_width=True)

        if apply:
            if not token_input.strip():
                st.sidebar.error("❌ Please enter the reset token.")
            elif new_pw != confirm_pw:
                st.sidebar.error("❌ Passwords do not match.")
            else:
                ok, reason = _password_is_strong(new_pw)
                if not ok:
                    st.sidebar.error(f"❌ {reason}")
                else:
                    if reset_password(token_input, new_pw):
                        st.sidebar.success("✅ Password reset successfully! Please log in.")
                        st.session_state.pop("reset_username_hint", None)
                        st.session_state["auth_view"] = "login"
                        st.rerun()
                    else:
                        st.sidebar.error(
                            "❌ Invalid or expired token. "
                            "Please request a new one."
                        )

        st.sidebar.markdown("---")
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state["auth_view"] = "forgot"
                st.rerun()
        with col2:
            if st.button("🏠 Login", use_container_width=True):
                st.session_state["auth_view"] = "login"
                st.rerun()

