"""
Authentication Engine & SQLite Session Manager for South India Urban Intelligence (§4).

Features:
- Secure SQLite user & session store.
- Timing-safe password hashing using PBKDF2-HMAC-SHA256 (600,000 iterations).
- Cryptographic session tokens & expiry management.
- Protection against timing attacks, user enumeration, and duplicate signups.
"""

import os
import sqlite3
import secrets
import hashlib
import hmac
import datetime
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

PBKDF2_ITERATIONS = 600_000

def get_db_connection() -> sqlite3.Connection:
    db_path = os.getenv("AUTH_DB_PATH", "auth_store.db")
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_auth_db():
    """Initializes SQLite database schemas for users and sessions."""
    db_path = os.getenv("AUTH_DB_PATH", "auth_store.db")
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL COLLATE NOCASE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL,
                last_login_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        conn.commit()
    logger.info(f"[Auth DB] Initialized authentication tables at {db_path}")

def hash_password(password: str) -> str:
    """Hashes password using PBKDF2-HMAC-SHA256 with a unique random salt."""
    salt = secrets.token_bytes(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${key.hex()}"

def verify_password(password: str, hashed_str: str) -> bool:
    """Verifies password against stored hash using constant-time comparison."""
    try:
        parts = hashed_str.split('$')
        if len(parts) != 4 or parts[0] != 'pbkdf2_sha256':
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_key = bytes.fromhex(parts[3])
        computed_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        return hmac.compare_digest(computed_key, expected_key)
    except Exception as e:
        logger.error(f"[Auth] Password verification error: {e}")
        return False

def signup_user(full_name: str, email: str, password: str) -> Dict[str, Any]:
    """Creates a new user account if email is available."""
    email_clean = email.strip().lower()
    if len(password) < 10:
        raise ValueError("Password must be at least 10 characters long.")

    user_id = f"usr_{secrets.token_hex(8)}"
    pwd_hash = hash_password(password)
    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (id, full_name, email, password_hash, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, full_name.strip(), email_clean, pwd_hash, now_iso)
            )
            conn.commit()
    except sqlite3.IntegrityError:
        raise ValueError("User with this email already exists.")

    return {
        "id": user_id,
        "full_name": full_name.strip(),
        "email": email_clean,
        "created_at": now_iso
    }

def authenticate_user(email: str, password: str, remember: bool = False) -> Dict[str, Any]:
    """Authenticates user credentials and generates a session token."""
    email_clean = email.strip().lower()
    
    # Timing-safe dummy calculation if user is not found to prevent enumeration timing side channels
    dummy_hash = "pbkdf2_sha256$600000$00000000000000000000000000000000$0000000000000000000000000000000000000000000000000000000000000000"

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, full_name, email, password_hash FROM users WHERE email = ?", (email_clean,))
        row = cursor.fetchone()

    if not row:
        verify_password(password, dummy_hash)
        raise ValueError("Invalid email or password.")

    user_id, full_name, user_email, pwd_hash = row["id"], row["full_name"], row["email"], row["password_hash"]

    if not verify_password(password, pwd_hash):
        raise ValueError("Invalid email or password.")

    # Create session
    token = secrets.token_hex(32)
    now = datetime.datetime.now(datetime.timezone.utc)
    duration_days = 30 if remember else 1
    expires_at = (now + datetime.timedelta(days=duration_days)).isoformat()
    now_iso = now.isoformat()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO sessions (token, user_id, expires_at, created_at) VALUES (?, ?, ?, ?)",
            (token, user_id, expires_at, now_iso)
        )
        cursor.execute(
            "UPDATE users SET last_login_at = ? WHERE id = ?",
            (now_iso, user_id)
        )
        conn.commit()

    return {
        "token": token,
        "user": {
            "id": user_id,
            "full_name": full_name,
            "email": user_email,
            "last_login_at": now_iso
        }
    }

def get_session_user(token: str) -> Optional[Dict[str, Any]]:
    """Retrieves user profile for a valid non-expired session token."""
    if not token:
        return None

    now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.expires_at, u.id, u.full_name, u.email, u.created_at
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
        """, (token,))
        row = cursor.fetchone()

        if not row:
            return None

        if row["expires_at"] < now_iso:
            # Delete expired session
            cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return None

        return {
            "id": row["id"],
            "full_name": row["full_name"],
            "email": row["email"],
            "created_at": row["created_at"]
        }

def delete_session(token: str):
    """Deletes a session token from storage (logout)."""
    if not token:
        return
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()

# Ensure tables are created on module import
init_auth_db()
