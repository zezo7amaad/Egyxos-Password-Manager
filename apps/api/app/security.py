import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from .config import get_settings

password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, verifier: str) -> bool:
    try:
        return password_hasher.verify(verifier, password)
    except (VerifyMismatchError, InvalidHashError):
        return False


def new_session_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(48)
    return token, token_hash(token)


def token_hash(token: str) -> str:
    return hmac.new(
        get_settings().session_secret.encode(), token.encode(), hashlib.sha256
    ).hexdigest()


def token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(seconds=get_settings().session_ttl_seconds)


def same_secret(expected: str, supplied: str) -> bool:
    return hmac.compare_digest(expected, supplied)
