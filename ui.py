# ui.py
# GUI con PyQt5: un tab per ogni DEX.

import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QPushButton, 
                             QTextEdit, QHBoxLayout, QTabWidget)
from PyQt5.QtCore import pyqtSlot
import matplotlib
matplotlib.use('Agg')
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

class DexTab(QWidget):
    def __init__(self, dex_name):
        super().__init__()
        self.dex_name = dex_name
        
        layout = QVBoxLayout()
        
        self.info_label = QLabel(f"{dex_name} Running...")
        layout.addWidget(self.info_label)
        
        self.price_label = QLabel("Mid Price: N/A")
        self.spread_label = QLabel("Spread: N/A")
        self.pred_label = QLabel("Prediction: N/A")
        
        info_layout = QHBoxLayout()
        info_layout.addWidget(self.price_label)
        info_layout.addWidget(self.spread_label)
        info_layout.addWidget(self.pred_label)
        
        layout.addLayout(info_layout)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
        
        self.fig = Figure(figsize=(5,3), dpi=100)
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Mid Price Over Time")
        self.ax.set_xlabel("Time (ticks)")
        self.ax.set_ylabel("Mid Price")
        self.price_data = []
        self.line, = self.ax.plot([], [])
        layout.addWidget(self.canvas)

        self.setLayout(layout)
    
    def update_data(self, data_dict):
        mid_price = data_dict.get("mid_price", None)
        spread = data_dict.get("spread", None)
        pred = data_dict.get("pred", None)
        
        if mid_price is not None:
            self.price_label.setText(f"Mid Price: {mid_price:.4f}")
        if spread is not None:
            self.spread_label.setText(f"Spread: {spread:.4f}")
        if pred is not None:
            self.pred_label.setText(f"Prediction: {pred:.4f}")
        else:
            self.pred_label.setText("Prediction: N/A")
    
    def append_log(self, text):
        self.log_area.append(text)
    
    def update_chart(self, price):
        self.price_data.append(price)
        self.line.set_xdata(np.arange(len(self.price_data)))
        self.line.set_ydata(self.price_data)
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

class MainWindow(QWidget):
    def __init__(self, dex_configs):
        super().__init__()
        
        self.setWindowTitle("Solana DEX Sniper Bot - Multi DEX")
        self.resize(1000, 800)
        
        layout = QVBoxLayout()
        
        self.tabs = QTabWidget()
        self.dex_tabs = {}
        
        for dex_conf in dex_configs:
            dex_name = dex_conf["name"]
            tab = DexTab(dex_name)
            self.dex_tabs[dex_name] = tab
            self.tabs.addTab(tab, dex_name)
        
        layout.addWidget(self.tabs)
        
        self.stop_button = QPushButton("Stop All Bots")
        layout.addWidget(self.stop_button)

        self.setLayout(layout)
    
    @pyqtSlot(dict, str)
    def update_data(self, data_dict, dex_name):
        self.dex_tabs[dex_name].update_data(data_dict)
    
    @pyqtSlot(str, str)
    def append_log(self, text, dex_name):
        self.dex_tabs[dex_name].append_log(text)
    
    @pyqtSlot(float, str)
    def update_chart(self, price, dex_name):
        self.dex_tabs[dex_name].update_chart(price)
