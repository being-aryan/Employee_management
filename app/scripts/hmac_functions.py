import hashlib
import hmac


def generate_hmac(message: str, secret_key: bytes) -> str:
    message_bytes = message.encode("utf-8")

    digest = hmac.new(
        secret_key,
        message_bytes,
        hashlib.sha256,
    )

    return digest.hexdigest()


def verify_hmac(
    message: str,
    secret_key: bytes,
    stored_digest: str,
) -> bool:
    submitted_digest = generate_hmac(message, secret_key)

    return hmac.compare_digest(
        stored_digest,
        submitted_digest,
    )


def main() -> None:
    secret_key = b"my-secret-key"

    original_message = "482193"

    stored_digest = generate_hmac(
        original_message,
        secret_key,
    )

    print("Stored digest:", stored_digest)

    result = verify_hmac(
        "482193",
        secret_key,
        stored_digest,
    )

    print("Correct OTP:", result)

    result = verify_hmac(
        "123456",
        secret_key,
        stored_digest,
    )

    print("Incorrect OTP:", result)


if __name__ == "__main__":
    main()
