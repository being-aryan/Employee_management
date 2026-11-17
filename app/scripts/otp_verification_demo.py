
import asyncio

from app.config import settings
from app.managers.otp_manager import OTPManager
from app.redis_client import redis_client


async def main() -> None:
    otp_manager = OTPManager(
        redis_client=redis_client,
        secret_key=bytes.fromhex(settings.otp_hmac_secret_key),
    )

    try:
        print("\nTEST 1: Correct OTP")

        challenge_id, otp = await otp_manager.create_challenge(
            admin_id=123
        )

        result = await otp_manager.verify_challenge(
            challenge_id,
            otp,
        )

        print("Expected admin ID: 123")
        print("Actual result:", result)
        print("Passed:", result == 123)

        print("\nTEST 2: Reusing the same OTP")

        result = await otp_manager.verify_challenge(
            challenge_id,
            otp,
        )

        print("Expected result: None")
        print("Actual result:", result)
        print("Passed:", result is None)

        print("\nTEST 3: Incorrect OTP")

        challenge_id, otp = await otp_manager.create_challenge(
            admin_id=456
        )

        result = await otp_manager.verify_challenge(
            challenge_id,
            "000000" if otp != "000000" else "000001",
        )

        redis_key = f"otp:challenge:{challenge_id}"
        attempts = await redis_client.hget(
            redis_key,
            "attempts",
        )

        print("Expected result: None")
        print("Actual result:", result)
        print("Failed attempts:", attempts)
        print("Passed:", result is None and attempts == "1")

        print("\nTEST 4: Maximum five incorrect attempts")

        challenge_id, otp = await otp_manager.create_challenge(
            admin_id=789
        )

        wrong_otp = "000000" if otp != "000000" else "000001"

        results = []

        for _ in range(5):
            result = await otp_manager.verify_challenge(
                challenge_id,
                wrong_otp,
            )
            results.append(result)

        exists = await redis_client.exists(
            f"otp:challenge:{challenge_id}"
        )

        print("All results are None:", all(
            result is None for result in results
        ))
        print("Challenge exists:", bool(exists))
        print("Passed:", all(
            result is None for result in results
        ) and exists == 0)

    finally:
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
