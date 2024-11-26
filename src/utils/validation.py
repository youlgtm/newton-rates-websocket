from typing import Dict, Any, List
import logging
from datetime import datetime
from src.config.constants import SUPPORTED_ASSETS

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    pass

# INFO: Validate the response that we are sending to the client. 
def validate_response(response: Dict[str, Any]) -> bool:
    try:
        required_fields = {"channel", "event", "data"}
        if not all(field in response for field in required_fields):
            raise ValidationError("Missing required top-level fields")
            
        if response["channel"] != "rates":
            raise ValidationError(f"Invalid channel: {response['channel']}")
            
        if response["event"] not in ["data", "update", "error"]:
            raise ValidationError(f"Invalid event type: {response['event']}")
            
        if response["event"] == "error":
            if not isinstance(response.get("message"), str):
                raise ValidationError("Error response must include message string")
            return True
            
        if not isinstance(response["data"], list):
            raise ValidationError("Data must be an array")

        if(response["data"] and len(response["data"]) != len(SUPPORTED_ASSETS)):
            raise ValidationError("Data must contain all supported assets")

        for rate in response["data"]:
            if not validate_rate(rate):
                return False
                
        return True
        
    except ValidationError as e:
        logger.error(f"Response validation step error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in validation step: {str(e)}")
        return False


def validate_rate(rate: Dict[str, Any]) -> bool:

    required_fields = {
        "symbol": str,
        "bid": (int, float),
        "ask": (int, float),
        "spot": (int, float),
        "change": (int, float)
    }
    
    try:
        for field, expected_type in required_fields.items():
            if field not in rate:
                raise ValidationError(f"Missing required field: {field}")
            if not isinstance(rate[field], expected_type):
                raise ValidationError(f"Invalid type for {field}: expected {expected_type}, got {type(rate[field])}")
        
        # TODO: Can generalize this to work with other suffixes.
        if not rate["symbol"].endswith("_CAD"):
            raise ValidationError(f"Invalid symbol format: {rate['symbol']}")
            
        if rate["bid"] < 0 or rate["ask"] < 0 or rate["spot"] < 0:
            raise ValidationError("Price values cannot be negative")
            
        if rate["ask"] < rate["bid"]:
            raise ValidationError("Ask price cannot be less than bid price")
            
        return True
        
    except ValidationError as e:
        logger.error(f"Rate validation step error: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in rate validation step: {str(e)}")
        return False