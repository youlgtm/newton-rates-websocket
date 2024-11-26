import os
from dotenv import load_dotenv

load_dotenv()

WEBSOCKET_PORT = int(os.getenv('PORT', 8765)) 
WEBSOCKET_HOST = "0.0.0.0" 
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost')

# INFO: We had to use three services to fetach all the rates for the supported assets
# Newton api did not support all assets anymore, so we had to add Binance and Kraken.
# If any of the assets is not supported by Newton, the rate provider will fetch the rates from Binance or Kraken.
# INFO: We use Kraken for USD/CAD conversion.
# INFO: QCAD is not supported by any of the services
NEWTON_API_URL = 'https://api.newton.co/markets/v1.1/rates/'
BINANCE_API_URL = 'https://api.binance.com/api/v3/ticker/24hr'
KRAKEN_API_URL = 'https://api.kraken.com/0/public/Ticker'


SUPPORTED_ASSETS = [
    "BTC", "ETH", "LTC", "XRP", "BCH", "USDC", "XMR", "XLM",
    "USDT", "QCAD", "DOGE", "LINK", "MATIC", "UNI", "COMP", "AAVE", "DAI",
    "SUSHI", "SNX", "CRV", "DOT", "YFI", "MKR", "PAXG", "ADA", "BAT", "ENJ",
    "AXS", "DASH", "EOS", "BAL", "KNC", "ZRX", "SAND", "GRT", "QNT", "ETC",
    "ETHW", "1INCH", "CHZ", "CHR", "SUPER", "ELF", "OMG", "FTM", "MANA",
    "SOL", "ALGO", "LUNC", "UST", "ZEC", "XTZ", "AMP", "REN", "UMA", "SHIB",
    "LRC", "ANKR", "HBAR", "EGLD", "AVAX", "ONE", "GALA", "ALICE", "ATOM",
    "DYDX", "CELO", "STORJ", "SKL", "CTSI", "BAND", "ENS", "RNDR", "MASK", "APE"
] # 75 assets