# Newton Rates Websocket Server 

#### Features:

- Pub/Sub architecture (Broadcasts to all subscribed clients)
- Event and channel based communication
- Multi-api data aggregation (Newton, Binance, Kraken)
- Concurrent API request logic
- Retry logic with exponential backoff
- Redis caching with expiration
- Response validation
- Logging

### Endpoint: 
    "wss://newton-websocket-server-f3fc73957856.herokuapp.com/markets/ws";

### Subscription Message:
    {
      "event": "subscribe",
      "channel":"rates"
    }

### Response Message:
    {
    "channel": "rates",
    "event": "data",
    "data": {
    "symbol": "BTC_CAD",
    "timestamp": 1718707723,
    "bid": 88973.83,
    "ask": 91044,
    "spot": 90008.92,
    "change": -0.49
      }
    }

### Assets Supported:
    assets = [
    "BTC", "ETH", "LTC", "XRP", "BCH", "USDC", "XMR", "XLM",
    "USDT", "QCAD", "DOGE", "LINK", "MATIC", "UNI", "COMP", "AAVE", "DAI",
    "SUSHI", "SNX", "CRV", "DOT", "YFI", "MKR", "PAXG", "ADA", "BAT", "ENJ",
    "AXS", "DASH", "EOS", "BAL", "KNC", "ZRX", "SAND", "GRT", "QNT", "ETC",
    "ETHW", "1INCH", "CHZ", "CHR", "SUPER", "ELF", "OMG", "FTM", "MANA",
    "SOL", "ALGO", "LUNC", "UST", "ZEC", "XTZ", "AMP", "REN", "UMA", "SHIB",
    "LRC", "ANKR", "HBAR", "EGLD", "AVAX", "ONE", "GALA", "ALICE", "ATOM",
    "DYDX", "CELO", "STORJ", "SKL", "CTSI", "BAND", "ENS", "RNDR", "MASK",
    "APE"
    ]

### Architecture:

![websocket-newton](https://github.com/user-attachments/assets/83a0a557-ecbf-4a41-bbd0-7ab97e21cd7f)
