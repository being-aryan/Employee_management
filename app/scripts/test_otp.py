
import asyncio

from app.config import settings
from app.managers.otp_manager import OTPManager
from app.redis_client import redis_client

otp_manager = OTPManager(
    redis_client=redis_client,
    secret_key=bytes.fromhex(settings.otp_hmac_secret_key),
)


async def test_challenge_creation():
    print("\nTEST 1: OTP challenge creation")

    challenge_id, otp = await otp_manager.create_challenge(
        admin_id=123
    )

    redis_key = f"otp:challenge:{challenge_id}"

    data = await redis_client.hgetall(redis_key)
    ttl = await redis_client.ttl(redis_key)

    assert len(otp) == 6
    assert otp.isdigit()
    assert data["admin_id"] == "123"
    assert data["attempts"] == "0"
    assert "otp_digest" in data
    assert data["otp_digest"] != otp
    assert 0 < ttl <= 300

    print("Challenge ID generated:", bool(challenge_id))
    print("OTP format valid:", len(otp) == 6)
    print("Admin ID stored:", data["admin_id"])
    print("OTP digest stored:", bool(data["otp_digest"]))
    print("Initial attempts:", data["attempts"])
    print("TTL:", ttl)
    print("PASSED")

    await redis_client.delete(redis_key)


async def test_correct_otp():
    print("\nTEST 2: Correct OTP verification")

    challenge_id, otp = await otp_manager.create_challenge(
        admin_id=123
    )

    result = await otp_manager.verify_challenge(
        challenge_id,
        otp,
    )

    exists = await redis_client.exists(
        f"otp:challenge:{challenge_id}"
    )

    assert result == 123
    assert exists == 0

    print("Expected admin ID: 123")
    print("Actual result:", result)
    print("Challenge deleted:", exists == 0)
    print("PASSED")


async def test_otp_reuse():
    print("\nTEST 3: OTP reuse prevention")

    challenge_id, otp = await otp_manager.create_challenge(
        admin_id=123
    )

    first_result = await otp_manager.verify_challenge(
        challenge_id,
        otp,
    )

    second_result = await otp_manager.verify_challenge(
        challenge_id,
        otp,
    )

    assert first_result == 123
    assert second_result is None

    print("First verification:", first_result)
    print("Second verification:", second_result)
    print("PASSED")


async def test_incorrect_otp():
    print("\nTEST 4: Incorrect OTP verification")

    challenge_id, _ = await otp_manager.create_challenge(
        admin_id=456
    )

    result = await otp_manager.verify_challenge(
        challenge_id,
        "000000",
    )

    redis_key = f"otp:challenge:{challenge_id}"

    attempts = await redis_client.hget(
        redis_key,
        "attempts",
    )

    assert result is None
    assert attempts == "1"

    print("Verification result:", result)
    print("Failed attempts:", attempts)
    print("PASSED")

    await redis_client.delete(redis_key)


async def test_maximum_attempts():
    print("\nTEST 5: Maximum five incorrect attempts")

    challenge_id, _ = await otp_manager.create_challenge(
        admin_id=789
    )

    redis_key = f"otp:challenge:{challenge_id}"

    results = []

    for attempt in range(1, 6):
        result = await otp_manager.verify_challenge(
            challenge_id,
            "000000",
        )

        results.append(result)

        print(f"Attempt {attempt}: {result}")

    exists = await redis_client.exists(redis_key)

    assert all(result is None for result in results)
    assert exists == 0

    print("Challenge deleted:", exists == 0)
    print("PASSED")


async def test_invalid_otp_format():
    print("\nTEST 6: Invalid OTP format")

    challenge_id, _ = await otp_manager.create_challenge(
        admin_id=123
    )

    redis_key = f"otp:challenge:{challenge_id}"

    invalid_values = [
        "12345",
        "1234567",
        "abcdef",
        "12ab56",
        "",
    ]

    for value in invalid_values:
        result = await otp_manager.verify_challenge(
            challenge_id,
            value,
        )

        assert result is None

    attempts = await redis_client.hget(
        redis_key,
        "attempts",
    )

    assert attempts == "0"

    print("Invalid OTP formats rejected")
    print("Attempts after invalid formats:", attempts)
    print("PASSED")

    await redis_client.delete(redis_key)


async def test_expired_challenge():
    print("\nTEST 7: Expired challenge")

    challenge_id, otp = await otp_manager.create_challenge(
        admin_id=123
    )

    redis_key = f"otp:challenge:{challenge_id}"

    await redis_client.expire(redis_key, 1)

    await asyncio.sleep(1.2)

    result = await otp_manager.verify_challenge(
        challenge_id,
        otp,
    )

    exists = await redis_client.exists(redis_key)

    assert result is None
    assert exists == 0

    print("Verification result:", result)
    print("Challenge exists:", bool(exists))
    print("PASSED")


async def test_concurrent_verification():
    print("\nTEST 8: Concurrent OTP verification")

    challenge_id, otp = await otp_manager.create_challenge(
        admin_id=123
    )

    results = await asyncio.gather(
        otp_manager.verify_challenge(challenge_id, otp),
        otp_manager.verify_challenge(challenge_id, otp),
    )

    assert results.count(123) == 1
    assert results.count(None) == 1

    print("Concurrent results:", results)
    print("Successful verifications:", results.count(123))
    print("Rejected verifications:", results.count(None))
    print("PASSED")


async def main():
    tests = [
        test_challenge_creation,
        test_correct_otp,
        test_otp_reuse,
        test_incorrect_otp,
        test_maximum_attempts,
        test_invalid_otp_format,
        test_expired_challenge,
        test_concurrent_verification,
    ]

    passed = 0

    try:
        print("=" * 50)
        print("OTP AUTHENTICATION TEST SUITE")
        print("=" * 50)

        for test in tests:
            await test()
            passed += 1

        print("\n" + "=" * 50)
        print(f"RESULT: {passed}/{len(tests)} TESTS PASSED")
        print("=" * 50)

    finally:
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
