import hashlib
import hmac
import secrets


def generate_otp() -> str:
    return str(secrets.randbelow(900000) + 100000)


def generate_challenge_id() -> str:
    return secrets.token_urlsafe(32)


def generate_otp_digest(
    otp: str,
    secret_key: bytes,
) -> str:
    return hmac.new(
        secret_key,
        otp.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_otp(
    submitted_otp: str,
    stored_digest: str,
    secret_key: bytes,
) -> bool:
    submitted_digest = generate_otp_digest(
        submitted_otp,
        secret_key,
    )
    return hmac.compare_digest(
        stored_digest,
        submitted_digest,
    )
