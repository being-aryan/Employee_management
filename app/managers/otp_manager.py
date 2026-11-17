import hmac

from redis.asyncio import Redis

from app.utils.otp import (
    generate_challenge_id,
    generate_otp,
    generate_otp_digest,
)


class OTPManager:
    OTP_EXPIRY_SECONDS = 300
    MAX_ATTEMPTS = 5

    VERIFY_OTP_SCRIPT = """
    local stored_digest = redis.call('HGET', KEYS[1], 'otp_digest')

    if not stored_digest then
        return -1
    end

    if stored_digest ~= ARGV[1] then
        return -1
    end

    local attempts = tonumber(
        redis.call('HGET', KEYS[1], 'attempts') or '0'
    )

    if attempts >= tonumber(ARGV[3]) then
        redis.call('DEL', KEYS[1])
        return -2
    end

    if ARGV[2] == '1' then
        local admin_id = redis.call('HGET', KEYS[1], 'admin_id')
        redis.call('DEL', KEYS[1])
        return admin_id
    end

    attempts = redis.call('HINCRBY', KEYS[1], 'attempts', 1)

    if attempts >= tonumber(ARGV[3]) then
        redis.call('DEL', KEYS[1])
        return -2
    end

    return 0
    """

    def __init__(
        self,
        redis_client: Redis,
        secret_key: bytes,
    ) -> None:
        self.redis = redis_client
        self.secret_key = secret_key

    async def create_challenge(
        self,
        admin_id: int,
    ) -> tuple[str, str]:
        otp = generate_otp()
        challenge_id = generate_challenge_id()

        otp_digest = generate_otp_digest(
            otp,
            self.secret_key,
        )

        redis_key = f"otp:challenge:{challenge_id}"

        async with self.redis.pipeline(transaction=True) as pipeline:
            pipeline.hset(
                redis_key,
                mapping={
                    "admin_id": str(admin_id),
                    "otp_digest": otp_digest,
                    "attempts": "0",
                },
            )
            pipeline.expire(
                redis_key,
                self.OTP_EXPIRY_SECONDS,
            )
            await pipeline.execute()

        return challenge_id, otp

    async def verify_challenge(
        self,
        challenge_id: str,
        submitted_otp: str,
    ) -> int | None:
        if not submitted_otp.isdigit() or len(submitted_otp) != 6:
            return None

        redis_key = f"otp:challenge:{challenge_id}"

        stored_digest = await self.redis.hget(
            redis_key,
            "otp_digest",
        )

        if stored_digest is None:
            return None

        submitted_digest = generate_otp_digest(
            submitted_otp,
            self.secret_key,
        )

        is_valid = hmac.compare_digest(
            stored_digest,
            submitted_digest,
        )

        result = await self.redis.eval(
            self.VERIFY_OTP_SCRIPT,
            1,
            redis_key,
            stored_digest,
            "1" if is_valid else "0",
            self.MAX_ATTEMPTS,
        )

        if isinstance(result, bytes):
            result = result.decode("utf-8")

        try:
            admin_id = int(result)
        except (TypeError, ValueError):
            return None

        return admin_id if admin_id > 0 else None
