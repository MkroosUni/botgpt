# utils.py
# Funzioni di utilità: fetch dati, volume, label, invio ordini, rug pull, feature engineering.

import time
import numpy as np
from pyserum.market import Market
from pyserum.connection import conn
from pyserum.enums import OrderType, Side
from solana.keypair import Keypair
from solana.rpc.api import Client
from solana.rpc.async_api import AsyncClient
from config import (HISTORY_LENGTH, FUTURE_STEPS, FEATURE_COLS, 
                    VOLUME_THRESHOLD, PRICE_DROP_THRESHOLD)
import logging

logger = logging.getLogger("bot_logger")

async def fetch_market_data(endpoint, market_address):
    """
    Recupera dati dal DEX (order book) e calcola mid_price, spread, volume stimato.
    Se non riesce, ritorna None.
    """
    async with AsyncClient(endpoint) as client:
        http_conn = conn.HTTPConnection(endpoint)
        market = Market.load(http_conn, market_address)
        
        bids = market.load_bids()
        asks = market.load_asks()

        best_bid = next(bids, None)
        best_ask = next(asks, None)
        
        if best_bid is None or best_ask is None:
            return None
        
        spread = best_ask.price - best_bid.price
        mid_price = (best_ask.price + best_bid.price) / 2.0
        volume = estimate_volume(market, 5)
        
        data = {
            "mid_price": mid_price,
            "best_bid": best_bid.price,
            "best_ask": best_ask.price,
            "spread": spread,
            "volume": volume,
            "timestamp": time.time()
        }
        return data

def estimate_volume(market: Market, levels=5):
    """
    Stima il volume guardando i primi 'levels' di bid e ask.
    """
    bids = market.load_bids()
    asks = market.load_asks()
    bid_list = []
    ask_list = []
    for i, b in zip(range(levels), bids.items()):
        bid_list.append(b)
    for i, a in zip(range(levels), asks.items()):
        ask_list.append(a)
    vol = sum([b.size for b in bid_list]) + sum([a.size for a in ask_list])
    return vol

def generate_labels(data_buffer):
    """
    Genera le label per il training:
    1 se il prezzo futuro (FUTURE_STEPS avanti) > prezzo attuale, altrimenti 0.
    """
    mid_prices = [d[0] for d in data_buffer]
    y = []
    for i in range(HISTORY_LENGTH, len(data_buffer)-FUTURE_STEPS):
        future_price = mid_prices[i+FUTURE_STEPS]
        current_price = mid_prices[i]
        y.append(1 if future_price > current_price else 0)
    return np.array(y)

async def place_order(endpoint, market_address, private_key, order_type, price, size):
    """
    Piazza un ordine sul DEX Serum.
    Necessita chiave privata e fondi nel wallet.
    """
    payer = Keypair.from_secret_key(bytes(private_key))
    client = Client(endpoint)
    http_conn = conn.HTTPConnection(endpoint)
    market = Market.load(http_conn, market_address)
    side = Side.BUY if order_type.lower() == "buy" else Side.SELL
    try:
        tx = market.place_order(
            owner = payer,
            payer = payer.public_key,
            side = side,
            limit_price=float(price),
            max_quantity=float(size),
            order_type=OrderType.LIMIT
        )
        result = client.send_transaction(tx, payer)
        client.confirm_transaction(result["result"])
        logger.info(f"[ORDER] {order_type.upper()} {size} @ {price} on {market_address}")
    except Exception as e:
        logger.error(f"place_order failed on {market_address}: {e}")

def check_rug_pull(data_buffer):
    """
    Heuristic rug pull detection:
    - Volume molto basso.
    - Crollo del prezzo > PRICE_DROP_THRESHOLD.
    """
    if len(data_buffer) < 10:
        return False
    volumes = [d[2] for d in data_buffer]
    recent_vol = np.mean(volumes[-10:])
    if recent_vol < VOLUME_THRESHOLD:
        return True
    prices = [d[0] for d in data_buffer]
    recent_prices = prices[-10:]
    start_price = recent_prices[0]
    end_price = recent_prices[-1]
    drop = (start_price - end_price) / start_price
    if drop > PRICE_DROP_THRESHOLD:
        return True
    return False

def add_features(data_buffer):
    """
    Aggiunge ma_10 e volatility_10 all'ultima entry di data_buffer.
    ma_10: media mobile a 10 step del prezzo
    volatility_10: std dei log-return su 10 step
    """
    if len(data_buffer) < 10:
        ma_10 = data_buffer[-1][0]
        volatility_10 = 0.0
    else:
        prices = [d[0] for d in data_buffer[-10:]]
        ma_10 = np.mean(prices)
        returns = np.diff(np.log(prices))
        volatility_10 = np.std(returns)
    data_buffer[-1].append(ma_10)
    data_buffer[-1].append(volatility_10)
