

### `config.py`

# config.py
# Configurazione generale del bot

# Endpoint solana (devnet/mainnet)
RPC_ENDPOINT_MAIN = "https://api.mainnet-beta.solana.com"
RPC_ENDPOINT_DEV = "https://api.devnet.solana.com"

# Lista di DEX/market su cui operare.
# Ognuno deve avere:
# - name
# - endpoint
# - market_address
# - private_key (array di int generato da solana-keygen)
# - base_currency, quote_currency
DEX_CONFIGS = [
    {
        "name": "Serum_SOL_USDC_Devnet",
        "endpoint": RPC_ENDPOINT_DEV,
        "market_address": "Inserire_market_devnet",  # Inserire un market valido su devnet
        "private_key": [133, 56, 94, ...],  # Chiave devnet ottenuta da solana-keygen
        "base_currency": "SOL",
        "quote_currency": "USDC"
    },
    # Aggiungerne altri se necessario
]

HISTORY_LENGTH = 100
BATCH_SIZE = 32
FUTURE_STEPS = 5
SPREAD_THRESHOLD = 0.5
SLEEP_TIME = 5

FEATURE_COLS = ["mid_price", "spread", "volume"]

VOLUME_THRESHOLD = 1000   
PRICE_DROP_THRESHOLD = 0.1

PRETRAINED_MODEL_PATH = "model.h5"
ORDER_SIZE = 0.1
