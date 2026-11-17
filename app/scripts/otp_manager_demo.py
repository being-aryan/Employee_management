from app.config import settings
from app.managers.otp_manager import OTPManager
from app.redis_client import redis_client


async def main() -> None:
    try:
        otp_manager = OTPManager(
            redis_client=redis_client,
            secret_key=bytes.fromhex(settings.otp_hmac_secret_key),
        )

        challenge_id, otp = await otp_manager.create_challenge(admin_id=123)

        redis_key = f"otp:challenge:{challenge_id}"

        print("Generated OTP:", otp)
        print("Challenge ID:", challenge_id)

        challenge = await redis_client.hgetall(redis_key)

        print("\nStored Redis Hash:")
        print(challenge)

        ttl = await redis_client.ttl(redis_key)

        print("\nRemaining TTL:", ttl)

        await redis_client.delete(redis_key)

        print("Test challenge deleted.")

    finally:
        await redis_client.aclose()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
