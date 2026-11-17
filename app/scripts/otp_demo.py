from app.utils.otp import (
    generate_challenge_id,
    generate_otp,
    generate_otp_digest,
    verify_otp,
)


def main() -> None:
    secret_key = b"practice-secret-key"

    otp = generate_otp()
    challenge_id = generate_challenge_id()
    stored_digest = generate_otp_digest(
        otp,
        secret_key,
    )

    print("OTP:", otp)
    print("Challenge ID:", challenge_id)
    print("OTP digest:", stored_digest)

    print(
        "Correct OTP:",
        verify_otp(otp, stored_digest, secret_key),
    )

    print(
        "Incorrect OTP:",
        verify_otp("123456", stored_digest, secret_key),
    )


if __name__ == "__main__":
    main()
