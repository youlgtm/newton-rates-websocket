import aiohttp
import logging
from src.cache.redis_cache import RedisCache

logger = logging.getLogger(__name__)
# TODO: Make this more generic, we could use this for other currencies. 
async def fetch_usd_cad_rate(session: aiohttp.ClientSession, redis_cache: RedisCache = None) -> float:
    try:
        if redis_cache:
            cached_rate = await redis_cache.get("usd_cad_rate")
            if cached_rate:
                logger.info("Using cached USD/CAD rate")
                return float(cached_rate)

        async with session.get('https://api.kraken.com/0/public/Ticker?pair=USDCAD') as response:
            if response.status == 200:
                data = await response.json()
                rate = float(data["result"]["ZUSDZCAD"]["c"][0])
                if redis_cache:
                    await redis_cache.set("usd_cad_rate", rate)
                return rate
    except Exception as e:
        logger.error(f"Error fetching USD/CAD rate: {e}")
    return 1.35