from typing import Any
import json
from redis.asyncio import Redis

# TODO: Add logging
# INFO: This Redis cache is used to store the conversion rates and the rates for each asset.
# INFO: We use this to avoid making repeated calls to the external APIs, which reduces latency for our clients.
# INFO: We set a default TTL of 10 seconds to resemble the upate time on the newton site. 
class RedisCache:
    def __init__(self, redis_url: str = 'redis://localhost', ttl_seconds: int = 10):
        self.redis = Redis.from_url(redis_url, decode_responses=True)
        self.ttl_seconds = ttl_seconds

    async def get(self, key: str) -> Any:
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any) -> None:
        str_value = json.dumps(value)
        await self.redis.set(
            key,
            str_value,
            ex=self.ttl_seconds
        )

    async def close(self):
        await self.redis.close()