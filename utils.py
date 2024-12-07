# utils.py
# Funzioni di utilità: fetch dati, volume, label, place_order, rug pull detection.

import time
import numpy as np
from pyserum.market import Market
from pyserum.connection import conn
from pyserum.enums import OrderType, Side
from solana.keypair import Keypair
from solana.rpc.api import Client
from config import (HISTORY_LENGTH, FUTURE_STEPS, FEATURE_COLS, 
                    VOLUME_THRESHOLD, PRICE_DROP_THRESHOLD)
from solana.rpc.async_api import AsyncClient

async def fetch_market_data(endpoint, market_address):
    """
    Fetch dei dati di mercato dal DEX (Serum).
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
        
        volume = estimate_volume(market, levels=5)
        
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
    Stima il volume dai primi livelli di bid e ask.
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
    Genera label per training incrementale:
    1 se prezzo futuro > prezzo attuale, 0 altrimenti.
    """
    y = []
    mid_prices = [d[0] for d in data_buffer]  
    for i in range(HISTORY_LENGTH, len(data_buffer)-FUTURE_STEPS):
        future_price = mid_prices[i+FUTURE_STEPS]
        current_price = mid_prices[i]
        y.append(1 if future_price > current_price else 0)
    return np.array(y)

async def place_order(endpoint, market_address, private_key, order_type, price, size):
    """
    Piazza un ordine su Serum.
    Da testare su devnet.
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
            limit_price = float(price),
            max_quantity = float(size),
            order_type = OrderType.LIMIT
        )
        result = client.send_transaction(tx, payer)
        client.confirm_transaction(result["result"])
        print(f"[ORDER] {order_type.upper()} {size} @ {price} on {market_address}")
    except Exception as e:
        print(f"[ERROR] place_order failed on {market_address}: {e}")

def check_rug_pull(data_buffer):
    """
    Heuristics rug pull:
    - Volume basso
    - Crollo prezzo
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
