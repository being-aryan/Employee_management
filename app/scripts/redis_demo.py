import asyncio

from app.redis_client import redis_client


async def main() -> None:
    try:
        await redis_client.set(
            "learning:username",
            "aryan",
            ex=30,
        )

        username = await redis_client.get("learning:username")
        print("Username:", username)

        exists = await redis_client.exists("learning:username")
        print("Key exists:", exists)

        ttl = await redis_client.ttl("learning:username")
        print("Remaining TTL:", ttl)

        deleted = await redis_client.delete("learning:username")
        print("Deleted:", deleted)

    finally:
        await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
