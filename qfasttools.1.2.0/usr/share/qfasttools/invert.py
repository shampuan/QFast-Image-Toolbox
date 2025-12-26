#!/usr/bin/env python3
import sys
import os
import io
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QMessageBox, QGroupBox, 
                             QFrame, QCheckBox)
from PyQt5.QtGui import QPixmap, QImage, QCursor, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt
from PIL import Image, ImageOps

# Debian/Pardus grafik uyumluluğu
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class QFastInverter(QWidget):
    def __init__(self, target_files=None):
        super().__init__()
        self.selected_files = target_files if target_files else []
        self.original_full = None
        self.proxy_image = None
        self.display_image = None
        
        self.apply_dark_theme() # q.py stili koyu tema
        self.initUI()
        
        if self.selected_files:
            self.load_image(self.selected_files[0])

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(40, 40, 40))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Button, QColor(55, 55, 55))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.Text, Qt.white)
        self.setPalette(palette)

    def initUI(self):
        self.setWindowTitle('QFast Color Inverter')
        self.setFixedWidth(550)
        
        # İkon Ataması: icons/invert.png
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'icons', 'invert.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        main_layout = QVBoxLayout(self)

        # ÜST: Sürükle-Bırak Alanı (resize.py stilinde)
        self.drop_label = QLabel('\n\nDrag-Drop Image Here for Invert\n\n')
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setMinimumHeight(280)
        self.drop_label.setStyleSheet("""
            border: 2px dashed #555555; border-radius: 10px;
            color: #aaaaaa; font-weight: bold; background-color: #2a2a2a;
        """)
        self.setAcceptDrops(True)
        main_layout.addWidget(self.drop_label)

        # ORTA: Seçenekler
        options_group = QGroupBox("Processing Options")
        opt_lay = QVBoxLayout()
        
        self.cb_keep_exif = QCheckBox("Keep Metadata (EXIF)")
        self.cb_keep_exif.setChecked(True)
        self.cb_keep_exif.setStyleSheet("font-weight: bold; color: #aaaaaa;")
        opt_lay.addWidget(self.cb_keep_exif)
        
        options_group.setLayout(opt_lay)
        main_layout.addWidget(options_group)

        # ALT: İşlem Butonu (resize.py stilinde)
        self.btn_do_it = QPushButton("INVERT AND SAVE")
        self.btn_do_it.setFixedHeight(50)
        self.btn_do_it.setStyleSheet("""
            QPushButton { background-color: #1a639b; color: white; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:disabled { background-color: #444; color: #888; }
        """)
        self.btn_do_it.setEnabled(False)
        self.btn_do_it.clicked.connect(self.process_final_render)
        main_layout.addWidget(self.btn_do_it)

    def load_image(self, path):
        try:
            self.image_path = path
            self.original_full = Image.open(path)
            
            # Önizleme için proxy (Hız için lightcontrast.py mantığı)
            w, h = self.original_full.size
            self.proxy_image = self.original_full.resize((w//4, h//4), Image.LANCZOS)
            
            # Önizlemede negatifini göster
            self.display_image = ImageOps.invert(self.proxy_image.convert('RGB'))
            self.update_display()
            
            self.btn_do_it.setEnabled(True)
            self.drop_label.setStyleSheet("border: 2px solid #27ae60; background-color: #1e2a1e;")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Load failed: {e}")

    def update_display(self):
        if self.display_image:
            byte_array = io.BytesIO()
            self.display_image.save(byte_array, format='PNG')
            qimage = QImage.fromData(byte_array.getvalue())
            pixmap = QPixmap.fromImage(qimage)
            
            scaled = pixmap.scaled(self.drop_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.drop_label.setPixmap(scaled)

    def process_final_render(self):
        if not self.original_full: return
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            # Gerçek render (arabını üretme)
            work_img = ImageOps.invert(self.original_full.convert('RGB'))
            output_path = self.get_unique_path()
            
            save_params = {}
            if self.cb_keep_exif.isChecked():
                exif = self.original_full.info.get('exif')
                if exif: save_params['exif'] = exif

            work_img.save(output_path, quality=95, **save_params)
            QMessageBox.information(self, "Success", f"Inverted image saved:\n{os.path.basename(output_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Render failed: {e}")
        finally:
            QApplication.restoreOverrideCursor()

    def get_unique_path(self):
        directory = os.path.dirname(self.image_path)
        name_part, ext = os.path.splitext(os.path.basename(self.image_path))
        if "_inverted" in name_part: name_part = name_part.split("_inverted")[0]
        
        counter = 1
        while True:
            new_filename = f"{name_part}_inverted{counter:02d}{ext if ext else '.jpg'}"
            full_path = os.path.join(directory, new_filename)
            if not os.path.exists(full_path): return full_path
            counter += 1

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.selected_files = files
            self.load_image(files[0])

    def resizeEvent(self, event):
        if self.display_image: self.update_display()
        super().resizeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ex = QFastInverter()
    ex.show()
    sys.exit(app.exec_())