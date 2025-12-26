#!/usr/bin/env python3
import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QGridLayout, 
                             QFrame, QToolTip)
from PyQt5.QtGui import QColor, QCursor, QPalette, QBrush, QPixmap, QPainter, QIcon
from PyQt5.QtCore import Qt, pyqtSignal, QPoint

# Debian/Pardus grafik uyumluluğu
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class ColorBox(QFrame):
    """Small boxes showing color history"""
    clicked = pyqtSignal(QColor)

    def __init__(self, color=QColor("#333333")):
        super().__init__()
        self.setFixedSize(30, 30)
        self.setFrameShape(QFrame.StyledPanel)
        self.setColor(color)

    def setColor(self, color):
        self.color = color
        self.setStyleSheet(f"background-color: {color.name()}; border: 1px solid #555; border-radius: 3px;")

    def mousePressEvent(self, event):
        self.clicked.emit(self.color)

class PickerOverlay(QWidget):
    """Transparent overlay for screen color picking"""
    color_selected = pyqtSignal(QColor)

    def __init__(self, screenshot):
        super().__init__()
        self.screenshot = screenshot
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setCursor(Qt.CrossCursor)
        self.showFullScreen()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.drawPixmap(0, 0, self.screenshot)

    def mousePressEvent(self, event):
        x = event.globalPos().x()
        y = event.globalPos().y()
        pixel_color = QColor(self.screenshot.toImage().pixel(x, y))
        self.color_selected.emit(pixel_color)
        self.close()

class ColorPickerTool(QWidget):
    def __init__(self):
        super().__init__()
        self.history_boxes = []
        self.initUI()

    def initUI(self):
        self.setWindowTitle('QFast Color Picker')
        self.setFixedSize(350, 420)
        
        # 1- İkon ayarı (icons/colorpicker.png)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "icons", "colorpicker.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.apply_dark_theme()

        layout = QVBoxLayout()

        # --- MAIN PREVIEW ---
        self.preview_box = QFrame()
        self.preview_box.setMinimumHeight(100)
        self.preview_box.setStyleSheet("background-color: #333; border-radius: 10px; border: 2px solid #555;")
        layout.addWidget(self.preview_box)

        # --- COLOR CODES ---
        codes_layout = QGridLayout()

        # 2 & 3 - Beyaz yazı rengi ve İngilizce etiketler
        label_style = "color: white;"
        
        lbl_hex = QLabel("HTML (HEX):")
        lbl_hex.setStyleSheet(label_style)
        codes_layout.addWidget(lbl_hex, 0, 0)
        
        self.edit_hex = QLineEdit("#333333")
        self.edit_hex.setReadOnly(True)
        self.edit_hex.setStyleSheet("color: white; background-color: #444; border: 1px solid #555;")
        self.btn_copy_hex = QPushButton("Copy")
        self.btn_copy_hex.clicked.connect(lambda: self.copy_to_clipboard(self.edit_hex.text()))
        codes_layout.addWidget(self.edit_hex, 0, 1)
        codes_layout.addWidget(self.btn_copy_hex, 0, 2)

        lbl_rgb = QLabel("RGB:")
        lbl_rgb.setStyleSheet(label_style)
        codes_layout.addWidget(lbl_rgb, 1, 0)
        
        self.edit_rgb = QLineEdit("rgb(51, 51, 51)")
        self.edit_rgb.setReadOnly(True)
        self.edit_rgb.setStyleSheet("color: white; background-color: #444; border: 1px solid #555;")
        self.btn_copy_rgb = QPushButton("Copy")
        self.btn_copy_rgb.clicked.connect(lambda: self.copy_to_clipboard(self.edit_rgb.text()))
        codes_layout.addWidget(self.edit_rgb, 1, 1)
        codes_layout.addWidget(self.btn_copy_rgb, 1, 2)

        layout.addLayout(codes_layout)

        # --- PICK COLOR BUTTON ---
        self.btn_pick = QPushButton("PICK COLOR")
        self.btn_pick.setMinimumHeight(50)
        self.btn_pick.clicked.connect(self.start_picking)
        layout.addWidget(self.btn_pick)

        # --- COLOR HISTORY ---
        lbl_history = QLabel("Color History:")
        lbl_history.setStyleSheet(label_style)
        layout.addWidget(lbl_history)
        
        history_layout = QGridLayout()
        for i in range(24):
            box = ColorBox()
            box.clicked.connect(self.update_from_history)
            history_layout.addWidget(box, i // 8, i % 8)
            self.history_boxes.append(box)
        
        layout.addLayout(history_layout)
        self.setLayout(layout)

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(45, 45, 45))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(35, 35, 35))
        palette.setColor(QPalette.Button, QColor(60, 60, 60))
        palette.setColor(QPalette.ButtonText, Qt.white)
        self.setPalette(palette)

    def copy_to_clipboard(self, text):
        QApplication.clipboard().setText(text)
        QToolTip.showText(QCursor.pos(), "Copied!", self)

    def update_from_history(self, color):
        self.set_color(color, add_to_history=False)

    def set_color(self, color, add_to_history=True):
        hex_code = color.name().upper()
        rgb_code = f"rgb({color.red()}, {color.green()}, {color.blue()})"
        self.edit_hex.setText(hex_code)
        self.edit_rgb.setText(rgb_code)
        self.preview_box.setStyleSheet(f"background-color: {hex_code}; border-radius: 10px; border: 2px solid #555;")
        if add_to_history: self.add_to_history(color)

    def add_to_history(self, color):
        if self.history_boxes[0].color == color: return
        for i in range(len(self.history_boxes)-1, 0, -1):
            self.history_boxes[i].setColor(self.history_boxes[i-1].color)
        self.history_boxes[0].setColor(color)

    def start_picking(self):
        self.hide()
        QApplication.processEvents()
        
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        
        self.overlay = PickerOverlay(screenshot)
        self.overlay.color_selected.connect(self.handle_color_picked)
        self.overlay.show()

    def handle_color_picked(self, color):
        self.set_color(color)
        self.show()
        self.raise_()
        self.activateWindow()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ColorPickerTool()
    win.show()
    sys.exit(app.exec_())
