#!/usr/bin/env python3
import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QMessageBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QFrame)
from PyQt5.QtGui import QPixmap, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt
from PIL import Image
from PIL.ExifTags import TAGS

# Debian/Pardus grafik uyumluluğu
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class QFastExifCleaner(QWidget):
    def __init__(self, target_file=None):
        super().__init__()
        self.image_path = target_file
        self.current_exif = {}
        self.apply_dark_theme() # Koyu temayı uygula
        self.initUI()
        
        if self.image_path:
            self.load_image(self.image_path)

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(40, 40, 40))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Button, QColor(55, 55, 55))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Highlight, QColor(80, 80, 80))
        QApplication.setPalette(palette)

    def initUI(self):
        self.setWindowTitle('QFast EXIF Cleaner & Editor')
        self.setMinimumSize(800, 600)

        # --- İSTEDİĞİN İKON ATAMASI ---
        # Program nereden çalışırsa çalışsın aynı dizindeki icons klasörüne bakar
        base_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_dir, "icons", "deleteexif.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        # ------------------------------
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        # 1. Sürükle-Bırak Alanı
        self.drop_label = QLabel("Drag & Drop Image Here")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setFixedHeight(100)
        self.drop_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaaaaa; 
                border-radius: 10px; 
                color: #aaaaaa; 
                background-color: #353535;
                font-weight: bold;
                font-size: 10pt;
            }
        """)
        self.setAcceptDrops(True)
        main_layout.addWidget(self.drop_label)

        # 2. Bilgi Paneli (Tablo)
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Tag Name", "Value"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                gridline-color: #333;
                color: white;
                border: 1px solid #555;
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #454545;
                color: #aaaaaa;
                padding: 4px;
                border: 1px solid #333;
                font-weight: bold;
            }
        """)
        main_layout.addWidget(self.table)

        # 3. Butonlar
        btn_layout = QHBoxLayout()
        btn_style = """
            QPushButton { 
                background-color: #454545; 
                color: white; 
                font-weight: bold; 
                border-radius: 5px; 
                padding: 10px;
            }
            QPushButton:hover { background-color: #555555; }
            QPushButton:disabled { background-color: #333333; color: #777777; }
        """

        self.btn_clear = QPushButton("Remove All EXIF Data")
        self.btn_clear.setStyleSheet(btn_style.replace("#454545", "#5a4a4a"))
        self.btn_clear.setEnabled(False)
        self.btn_clear.clicked.connect(self.save_cleaned_image)

        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_clear)
        main_layout.addLayout(btn_layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files: self.load_image(files[0])

    def load_image(self, path):
        try:
            self.image_path = path
            self.drop_label.setText(f"File: {os.path.basename(path)}")
            self.drop_label.setStyleSheet(self.drop_label.styleSheet() + "border: 2px solid #27ae60; color: #27ae60;")
            
            img = Image.open(path)
            exif_data = img._getexif()
            
            self.table.setRowCount(0)
            if exif_data:
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(str(tag)))
                    self.table.setItem(row, 1, QTableWidgetItem(str(value)))
                self.btn_clear.setEnabled(True)
            else:
                QMessageBox.information(self, "Info", "No EXIF data found in this image.")
                self.btn_clear.setEnabled(False)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Load failed: {e}")

    def get_unique_path(self):
        directory = os.path.dirname(self.image_path)
        name_part, extension = os.path.splitext(os.path.basename(self.image_path))
        
        if "_exif_cleaned" in name_part:
            name_part = name_part.split("_exif_cleaned")[0]
        
        counter = 1
        while True:
            new_filename = f"{name_part}_exif_cleaned{counter:02d}{extension}"
            full_path = os.path.join(directory, new_filename)
            if not os.path.exists(full_path): return full_path
            counter += 1

    def save_cleaned_image(self):
        try:
            img = Image.open(self.image_path)
            
            # EXIF verisi olmadan yeni bir resim oluşturma (Meta verisiz kopyalama)
            data = list(img.getdata())
            clean_img = Image.new(img.mode, img.size)
            clean_img.putdata(data)
            
            output_path = self.get_unique_path()
            clean_img.save(output_path)
            
            QMessageBox.information(self, "Success", f"All EXIF metadata removed!\nSaved: {os.path.basename(output_path)}")
            self.image_path = output_path
            self.table.setRowCount(0)
            self.btn_clear.setEnabled(False)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save failed: {e}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ex = QFastExifCleaner()
    ex.show()
    sys.exit(app.exec_())