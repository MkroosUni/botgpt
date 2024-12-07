# main.py
# Entry point del programma. Crea GUI, avvia i worker per ciascun DEX, gestisce stop e chiusura.

import sys
import asyncio
import threading
import logging
from logging.handlers import RotatingFileHandler
from PyQt5.QtWidgets import QApplication
from ui import MainWindow
from bot import TradingBotWorker
from config import DEX_CONFIGS

logger = logging.getLogger("bot_logger")
logger.setLevel(logging.INFO)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

fh = RotatingFileHandler("bot.log", maxBytes=1000000, backupCount=5)
fh.setLevel(logging.INFO)
fh.setFormatter(formatter)

logger.addHandler(ch)
logger.addHandler(fh)

async def run_bots(app, window, bot_workers):
    await asyncio.gather(*[bw.run_bot() for bw in bot_workers])
    app.quit()

def main():
    app = QApplication(sys.argv)
    window = MainWindow(DEX_CONFIGS)
    window.show()

    bot_workers = []
    for dex_conf in DEX_CONFIGS:
        bw = TradingBotWorker(dex_conf["name"], dex_conf["endpoint"], dex_conf["market_address"], dex_conf["private_key"])
        bw.data_signal.connect(window.update_data)
        bw.log_signal.connect(window.append_log)
        bw.chart_signal.connect(window.update_chart)
        bot_workers.append(bw)

    def stop_action():
        for bw in bot_workers:
            bw.stop()
        window.stop_button.setDisabled(True)
        for dex_conf in DEX_CONFIGS:
            window.append_log("[INFO] Stop requested.", dex_conf["name"])
        logger.info("Stop requested by user.")

    window.stop_button.clicked.connect(stop_action)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    def run_loop():
        loop.run_until_complete(run_bots(app, window, bot_workers))

    thread = threading.Thread(target=run_loop, daemon=True)
    thread.start()

    def on_close():
        for bw in bot_workers:
            bw.stop()
        for dex_conf in DEX_CONFIGS:
            window.append_log("[INFO] Closing application...", dex_conf["name"])
        logger.info("Closing application.")
        loop.call_soon_threadsafe(loop.stop)
        thread.join()

    app.aboutToQuit.connect(on_close)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
