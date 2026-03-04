"""PASETO v4.local token helpers (symmetric encryption)."""
import json
import uuid
from datetime import datetime, timedelta, timezone

import pyseto
from pyseto import Key

from app.core.config import get_settings

settings = get_settings()

# ── Validate and build symmetric key at module load ──────────────────────────

_raw_key = settings.paseto_secret_key.encode()
if len(_raw_key) != 32:
    raise RuntimeError(
        f"PASETO_SECRET_KEY must be exactly 32 bytes, got {len(_raw_key)}"
    )

_symmetric_key = Key.new(version=4, purpose="local", key=_raw_key)


class PasetoError(Exception):
    """Raised when a PASETO token is invalid or expired."""


# ── Token helpers ────────────────────────────────────────────────────────────


def _create_token(
    user_id: str,
    token_type: str,
    expires_delta: timedelta,
) -> tuple[str, str, datetime]:
    """Return (encoded_token, jti, expires_at)."""
    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires_at = now + expires_delta
    payload = {
        "sub": user_id,
        "jti": jti,
        "exp": expires_at.isoformat(),
        "iat": now.isoformat(),
        "type": token_type,
    }
    token = pyseto.encode(
        _symmetric_key,
        payload=json.dumps(payload).encode(),
    )
    # pyseto.encode returns bytes; decode to str
    return token.decode() if isinstance(token, bytes) else str(token), jti, expires_at


def create_paseto_access_token(user_id: str) -> tuple[str, str, datetime]:
    return _create_token(
        user_id,
        "access",
        timedelta(minutes=settings.paseto_access_token_expire_minutes),
    )


def create_paseto_refresh_token(user_id: str) -> tuple[str, str, datetime]:
    return _create_token(
        user_id,
        "refresh",
        timedelta(days=settings.paseto_refresh_token_expire_days),
    )


def decode_paseto_token(token: str) -> dict:
    """Decrypt and verify a PASETO v4.local token. Raises PasetoError."""
    try:
        decoded = pyseto.decode(_symmetric_key, token)
    except Exception as exc:
        raise PasetoError(f"Invalid PASETO token: {exc}") from exc

    try:
        payload = json.loads(decoded.payload)
    except (json.JSONDecodeError, AttributeError) as exc:
        raise PasetoError(f"Malformed PASETO payload: {exc}") from exc

    # Manual expiration check (PASETO v4.local doesn't enforce claims)
    exp_str = payload.get("exp")
    if exp_str:
        exp_dt = datetime.fromisoformat(exp_str)
        if exp_dt < datetime.now(timezone.utc):
            raise PasetoError("PASETO token has expired")

    return payload
