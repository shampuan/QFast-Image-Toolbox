#!/usr/bin/env python3
import sys
import os
from PIL import Image
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QMessageBox, QFrame, 
                             QSlider, QCheckBox)
from PyQt5.QtGui import QPixmap, QColor, QPalette, QImage, QCursor, QIcon
from PyQt5.QtCore import Qt

# Debian/Pardus grafik uyumluluğu
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class ColorTransparencyTool(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setAcceptDrops(True)
        self.input_path = None
        self.current_pil_img = None
        self.history = [] 

    def initUI(self):
        # Pencere Başlığı Güncellendi
        self.setWindowTitle('QFast Background Remover')
        self.setFixedSize(850, 520)
        
        # İkon Ayarı (icons/backgroundremover.png)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "icons", "remover.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.apply_dark_theme()

        main_layout = QHBoxLayout(self)

        # --- Left Section: Preview ---
        left_frame = QFrame()
        left_frame.setFrameShape(QFrame.StyledPanel)
        left_layout = QVBoxLayout(left_frame)

        self.label_image = QLabel("Drag & Drop Image Here\nClick any color to remove instantly")
        self.label_image.setAlignment(Qt.AlignCenter)
        self.label_image.setStyleSheet("border: 2px dashed #555; background: #222; color: #888;")
        self.label_image.setMinimumSize(500, 450)
        
        self.label_image.setCursor(QCursor(Qt.CrossCursor))
        self.label_image.mousePressEvent = self.get_pixel_and_process
        left_layout.addWidget(self.label_image)

        # --- Right Section: Controls ---
        right_frame = QFrame()
        right_frame.setFrameShape(QFrame.StyledPanel)
        right_frame.setFixedWidth(280)
        right_layout = QVBoxLayout(right_frame)

        right_layout.addWidget(QLabel("Selected Color:"))
        self.color_preview = QLabel()
        self.color_preview.setFixedHeight(40)
        self.color_preview.setStyleSheet("border: 1px solid #666; background: transparent;")
        right_layout.addWidget(self.color_preview)

        right_layout.addSpacing(15)
        
        right_layout.addWidget(QLabel("Tolerance (0 - 100):"))
        self.slider_tolerance = QSlider(Qt.Horizontal)
        self.slider_tolerance.setRange(0, 100)
        self.slider_tolerance.setValue(10)
        self.slider_tolerance.valueChanged.connect(lambda v: self.label_tolerance_val.setText(f"Value: {v}"))
        right_layout.addWidget(self.slider_tolerance)
        
        self.label_tolerance_val = QLabel("Value: 10")
        self.label_tolerance_val.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.label_tolerance_val)

        right_layout.addSpacing(10)
        self.check_exif = QCheckBox("Keep EXIF data")
        self.check_exif.setChecked(True)
        right_layout.addWidget(self.check_exif)

        right_layout.addStretch()

        self.btn_undo = QPushButton("Undo (Ctrl+Z)")
        self.btn_undo.setEnabled(False)
        self.btn_undo.clicked.connect(self.undo_step)
        right_layout.addWidget(self.btn_undo)

        self.btn_save = QPushButton("Appy and Save")
        self.btn_save.setFixedHeight(45)
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_image)
        right_layout.addWidget(self.btn_save)

        main_layout.addWidget(left_frame)
        main_layout.addWidget(right_frame)

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(40, 40, 40))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.Button, QColor(60, 60, 60))
        palette.setColor(QPalette.ButtonText, Qt.white)
        self.setPalette(palette)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Z and event.modifiers() & Qt.ControlModifier:
            if self.btn_undo.isEnabled():
                self.undo_step()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files: self.load_image(files[0])

    def load_image(self, path):
        self.input_path = path
        self.current_pil_img = Image.open(path).convert("RGBA")
        self.history = [] 
        self.btn_undo.setEnabled(False)
        self.btn_save.setEnabled(False)
        self.update_preview()

    def update_preview(self):
        if self.current_pil_img:
            data = self.current_pil_img.tobytes("raw", "RGBA")
            qimage = QImage(data, self.current_pil_img.size[0], self.current_pil_img.size[1], QImage.Format_RGBA8888)
            pix = QPixmap.fromImage(qimage)
            self.label_image.setPixmap(pix.scaled(self.label_image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.label_image.setText("")

    def get_pixel_and_process(self, event):
        if not self.current_pil_img: return
        pixmap = self.label_image.pixmap()
        if not pixmap: return

        lb_w, lb_h = self.label_image.width(), self.label_image.height()
        px_w, px_h = pixmap.width(), pixmap.height()
        
        offset_x = (lb_w - px_w) / 2
        offset_y = (lb_h - px_h) / 2
        rel_x = event.pos().x() - offset_x
        rel_y = event.pos().y() - offset_y

        if 0 <= rel_x < px_w and 0 <= rel_y < px_h:
            img_x = int(rel_x * (self.current_pil_img.size[0] / px_w))
            img_y = int(rel_y * (self.current_pil_img.size[1] / px_h))
            
            pixel_data = self.current_pil_img.getpixel((img_x, img_y))
            
            if len(pixel_data) == 4 and pixel_data[3] == 0:
                return

            selected_rgb = pixel_data[:3]
            self.color_preview.setStyleSheet(f"background-color: rgb{selected_rgb}; border: 1px solid white;")
            self.apply_transparency(*selected_rgb)

    def apply_transparency(self, r_sel, g_sel, b_sel):
        self.history.append(self.current_pil_img.copy())
        self.btn_undo.setEnabled(True)

        img = self.current_pil_img.copy()
        data = img.getdata()
        tolerance = self.slider_tolerance.value()
        
        new_data = []
        for item in data:
            if item[3] > 0 and (abs(item[0] - r_sel) <= tolerance and 
                                abs(item[1] - g_sel) <= tolerance and 
                                abs(item[2] - b_sel) <= tolerance):
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)

        img.putdata(new_data)
        self.current_pil_img = img
        self.update_preview()
        self.btn_save.setEnabled(True)

    def undo_step(self):
        if self.history:
            self.current_pil_img = self.history.pop()
            self.update_preview()
            if not self.history:
                self.btn_undo.setEnabled(False)
                self.btn_save.setEnabled(False)

    def save_image(self):
        if not self.current_pil_img or not self.input_path: return
        
        dir_name = os.path.dirname(self.input_path)
        base_name = os.path.splitext(os.path.basename(self.input_path))[0]
        
        counter = 1
        final_path = os.path.join(dir_name, f"{base_name}_removed{counter}.png")
        while os.path.exists(final_path):
            counter += 1
            final_path = os.path.join(dir_name, f"{base_name}_removed{counter}.png")

        try:
            save_args = {"format": "PNG"}
            if self.check_exif.isChecked():
                with Image.open(self.input_path) as original:
                    exif_data = original.info.get("exif")
                    if exif_data:
                        save_args["exif"] = exif_data

            self.current_pil_img.save(final_path, **save_args)
            QMessageBox.information(self, "Saved", f"File saved to original folder:\n{os.path.basename(final_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Save failed: {str(e)}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ColorTransparencyTool()
    window.show()
    sys.exit(app.exec_())
