from typing import List, Dict, Any
import aiohttp
import logging
from src.cache.redis_cache import RedisCache
from src.config.constants import SUPPORTED_ASSETS, NEWTON_API_URL, BINANCE_API_URL, KRAKEN_API_URL
from src.utils.api_retry import retry_async_function
from src.utils.currency_conversion import fetch_usd_cad_rate
import asyncio
import time

logger = logging.getLogger(__name__)
# INFO: This class is responsible for fetching all the rates for the supported assets.
class RateProvider:
    def __init__(self, redis_cache: RedisCache):
        self.redis_cache = redis_cache
        self.assets_not_supported = set()
        
    # INFO: Since we are using asyncio, one optimization is to parallel process API requests, but that is overkill for this.
    # instead of fetching in paralle and having to deal with threads, we can just use asyncio gather to fetch them concurrently.
    async def fetch_all_rates(self) -> List[Dict[str, Any]]:

        # INFO: Benchmarking API calls 
        start_time = time.time()
        timings = {
            'newton': 0,
            'binance': 0,
            'kraken': 0,
            'total': 0
        }

        async with aiohttp.ClientSession() as session:
            newton_start = time.time()
            newton_task = retry_async_function(
                self.fetch_newton_rates,
                session,
                retries=3,
                initial_delay=0.1
            )
            usd_cad_task = retry_async_function(
                fetch_usd_cad_rate,
                session,
                self.redis_cache,
                retries=3,
                initial_delay=0.1
            )
            
            newton_rates, usd_cad_rate = await asyncio.gather(
                newton_task, 
                usd_cad_task
            )

            timings['newton'] = time.time() - newton_start
            
            if not newton_rates or not usd_cad_rate:
                logger.error("Failed to fetch initial rates")
                return []

            # INFO: Compute the missing assets
            # TODO: We could use a better way to identify assets instead of splitting the symbol, we could also deduplicate before.
            available_assets = {rate["symbol"].split("_")[0] for rate in newton_rates}
            missing_assets = set(SUPPORTED_ASSETS) - available_assets
            
            if not missing_assets:
                timings['total'] = time.time() - start_time
                return newton_rates

            binance_start = time.time()
            api_data = await self.process_missing_assets(missing_assets, session, usd_cad_rate) 

            timings['binance'] = time.time() - binance_start
            
            timings['total'] = time.time() - start_time
            logger.info(f"Rate fetching timings: {timings}")
            
            return newton_rates + api_data + self.populate_assets_not_supported()
    # INFO: We are populating the assets after checking with Kraken, could be removed if we don't need to return them.
    def populate_assets_not_supported(self) -> List[Dict[str, Any]]:
        return [{"symbol": f"{asset}_CAD", "ask": 0, "bid": 0, "spot": 0, "change": 0} for asset in self.assets_not_supported]

    async def process_missing_assets(
        self, 
        missing_asset_list: List[str], 
        session: aiohttp.ClientSession, 
        usd_cad_rate: float
    ) -> List[Dict[str, Any]]:

        binance_tasks = [
            self.binance_with_retry(asset, session, usd_cad_rate)
            for asset in missing_asset_list
        ]
        binance_results = await asyncio.gather(*binance_tasks)
        
        # INFO: Any failed assets will be funneled to Kraken by checking if Binance did not produce a result for an asset. 
        failed_assets = []
        valid_results = []
        
        for asset, result in zip(missing_asset_list, binance_results):
            if result is None:
                failed_assets.append(asset)
            else:
                valid_results.append(result)
        
        if failed_assets:
            kraken_tasks = [
                self.kraken_with_retry(asset, session, usd_cad_rate)
                for asset in failed_assets
            ]
            kraken_results = await asyncio.gather(*kraken_tasks)
            valid_results.extend([result for result in kraken_results if result is not None])
        
        return valid_results

    async def binance_with_retry(
        self, 
        asset: str, 
        session: aiohttp.ClientSession, 
        usd_cad_rate: float
    ) -> Dict[str, Any] | None:
        try:
            return await retry_async_function(
                self.fetch_binance_rate,
                asset,
                session,
                usd_cad_rate,
                retries=2,
                initial_delay=0.2
            )
        except Exception as e:
            logger.warning(f"Binance fetch failed for {asset}: {e}")
            return None

    async def kraken_with_retry(
        self, 
        asset: str, 
        session: aiohttp.ClientSession, 
        usd_cad_rate: float
    ) -> Dict[str, Any] | None:
        try:
            return await retry_async_function(
                self.fetch_kraken_rate,
                asset,
                session,
                usd_cad_rate,
                retries=2,
                initial_delay=0.2
            )
        except Exception as e:
            logger.warning(f"Kraken fetch failed for {asset}: {e}")
            return None

    # INFO: These all contain the fetching logic for the difrerent APIs, we also check the cache first before fetching.
    # INFO: We are funelling missing assets through the diferent APIs, with Newton as the starting layer. 
    async def fetch_newton_rates(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        try:
            cached_rates = await self.redis_cache.get("newton_rates")
            if cached_rates:
                logger.info("Fetched Newton rates from cache")
                return cached_rates
            else:
                async with session.get(NEWTON_API_URL) as response:
                    if response.status != 200:
                        raise Exception(f"Newton API failed with status code: {response.status}")
                    data = await response.json()
                    rates =  [
                        rate for rate in data 
                        if rate["symbol"].split("_")[0] in SUPPORTED_ASSETS
                    ]
                    await self.redis_cache.set("newton_rates", rates)
                    return rates
        except Exception as e:
            logger.error(f"Error fetching Newton rates: {e}")
            return []

    async def fetch_binance_rate(self, asset: str, session: aiohttp.ClientSession, usd_cad_rate: float) -> Dict[str, Any]:
        try:
            cache_key = f"binance_rate_{asset}"

            cached_rate = await self.redis_cache.get(cache_key)
            if cached_rate:
                logger.info(f"Fetched Binance rate for {asset} from cache")
                return cached_rate
            else:
                async with session.get(f'{BINANCE_API_URL}?symbol={asset}USDT') as response:
                    if response.status != 200:
                        raise Exception(f"Binance API failed with status code: {response.status}")
                    data = await response.json()
                    rate = {
                        "symbol": f"{asset}_CAD",
                        "ask": float(data["askPrice"]) * usd_cad_rate,
                        "bid": float(data["bidPrice"]) * usd_cad_rate,
                        "spot": float(data["lastPrice"]) * usd_cad_rate,
                        "change": float(data["priceChangePercent"])
                    }
                    # TODO: We can add better validation here, sometimes Binace has no data for an asset, but will still return a response.
                    if rate["ask"] == 0 and rate["bid"] == 0 and rate["spot"] == 0:
                        raise Exception(f"Invalid response from Binance for {asset}")
                    await self.redis_cache.set(cache_key, rate)
                    return rate
        except Exception as e:
            logger.error(f"Error fetching Binance rate for {asset}: {e}")
            return None

    async def fetch_kraken_rate(self, asset: str, session: aiohttp.ClientSession, usd_cad_rate: float) -> Dict[str, Any]:
        try:
            cache_key = f"kraken_rate_{asset}"
            
            cached_rate = await self.redis_cache.get(cache_key)
            if cached_rate:
                logger.info(f"Using cached Kraken rate for {asset}")
                return cached_rate

            async with session.get(f'{KRAKEN_API_URL}?pair={asset}USD') as response:
                if response.status != 200:
                    raise Exception(f"Kraken API failed with status code: {response.status}")
                
                data = await response.json()
                if "result" not in data or f"{asset}USD" not in data["result"]:
                    self.assets_not_supported.add(asset)
                    raise Exception(f"Invalid response from Kraken for {asset}")
                    
                result = data["result"][f"{asset}USD"]
                rate = {
                    "symbol": f"{asset}_CAD",
                    "ask": float(result["a"][0]) * usd_cad_rate,
                    "bid": float(result["b"][0]) * usd_cad_rate,
                    "spot": float(result["c"][0]) * usd_cad_rate,
                    "change": (float(result["c"][0]) - float(result["o"])) / float(result["o"]) * 100
                }
                
                await self.redis_cache.set(cache_key, rate)
                return rate
                
        except Exception as e:
            logger.error(f"Error fetching Kraken rate for {asset}: {e}")
            return None