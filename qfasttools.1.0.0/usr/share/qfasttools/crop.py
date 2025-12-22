#!/usr/bin/env python3
import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QMessageBox, QRubberBand, QCheckBox)
from PyQt5.QtGui import QPixmap, QIcon, QPalette, QColor
from PyQt5.QtCore import Qt, QRect, QPoint, QSize
from PIL import Image

# Debian/Pardus grafik uyumluluğu
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class QFastCropper(QWidget):
    def __init__(self, target_file=None):
        super().__init__()
        self.image_path = target_file
        self.origin = QPoint()
        self.rubberBand = None
        self.pixmap = None
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
        palette.setColor(QPalette.Highlight, QColor(100, 100, 100)) # Seçim alanı rengi
        QApplication.setPalette(palette)

    def initUI(self):
        self.setWindowTitle('QFast Image Cropper')
        
        # Dinamik ikon yolu (icons/crop.png)
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'icons', 'crop.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.setMinimumSize(800, 600)
        
        # Ana Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(15, 15, 15, 15)
        
        # Resim Alanı (QLabel)
        self.img_label = QLabel("Drag & Drop an image here to start cropping")
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setMouseTracking(True)
        self.img_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #aaaaaa; 
                border-radius: 10px; 
                color: #aaaaaa; 
                background-color: #353535;
                font-weight: bold;
                font-size: 11pt;
            }
        """)
        self.setAcceptDrops(True)
        self.layout.addWidget(self.img_label)

        # Alt Panel (Kontroller ve Butonlar)
        controls_layout = QHBoxLayout()
        
        # Metaveri kutucuğu (resize.py'den eklendi)
        self.cb_keep_exif = QCheckBox("Keep Metadata (EXIF)")
        self.cb_keep_exif.setChecked(True)
        self.cb_keep_exif.setStyleSheet("font-weight: bold; color: #aaaaaa;")
        
        self.btn_crop = QPushButton("Do it! (Crop & Save)")
        self.btn_crop.setFixedHeight(45)
        self.btn_crop.setFixedWidth(180)
        self.btn_crop.setEnabled(False)
        self.btn_crop.setStyleSheet("""
            QPushButton { 
                background-color: #454545; 
                color: white; 
                font-weight: bold; 
                border-radius: 5px; 
            }
            QPushButton:hover { background-color: #555555; }
            QPushButton:disabled { background-color: #333333; color: #777777; }
        """)
        self.btn_crop.clicked.connect(self.save_cropped_image)
        
        controls_layout.addWidget(self.cb_keep_exif)
        controls_layout.addStretch()
        controls_layout.addWidget(self.btn_crop)
        
        self.layout.addLayout(controls_layout)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.load_image(files[0])

    def load_image(self, path):
        try:
            self.image_path = path
            self.pixmap = QPixmap(path)
            if self.pixmap.isNull():
                raise Exception("Could not load image.")
            self.update_image_display()
            self.btn_crop.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Load failed: {e}")

    def update_image_display(self):
        if self.pixmap:
            scaled_pixmap = self.pixmap.scaled(self.img_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_label.setPixmap(scaled_pixmap)
            self.img_label.setStyleSheet("border: 1px solid #555; background-color: #1e1e1e; border-radius: 5px;")

    def resizeEvent(self, event):
        if self.pixmap:
            self.update_image_display()
        super().resizeEvent(event)

    def mousePressEvent(self, event):
        if self.img_label.pixmap():
            label_rect = self.img_label.geometry()
            if label_rect.contains(event.pos()):
                self.origin = event.pos()
                if not self.rubberBand:
                    self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
                self.rubberBand.setGeometry(QRect(self.origin, QSize()))
                self.rubberBand.show()

    def mouseMoveEvent(self, event):
        if self.rubberBand:
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())

    def get_unique_path(self):
        directory = os.path.dirname(self.image_path)
        base_name, ext = os.path.splitext(os.path.basename(self.image_path))
        if "_cropped" in base_name:
            base_name = base_name.split("_cropped")[0]
        counter = 1
        while True:
            new_name = f"{base_name}_cropped{counter:02d}{ext}"
            full_path = os.path.join(directory, new_name)
            if not os.path.exists(full_path):
                return full_path
            counter += 1

    def save_cropped_image(self):
        if not self.rubberBand or self.rubberBand.geometry().isEmpty():
            QMessageBox.warning(self, "Warning", "Please select an area first!")
            return

        try:
            selection_rect = self.rubberBand.geometry()
            displayed_pixmap = self.img_label.pixmap()
            
            dw = displayed_pixmap.width()
            dh = displayed_pixmap.height()
            offset_x = (self.img_label.width() - dw) / 2 + self.img_label.x()
            offset_y = (self.img_label.height() - dh) / 2 + self.img_label.y()

            orig_img = Image.open(self.image_path)
            orig_w, orig_h = orig_img.size
            
            # EXIF verisini al (resize.py mantığı)
            exif_data = orig_img.info.get('exif') if self.cb_keep_exif.isChecked() else None
            
            scale_factor = orig_w / dw
            
            left = (selection_rect.left() - offset_x) * scale_factor
            top = (selection_rect.top() - offset_y) * scale_factor
            right = (selection_rect.right() - offset_x) * scale_factor
            bottom = (selection_rect.bottom() - offset_y) * scale_factor

            cropped_img = orig_img.crop((left, top, right, bottom))
            output_path = self.get_unique_path()
            
            # Kaydetme sırasında EXIF ekle
            if exif_data:
                cropped_img.save(output_path, quality=95, exif=exif_data)
            else:
                cropped_img.save(output_path, quality=95)
            
            QMessageBox.information(self, "Success", f"Saved: {os.path.basename(output_path)}")
            self.rubberBand.hide()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Crop failed: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ex = QFastCropper()
    ex.show()
    sys.exit(app.exec_())
