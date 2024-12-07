# bot.py
# Classe TradingBotWorker: un worker per ogni DEX.

import asyncio
from PyQt5.QtCore import pyqtSignal, QObject
from config import HISTORY_LENGTH, FUTURE_STEPS, SPREAD_THRESHOLD, SLEEP_TIME, FEATURE_COLS, ORDER_SIZE
from utils import fetch_market_data, place_order, check_rug_pull
from ml_model import load_pretrained_model, train_model, predict

class TradingBotWorker(QObject):
    data_signal = pyqtSignal(dict, str)
    log_signal = pyqtSignal(str, str)
    chart_signal = pyqtSignal(float, str)
    
    def __init__(self, dex_name, endpoint, market_address, private_key):
        super().__init__()
        self.running = True
        self.data_buffer = []
        self.model = load_pretrained_model()
        self.position = 0.0
        self.dex_name = dex_name
        self.endpoint = endpoint
        self.market_address = market_address
        self.private_key = private_key
    
    async def run_bot(self):
        while self.running:
            new_data = await fetch_market_data(self.endpoint, self.market_address)
            if new_data is None:
                self.log_signal.emit("[WARNING] No market data retrieved.", self.dex_name)
                await asyncio.sleep(SLEEP_TIME)
                continue
            
            entry = [new_data["mid_price"], new_data["spread"], new_data["volume"]]
            self.data_buffer.append(entry)
            
            pred = None
            if len(self.data_buffer) > HISTORY_LENGTH + FUTURE_STEPS:
                self.model = train_model(self.model, self.data_buffer)
                pred = predict(self.model, self.data_buffer)
                
                is_rug = check_rug_pull(self.data_buffer)
                current_spread = self.data_buffer[-1][1]
                current_mid_price = self.data_buffer[-1][0]
                
                if current_spread > SPREAD_THRESHOLD or is_rug:
                    self.log_signal.emit("[ALERT] Potential rug pull detected.", self.dex_name)
                    if self.position > 0:
                        await place_order(self.endpoint, self.market_address, self.private_key, "sell", current_mid_price, self.position)
                        self.log_signal.emit(f"[EMERGENCY SELL] Sold all {self.position} @ {current_mid_price:.4f}", self.dex_name)
                        self.position = 0
                else:
                    # Semplice logica trading
                    if pred > 0.7:
                        await place_order(self.endpoint, self.market_address, self.private_key, "buy", current_mid_price, ORDER_SIZE)
                        self.position += ORDER_SIZE
                        self.log_signal.emit(f"[TRADE] BUY {ORDER_SIZE} @ {current_mid_price:.4f}, pred={pred:.4f}, pos={self.position}", self.dex_name)
                    elif pred < 0.3 and self.position > 0:
                        await place_order(self.endpoint, self.market_address, self.private_key, "sell", current_mid_price, ORDER_SIZE)
                        self.position -= ORDER_SIZE
                        self.log_signal.emit(f"[TRADE] SELL {ORDER_SIZE} @ {current_mid_price:.4f}, pred={pred:.4f}, pos={self.position}", self.dex_name)
                    else:
                        self.log_signal.emit(f"[HOLD] pred={pred:.4f}, pos={self.position}", self.dex_name)
            
            update_dict = {
                "mid_price": self.data_buffer[-1][0],
                "spread": self.data_buffer[-1][1],
                "pred": pred if pred is not None else None
            }
            self.data_signal.emit(update_dict, self.dex_name)
            self.chart_signal.emit(self.data_buffer[-1][0], self.dex_name)
            
            await asyncio.sleep(SLEEP_TIME)
    
    def stop(self):
        self.running = False
