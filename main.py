import asyncio
import logging
import sys
import websockets
from src.config.constants import WEBSOCKET_HOST, WEBSOCKET_PORT, REDIS_URL
from src.cache.redis_cache import RedisCache
from src.providers.rate_provider import RateProvider
from src.websocket.rate_websocket import RateWebSocketHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

async def main(): 
    try:
        redis_cache = RedisCache(REDIS_URL, ttl_seconds=10)
        rate_service = RateProvider(redis_cache)
        rate_handler = RateWebSocketHandler(rate_service, update_interval=10)

        await rate_handler.start_updates()

        async def path_handler(websocket, path):
            if path == '/markets/ws':
                await rate_handler.handle_message(websocket)
            else:
                await websocket.close(1008, f"Unsupported path: {path}")
        
        server = await websockets.serve(
            rate_handler.handle_message, 
            WEBSOCKET_HOST, 
            WEBSOCKET_PORT
        )
        
        logger.info(f"WebSocket server started on ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}")
        
        try:
            await server.wait_closed()
        finally:
            await rate_handler.stop_updates()
            await redis_cache.close()
            
    except Exception as e:
        logger.error(f"Failed to start WebSocket server: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())