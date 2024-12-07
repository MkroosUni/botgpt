# main.py
# Punto d'ingresso. Crea i worker per ogni DEX, lancia la GUI e gestisce i thread.

import sys
import asyncio
import threading
from PyQt5.QtWidgets import QApplication
from ui import MainWindow
from bot import TradingBotWorker
from config import DEX_CONFIGS

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
        loop.call_soon_threadsafe(loop.stop)
        thread.join()

    app.aboutToQuit.connect(on_close)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
