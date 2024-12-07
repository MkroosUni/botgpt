# bot.py
# Worker per ciascun DEX. Si occupa di fetch dati, ML, ordini, risk management.

import asyncio
from PyQt5.QtCore import pyqtSignal, QObject
from config import (HISTORY_LENGTH, FUTURE_STEPS, SPREAD_THRESHOLD, SLEEP_TIME, FEATURE_COLS, ORDER_SIZE_BASE)
from utils import fetch_market_data, place_order, check_rug_pull, add_features
from ml_model import load_pretrained_model, train_model, predict
from risk_management import check_stop_loss_take_profit
import logging
import csv
import os   # AGGIUNTA: per controllare file CSV

logger = logging.getLogger("bot_logger")

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
        self.avg_entry_price = 0.0
        self.dex_name = dex_name
        self.endpoint = endpoint
        self.market_address = market_address
        self.private_key = private_key

        # AGGIUNTA: Nome file dati live
        self.data_file = 'live_data.csv'
        # Se il file non esiste, scriviamo l’header
        if not os.path.exists(self.data_file):
            with open(self.data_file, 'w', newline='') as f:
                writer = csv.writer(f)
                # Header con le metriche che otteniamo da fetch_market_data
                writer.writerow(["timestamp", "mid_price", "best_bid", "best_ask", "spread", "volume"])
    
    async def run_bot(self):
        while self.running:
            new_data = await fetch_market_data(self.endpoint, self.market_address)
            if new_data is None:
                self.log_signal.emit("[WARNING] No market data retrieved.", self.dex_name)
                logger.warning(f"{self.dex_name}: No market data retrieved.")
                await asyncio.sleep(SLEEP_TIME)
                continue
            
            # AGGIUNTA: Salviamo i dati grezzi ottenuti live su CSV
            with open(self.data_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    new_data["timestamp"], 
                    new_data["mid_price"], 
                    new_data["best_bid"], 
                    new_data["best_ask"],
                    new_data["spread"],
                    new_data["volume"]
                ])
            
            # Aggiunge i dati base
            self.data_buffer.append([new_data["mid_price"], new_data["spread"], new_data["volume"]])
            # Aggiunge feature avanzate
            add_features(self.data_buffer)
            
            pred = None
            if len(self.data_buffer) > HISTORY_LENGTH + FUTURE_STEPS:
                # Training incrementale
                self.model = train_model(self.model, self.data_buffer)
                pred = predict(self.model, self.data_buffer)
                
                current_price = self.data_buffer[-1][0]
                # Risk management: stop loss / take profit
                action, size_to_sell = check_stop_loss_take_profit(self.position, self.avg_entry_price, current_price)
                if action == "stop_loss":
                    await place_order(self.endpoint, self.market_address, self.private_key, "sell", current_price, size_to_sell)
                    self.position -= size_to_sell
                    self.log_signal.emit(f"[RISK] Stop loss executed, sold {size_to_sell}", self.dex_name)
                elif action == "take_profit_part":
                    await place_order(self.endpoint, self.market_address, self.private_key, "sell", current_price, size_to_sell)
                    self.position -= size_to_sell
                    self.log_signal.emit(f"[RISK] Take profit, sold {size_to_sell}", self.dex_name)

                # Rug pull check
                is_rug = check_rug_pull(self.data_buffer)
                current_spread = self.data_buffer[-1][1]
                if current_spread > SPREAD_THRESHOLD or is_rug:
                    self.log_signal.emit("[ALERT] Potential rug pull detected.", self.dex_name)
                    logger.warning(f"{self.dex_name}: Potential rug pull detected.")
                    if self.position > 0:
                        await place_order(self.endpoint, self.market_address, self.private_key, "sell", current_price, self.position)
                        self.log_signal.emit(f"[EMERGENCY SELL] Sold all {self.position}", self.dex_name)
                        self.position = 0
                else:
                    # Position sizing dinamico in base a predizione
                    if pred > 0.9:
                        order_size = ORDER_SIZE_BASE * 2
                    elif pred > 0.7:
                        order_size = ORDER_SIZE_BASE
                    elif pred > 0.5:
                        order_size = ORDER_SIZE_BASE * 0.5
                    else:
                        order_size = 0

                    if order_size > 0:
                        # BUY
                        await place_order(self.endpoint, self.market_address, self.private_key, "buy", current_price, order_size)
                        total_cost = self.avg_entry_price * self.position + current_price * order_size
                        self.position += order_size
                        self.avg_entry_price = total_cost / self.position
                        self.log_signal.emit(f"[TRADE] BUY {order_size} @ {current_price:.4f}, pred={pred:.4f}, pos={self.position}", self.dex_name)
                    elif pred < 0.3 and self.position > 0:
                        # SELL
                        sell_size = min(self.position, ORDER_SIZE_BASE)
                        await place_order(self.endpoint, self.market_address, self.private_key, "sell", current_price, sell_size)
                        self.position -= sell_size
                        self.log_signal.emit(f"[TRADE] SELL {sell_size} @ {current_price:.4f}, pred={pred:.4f}, pos={self.position}", self.dex_name)
                    else:
                        # HOLD
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
