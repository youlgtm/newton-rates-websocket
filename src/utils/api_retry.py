import asyncio
import logging

logger = logging.getLogger(__name__)

# INFO: This function will try a function once and then retry a specified amount of time with an exponential backoff. 
async def retry_async_function(
    func,
    *args,
    retries=3,
    initial_delay=0.1,
    max_delay=10,
    exponential_backoff_rate=2,
    **kwargs
) -> list[dict[str, any]]:

    delay = initial_delay

    for attempt in range(retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            if attempt == retries:
                logger.error(f"All retries failed for the function: {func.__name__}, error: {str(e)}")
                return None

            delay = min(delay * exponential_backoff_rate, max_delay)

            logger.warning(
                f"{func.__name__} failed (attempt {attempt + 1}/{retries + 1}), error: {str(e)}. "
                f"Retrying in {delay:.2f}s"
            )
            await asyncio.sleep(delay)

    return None