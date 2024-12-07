
### `config.py`

# config.py
# Configurazione generale del bot.

# Endpoint Solana
RPC_ENDPOINT_MAIN = "https://api.mainnet-beta.solana.com"
RPC_ENDPOINT_DEV = "https://api.devnet.solana.com"

# Lista di DEX/market: multi-DEX support
# Inserire market validi e chiavi private appropriate.
DEX_CONFIGS = [
    {
        "name": "Serum_SOL_USDC_Devnet",
        "endpoint": RPC_ENDPOINT_DEV,
        "market_address": "Inserire_market_devnet",  # Inserire un vero indirizzo di mercato Devnet
        "private_key": [133, 56, 94, ...],  # Chiave privata in forma di array di byte
        "base_currency": "SOL",
        "quote_currency": "USDC"
    },
    # Aggiungere altri DEX se necessario
]

# Parametri ML e Dati
HISTORY_LENGTH = 100
BATCH_SIZE = 32
FUTURE_STEPS = 5

# Feature columns (incluso ma_10 e volatility_10)
FEATURE_COLS = ["mid_price", "spread", "volume", "ma_10", "volatility_10"]

# Parametri Trading
SPREAD_THRESHOLD = 0.5
SLEEP_TIME = 5
ORDER_SIZE_BASE = 0.1  # Dimensione base dell'ordine

# Rug pull detection
VOLUME_THRESHOLD = 1000   
PRICE_DROP_THRESHOLD = 0.1

# Modello pre-addestrato (da hypertuning)
PRETRAINED_MODEL_PATH = "model.h5"

# Risk Management
STOP_LOSS_PERCENT = 0.05    # Stop loss al -5%
TAKE_PROFIT_PERCENT = 0.1   # Take profit al +10%
