#!/usr/bin/env python3
import sys
import os
import io
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QMessageBox, QRadioButton, 
                             QGroupBox, QFrame, QSlider, QCheckBox)
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QCursor, QPalette, QIcon
from PyQt5.QtCore import Qt, QRect, QPoint
from PIL import Image, ImageFilter, ImageDraw

# Debian/Pardus grafik uyumluluğu
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class CensorLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.is_drawing = False

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.parent.current_image:
            self.start_point = event.pos()
            self.end_point = event.pos()
            self.is_drawing = True
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.end_point = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_drawing:
            self.end_point = event.pos()
            self.is_drawing = False
            self.parent.apply_censor(self.start_point, self.end_point)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.is_drawing:
            painter = QPainter(self)
            pen = QPen(QColor(170, 170, 170), 2, Qt.DashLine)
            painter.setPen(pen)
            rect = QRect(self.start_point, self.end_point)
            if self.parent.rad_rect.isChecked():
                painter.drawRect(rect)
            else:
                painter.drawEllipse(rect)

class QFastImageCensor(QWidget):
    def __init__(self, target_file=None):
        super().__init__()
        self.image_path = target_file
        self.current_image = None
        self.history = [] 
        self.apply_dark_theme()
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
        self.setWindowTitle('QFast Image Censor')
        
        # Dinamik ikon yolu (icons/deleteexif.png)
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'icons', 'deleteexif.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.setMinimumSize(1000, 700)
        
        main_layout = QHBoxLayout(self)

        # Resim Alanı
        self.img_display = CensorLabel(self)
        self.img_display.setAlignment(Qt.AlignCenter)
        self.img_display.setFrameShape(QFrame.StyledPanel)
        self.img_display.setText("Drag & Drop an image here\nDraw to censor")
        self.img_display.setStyleSheet("""
            QLabel { 
                border: 2px dashed #aaaaaa; 
                border-radius: 10px; 
                color: #aaaaaa; 
                background-color: #353535;
                font-weight: bold;
            }
        """)
        self.setAcceptDrops(True)
        main_layout.addWidget(self.img_display, stretch=4)

        # Sağ Panel
        side_panel = QVBoxLayout()
        side_panel.setSpacing(10)
        
        group_style = "QGroupBox { color: #aaaaaa; font-weight: bold; border: 1px solid #555; margin-top: 10px; } QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 3px; }"
        btn_style = """
            QPushButton { background-color: #454545; color: white; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #555555; }
            QPushButton:disabled { background-color: #333333; color: #777777; }
        """

        # Seçim Şekli
        shape_group = QGroupBox("Selection Shape")
        shape_group.setStyleSheet(group_style)
        shape_layout = QVBoxLayout()
        self.rad_rect = QRadioButton("Rectangle")
        self.rad_circle = QRadioButton("Circle / Ellipse")
        self.rad_rect.setChecked(True)
        shape_layout.addWidget(self.rad_rect)
        shape_layout.addWidget(self.rad_circle)
        shape_group.setLayout(shape_layout)
        
        # Sansür Tipi
        type_group = QGroupBox("Censor Type")
        type_group.setStyleSheet(group_style)
        type_layout = QVBoxLayout()
        self.rad_pixel = QRadioButton("Pixelate")
        self.rad_blur = QRadioButton("Blur")
        self.rad_pixel.setChecked(True)
        type_layout.addWidget(self.rad_pixel)
        type_layout.addWidget(self.rad_blur)
        type_group.setLayout(type_layout)

        # Efekt Seviyesi (Slider)
        level_group = QGroupBox("Censor Strength")
        level_group.setStyleSheet(group_style)
        level_layout = QVBoxLayout()
        self.strength_slider = QSlider(Qt.Horizontal)
        self.strength_slider.setMinimum(5)
        self.strength_slider.setMaximum(100)
        self.strength_slider.setValue(25)
        self.strength_slider.setStyleSheet("""
            QSlider::groove:horizontal { border: 1px solid #555; height: 8px; background: #333; margin: 2px 0; border-radius: 4px; }
            QSlider::handle:horizontal { background: #aaaaaa; border: 1px solid #777; width: 18px; margin: -5px 0; border-radius: 9px; }
        """)
        level_layout.addWidget(self.strength_slider)
        level_group.setLayout(level_layout)

        # Metaveri kutucuğu (resize.py'den eklendi)
        self.cb_keep_exif = QCheckBox("Keep Metadata (EXIF)")
        self.cb_keep_exif.setChecked(True)
        self.cb_keep_exif.setStyleSheet("font-weight: bold; color: #aaaaaa; margin-top: 5px;")

        # Geri Al Butonu
        self.btn_undo = QPushButton("↺ Undo Last")
        self.btn_undo.setFixedHeight(40)
        self.btn_undo.setEnabled(False)
        self.btn_undo.setStyleSheet(btn_style)
        self.btn_undo.clicked.connect(self.undo_action)

        # Kaydet Butonu
        self.btn_do_it = QPushButton("Do it! (Save)")
        self.btn_do_it.setFixedHeight(50)
        self.btn_do_it.setEnabled(False)
        self.btn_do_it.setStyleSheet(btn_style.replace("#454545", "#4a5a6a"))
        self.btn_do_it.clicked.connect(self.save_image)

        side_panel.addWidget(shape_group)
        side_panel.addWidget(type_group)
        side_panel.addWidget(level_group)
        side_panel.addWidget(self.cb_keep_exif)
        side_panel.addSpacing(20)
        side_panel.addWidget(self.btn_undo)
        side_panel.addStretch()
        side_panel.addWidget(self.btn_do_it)
        
        main_layout.addLayout(side_panel, stretch=1)

    def load_image(self, path):
        try:
            self.image_path = path
            img = Image.open(path).convert("RGBA")
            self.current_image = img
            self.history = [img.copy()]
            self.update_display()
            self.btn_do_it.setEnabled(True)
            self.btn_undo.setEnabled(False)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Load failed: {e}")

    def update_display(self):
        if self.current_image:
            byte_array = io.BytesIO()
            self.current_image.save(byte_array, format='PNG')
            qimage = QImage.fromData(byte_array.getvalue())
            pixmap = QPixmap.fromImage(qimage)
            scaled = pixmap.scaled(self.img_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_display.setPixmap(scaled)

    def apply_censor(self, p1, p2):
        if not self.current_image or not self.img_display.pixmap(): return

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        
        try:
            self.history.append(self.current_image.copy())
            if len(self.history) > 10: self.history.pop(0) 
            self.btn_undo.setEnabled(True)

            img_w, img_h = self.current_image.size
            pixmap_w = self.img_display.pixmap().width()
            pixmap_h = self.img_display.pixmap().height()
            
            offset_x = (self.img_display.width() - pixmap_w) / 2
            offset_y = (self.img_display.height() - pixmap_h) / 2
            scale = img_w / pixmap_w
            
            x1, y1 = int((p1.x() - offset_x) * scale), int((p1.y() - offset_y) * scale)
            x2, y2 = int((p2.x() - offset_x) * scale), int((p2.y() - offset_y) * scale)

            left, right = sorted([x1, x2])
            top, bottom = sorted([y1, y2])
            left, top, right, bottom = max(0, left), max(0, top), min(img_w, right), min(img_h, bottom)

            if (right - left) < 2 or (bottom - top) < 2: 
                QApplication.restoreOverrideCursor()
                return

            region = self.current_image.crop((left, top, right, bottom))
            strength = self.strength_slider.value()

            if self.rad_pixel.isChecked():
                p_size = max(4, int(strength / 2))
                small = region.resize((max(1, region.size[0]//p_size), max(1, region.size[1]//p_size)), resample=Image.BILINEAR)
                processed = small.resize(region.size, Image.NEAREST)
            else:
                processed = region.filter(ImageFilter.GaussianBlur(radius=strength/2))

            if self.rad_circle.isChecked():
                mask = Image.new('L', region.size, 0)
                draw = ImageDraw.Draw(mask)
                draw.ellipse((0, 0, right-left, bottom-top), fill=255)
                self.current_image.paste(processed, (left, top), mask)
            else:
                self.current_image.paste(processed, (left, top))
                
            self.update_display()
        finally:
            QApplication.restoreOverrideCursor()

    def undo_action(self):
        if len(self.history) > 0:
            self.current_image = self.history.pop()
            self.update_display()
            if len(self.history) == 0:
                self.btn_undo.setEnabled(False)

    def save_image(self):
        try:
            # EXIF verisini orijinal dosyadan oku (resize.py mantığı)
            original_img = Image.open(self.image_path)
            exif_data = original_img.info.get('exif') if self.cb_keep_exif.isChecked() else None
            
            output_path = self.get_unique_path()
            save_img = self.current_image.convert('RGB') if output_path.lower().endswith(('.jpg', '.jpeg')) else self.current_image
            
            # Kaydetme sırasında EXIF ekle
            if exif_data:
                save_img.save(output_path, quality=95, exif=exif_data)
            else:
                save_img.save(output_path, quality=95)
                
            QMessageBox.information(self, "Success", f"Saved: {os.path.basename(output_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save failed: {e}")

    def get_unique_path(self):
        directory = os.path.dirname(self.image_path)
        name_part, extension = os.path.splitext(os.path.basename(self.image_path))
        if "_censored" in name_part: name_part = name_part.split("_censored")[0]
        counter = 1
        while True:
            new_filename = f"{name_part}_censored{counter:02d}{extension}"
            full_path = os.path.join(directory, new_filename)
            if not os.path.exists(full_path): return full_path
            counter += 1

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files: self.load_image(files[0])

    def resizeEvent(self, event):
        if self.current_image: self.update_display()
        super().resizeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ex = QFastImageCensor()
    ex.show()
    sys.exit(app.exec_())
