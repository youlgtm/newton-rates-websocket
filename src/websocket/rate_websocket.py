import json
import logging
from typing import Dict, Any
import websockets
from src.providers.rate_provider import RateProvider
import asyncio
from src.utils.validation import validate_response

logger = logging.getLogger(__name__)

class RateWebSocketHandler:
    def __init__(self, rate_service: RateProvider, update_interval: float = 10.0):
        self.rate_service = rate_service
        self.update_interval = update_interval
        self.connected_clients: Set[websockets.WebSocketServerProtocol] = set()
        self.cron_task = None

    # INFO: Start the crong job as a non-blocking function/separate coroutine.
    async def start_updates(self):
        self.cron_task = asyncio.create_task(self._cron_rate_update())

    async def stop_updates(self):
        if self.cron_task:
            self.cron_task.cancel()
            try:
                await self.cron_task
            except asyncio.CancelledError:
                pass
    # INFO: This is the cron job that will push the rates to the clients at a given interval.
    # INFO: Private function to be called by the start_updates.
    async def _cron_rate_update(self):
        while True:
            try:
                rates = await self.rate_service.fetch_all_rates()
                if rates:
                    response = {
                        "channel": "rates",
                        "event": "update",
                        "data": rates
                    }
                    await self.broadcast(response)
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                logger.error(f"Error in periodic updates: {e}")
                await asyncio.sleep(1) 

    async def broadcast(self, message: Dict):
        disconnected_clients = set()
        for client in self.connected_clients:
            try:
                await client.send(json.dumps(message))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")
                disconnected_clients.add(client)
        
        self.connected_clients -= disconnected_clients
    # INFO: This is the entry point for the client connection to the websocket. 
    async def handle_message(self, websocket: websockets.WebSocketServerProtocol):
        try:
            self.connected_clients.add(websocket)
            async for message in websocket:
                data = json.loads(message)
                logger.info(f"Received message: {data.get('event')} for channel: {data.get('channel')}")

                if data.get("event") == "subscribe" and data.get("channel") == "rates":
                    rates = await self.rate_service.fetch_all_rates()
                    
                    response = {
                        "channel": "rates",
                        "event": "data",
                        "data": rates
                    }
                    
                    if not validate_response(response):
                        error_response = {
                            "channel": "rates",
                            "event": "error",
                            "message": "Invalid rate data format"
                        }
                        await websocket.send(json.dumps(error_response))
                        continue
                    
                    await websocket.send(json.dumps(response))
                
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"Error handling websocket message: {str(e)}")
        finally:
            self.connected_clients.remove(websocket)