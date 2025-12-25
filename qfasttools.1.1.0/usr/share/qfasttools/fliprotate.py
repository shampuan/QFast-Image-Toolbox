#!/usr/bin/env python3
import sys
import os
import io
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QMessageBox, QFrame, QCheckBox)
from PyQt5.QtGui import QPixmap, QImage, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt
from PIL import Image

# Debian/Pardus grafik uyumluluğu
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class QFastFlipRotate(QWidget):
    def __init__(self, target_file=None):
        super().__init__()
        self.image_path = target_file
        self.original_image = None
        self.current_image = None
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
        QApplication.setPalette(palette)

    def initUI(self):
        self.setWindowTitle('QFast Flip & Rotate')
        
        # Dinamik ikon yolu (icons/flip-rotate.png)
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'icons', 'flip-rotate.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.setMinimumSize(850, 600)
        
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Resim Gösterici Alan
        self.img_label = QLabel("Drag & Drop an image here")
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaaaaa; 
                border-radius: 10px; 
                color: #aaaaaa; 
                background-color: #353535;
                font-weight: bold;
            }
        """)
        self.setAcceptDrops(True)
        main_layout.addWidget(self.img_label, stretch=4)

        # Kontrol Paneli
        side_panel = QVBoxLayout()
        side_panel.setSpacing(10)
        
        panel_label = QLabel("Operations")
        panel_label.setStyleSheet("color: #aaaaaa; font-weight: bold; margin-bottom: 5px;")
        side_panel.addWidget(panel_label)

        btn_style = """
            QPushButton { 
                background-color: #454545; 
                color: white; 
                font-weight: bold; 
                border-radius: 5px; 
                padding: 8px;
            }
            QPushButton:hover { background-color: #555555; }
            QPushButton:disabled { background-color: #333333; color: #777777; }
        """

        self.btn_flip_h = QPushButton(" ↔  Flip Horizontal")
        self.btn_flip_h.setStyleSheet(btn_style)
        self.btn_flip_h.clicked.connect(lambda: self.apply_transform("FLIP_LEFT_RIGHT"))
        
        self.btn_flip_v = QPushButton(" ↕  Flip Vertical")
        self.btn_flip_v.setStyleSheet(btn_style)
        self.btn_flip_v.clicked.connect(lambda: self.apply_transform("FLIP_TOP_BOTTOM"))
        
        self.btn_rotate_ccw = QPushButton(" ↺  Rotate 90° CCW")
        self.btn_rotate_ccw.setStyleSheet(btn_style)
        self.btn_rotate_ccw.clicked.connect(lambda: self.apply_transform("ROTATE_90"))

        self.btn_rotate_cw = QPushButton(" ↻  Rotate 90° CW")
        self.btn_rotate_cw.setStyleSheet(btn_style)
        self.btn_rotate_cw.clicked.connect(lambda: self.apply_transform("ROTATE_270"))

        # Metaveri kutucuğu (resize.py'den eklendi)
        self.cb_keep_exif = QCheckBox("Keep Metadata (EXIF)")
        self.cb_keep_exif.setChecked(True)
        self.cb_keep_exif.setStyleSheet("font-weight: bold; color: #aaaaaa; margin: 5px 0;")

        # Ayırıcı Çizgi
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #555;")
        
        # Kaydetme Butonu
        self.btn_do_it = QPushButton("Do it! (Save)")
        self.btn_do_it.setFixedHeight(45)
        self.btn_do_it.setEnabled(False)
        self.btn_do_it.setStyleSheet(btn_style.replace("#454545", "#4a5a6a"))
        self.btn_do_it.clicked.connect(self.save_image)

        side_panel.addWidget(self.btn_flip_h)
        side_panel.addWidget(self.btn_flip_v)
        side_panel.addWidget(self.btn_rotate_ccw)
        side_panel.addWidget(self.btn_rotate_cw)
        side_panel.addSpacing(10)
        side_panel.addWidget(self.cb_keep_exif)
        side_panel.addSpacing(5)
        side_panel.addWidget(line)
        side_panel.addSpacing(5)
        side_panel.addWidget(self.btn_do_it)
        side_panel.addStretch()

        main_layout.addLayout(side_panel, stretch=1)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files: self.load_image(files[0])

    def load_image(self, path):
        try:
            self.image_path = path
            img = Image.open(path)
            # Orijinal meta veriyi saklamak için açıyoruz
            self.original_raw = Image.open(path) 
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            self.original_image = img
            self.current_image = self.original_image.copy()
            self.update_display()
            self.btn_do_it.setEnabled(True)
            self.img_label.setStyleSheet("border: 1px solid #555; background-color: #1e1e1e; border-radius: 5px;")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load image: {e}")

    def apply_transform(self, action):
        if self.current_image:
            if action == "FLIP_LEFT_RIGHT":
                self.current_image = self.current_image.transpose(Image.FLIP_LEFT_RIGHT)
            elif action == "FLIP_TOP_BOTTOM":
                self.current_image = self.current_image.transpose(Image.FLIP_TOP_BOTTOM)
            elif action == "ROTATE_90":
                self.current_image = self.current_image.transpose(Image.ROTATE_90)
            elif action == "ROTATE_270":
                self.current_image = self.current_image.transpose(Image.ROTATE_270)
            self.update_display()

    def update_display(self):
        if self.current_image:
            try:
                byte_array = io.BytesIO()
                self.current_image.save(byte_array, format='PNG')
                qimage = QImage.fromData(byte_array.getvalue())
                pixmap = QPixmap.fromImage(qimage)
                scaled = pixmap.scaled(self.img_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.img_label.setPixmap(scaled)
            except Exception as e:
                print(f"Display Error: {e}")

    def resizeEvent(self, event):
        if self.current_image: self.update_display()
        super().resizeEvent(event)

    def get_unique_path(self):
        directory = os.path.dirname(self.image_path)
        filename = os.path.basename(self.image_path)
        name_part, extension = os.path.splitext(filename)
        
        if "_modified" in name_part:
            name_part = name_part.split("_modified")[0]
        
        counter = 1
        while True:
            new_filename = f"{name_part}_modified{counter:02d}{extension}"
            full_path = os.path.join(directory, new_filename)
            if not os.path.exists(full_path):
                return full_path
            counter += 1

    def save_image(self):
        if not self.current_image: return
        try:
            # EXIF verisini orijinal dosyadan al (resize.py mantığı)
            exif_data = self.original_raw.info.get('exif') if self.cb_keep_exif.isChecked() else None
            
            output_path = self.get_unique_path()
            save_img = self.current_image
            if output_path.lower().endswith(('.jpg', '.jpeg')):
                save_img = self.current_image.convert('RGB')
            
            # Kaydetme sırasında EXIF ekle
            if exif_data:
                save_img.save(output_path, quality=95, exif=exif_data)
            else:
                save_img.save(output_path, quality=95)
                
            QMessageBox.information(self, "Success", f"Saved: {os.path.basename(output_path)}")
            # Yeni durumu orijinal olarak set et
            self.image_path = output_path
            self.original_image = save_img.copy()
            self.original_raw = Image.open(output_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save failed: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ex = QFastFlipRotate()
    ex.show()
    sys.exit(app.exec_())
