# risk_management.py
# Gestione del rischio: stop loss, take profit

from config import STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT
import logging

logger = logging.getLogger("bot_logger")

def check_stop_loss_take_profit(position, avg_entry_price, current_price):
    """
    Controlla condizioni di stop loss e take profit.
    Ritorna (action, size_to_sell)
    action può essere: "stop_loss", "take_profit_part" o "none".
    """
    if position <= 0:
        return "none", 0
    drop = (avg_entry_price - current_price) / avg_entry_price
    gain = (current_price - avg_entry_price) / avg_entry_price
    if drop > STOP_LOSS_PERCENT:
        logger.info("Stop loss triggered.")
        return "stop_loss", position
    elif gain > TAKE_PROFIT_PERCENT:
        size_to_sell = position / 2
        logger.info("Take profit triggered.")
        return "take_profit_part", size_to_sell
    else:
        return "none", 0
