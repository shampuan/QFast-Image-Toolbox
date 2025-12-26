#!/usr/bin/env python3
import sys
import os
import io
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QMessageBox, QSlider, 
                             QGroupBox, QFrame, QCheckBox, QScrollArea)
from PyQt5.QtGui import QPixmap, QImage, QCursor, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt, QTimer
from PIL import Image, ImageEnhance, ImageOps, ImageFilter, ImageDraw
import sip

# Debian/Pardus grafik uyumluluğu
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class QFastImageAdjust(QWidget):
    def __init__(self, target_file=None):
        super().__init__()
        self.image_path = target_file
        self.original_full = None
        self.proxy_image = None
        self.display_image = None
        
        # Debouncing timer for fluid UI
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.process_preview)
        
        self.apply_dark_theme()
        self.initUI()
        
        # Correct path for icons folder relative to the script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "icons", "adjust.png")
        
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        if self.image_path:
            self.load_image(self.image_path)

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(40, 40, 40))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(55, 55, 55))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        self.setPalette(palette)
        if QApplication.instance():
            QApplication.instance().setPalette(palette)

    def initUI(self):
        self.setWindowTitle('QFast Image Adjust')
        self.setMinimumSize(1100, 850)
        
        main_layout = QHBoxLayout(self)

        # LEFT: Preview Area
        self.img_display = QLabel("DRAG & DROP IMAGE TO START")
        self.img_display.setAlignment(Qt.AlignCenter)
        self.img_display.setFrameShape(QFrame.StyledPanel)
        self.img_display.setStyleSheet("border: 2px dashed #666; background-color: #222; color: #aaa;")
        self.setAcceptDrops(True)
        main_layout.addWidget(self.img_display, stretch=4)

        # RIGHT: Control Panel (Scrollable)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(320)
        scroll_content = QWidget()
        side_panel = QVBoxLayout(scroll_content)

        # 1. Light and Contrast
        group_lc = QGroupBox("Light and Contrast")
        lay_lc = QVBoxLayout()
        self.sld_bright = self.add_control(lay_lc, "Brightness", 10, 300, 100)
        self.sld_contrast = self.add_control(lay_lc, "Contrast", 10, 300, 100)
        group_lc.setLayout(lay_lc)
        side_panel.addWidget(group_lc)

        # 2. Color Saturation
        group_sat = QGroupBox("Color Saturation")
        lay_sat = QVBoxLayout()
        self.sld_sat = self.add_control(lay_sat, "Saturation Factor", 0, 30, 10)
        group_sat.setLayout(lay_sat)
        side_panel.addWidget(group_sat)

        # 3. Hue Shift
        group_hue = QGroupBox("Hue Shift")
        lay_hue = QVBoxLayout()
        self.sld_hue = self.add_control(lay_hue, "Color Shift", 0, 255, 0)
        group_hue.setLayout(lay_hue)
        side_panel.addWidget(group_hue)

        # 4. Blur and Sharpen
        group_bs = QGroupBox("Blur and Sharpen")
        lay_bs = QVBoxLayout()
        self.sld_blur = self.add_control(lay_bs, "Fine Blur Radius", 0, 100, 0) 
        self.sld_sharp = self.add_control(lay_bs, "Sharpen Factor", 10, 50, 10)
        group_bs.setLayout(lay_bs)
        side_panel.addWidget(group_bs)

        # 5. Vintage and Vignette
        group_vv = QGroupBox("Vintage and Vignette")
        lay_vv = QVBoxLayout()
        self.sld_sepia = self.add_control(lay_vv, "Sepia Tone", 0, 100, 0)
        self.sld_vig = self.add_control(lay_vv, "Vignette Shadow", 0, 100, 0)
        group_vv.setLayout(lay_vv)
        side_panel.addWidget(group_vv)

        # Final Actions
        side_panel.addStretch()
        
        self.btn_reset = QPushButton("RESET ALL SETTINGS")
        self.btn_reset.clicked.connect(self.reset_settings)
        side_panel.addWidget(self.btn_reset)

        self.cb_keep_exif = QCheckBox("Keep Metadata EXIF")
        self.cb_keep_exif.setChecked(True)
        side_panel.addWidget(self.cb_keep_exif)

        self.btn_save = QPushButton("SAVE FINAL IMAGE")
        self.btn_save.setFixedHeight(60)
        self.btn_save.setEnabled(False)
        self.btn_save.setStyleSheet("background-color: #2a82da; font-weight: bold;")
        self.btn_save.clicked.connect(self.process_final_render)
        side_panel.addWidget(self.btn_save)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll, stretch=1)

    def add_control(self, layout, label_text, min_v, max_v, def_v):
        layout.addWidget(QLabel(label_text))
        sld = QSlider(Qt.Horizontal)
        sld.setRange(min_v, max_v)
        sld.setValue(def_v)
        sld.setEnabled(False)
        sld.valueChanged.connect(self.request_preview)
        layout.addWidget(sld)
        return sld

    def reset_settings(self):
        self.sld_bright.setValue(100)
        self.sld_contrast.setValue(100)
        self.sld_sat.setValue(10)
        self.sld_hue.setValue(0)
        self.sld_blur.setValue(0)
        self.sld_sharp.setValue(10)
        self.sld_sepia.setValue(0)
        self.sld_vig.setValue(0)
        self.request_preview()

    def load_image(self, path):
        try:
            self.image_path = path
            self.original_full = Image.open(path)
            w, h = self.original_full.size
            self.proxy_image = self.original_full.resize((w//4, h//4), Image.LANCZOS)
            
            for s in [self.sld_bright, self.sld_contrast, self.sld_sat, self.sld_hue, 
                      self.sld_blur, self.sld_sharp, self.sld_sepia, self.sld_vig]:
                s.setEnabled(True)
            self.btn_save.setEnabled(True)
            self.request_preview()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Load failed: {e}")

    def apply_pipeline(self, img):
        working = img.copy()
        
        if self.sld_hue.value() > 0:
            hsv = working.convert('HSV')
            h, s, v = hsv.split()
            h = h.point(lambda p: (p + self.sld_hue.value()) % 256)
            working = Image.merge('HSV', (h, s, v)).convert('RGB')

        working = ImageEnhance.Brightness(working).enhance(self.sld_bright.value() / 100.0)
        working = ImageEnhance.Contrast(working).enhance(self.sld_contrast.value() / 100.0)
        working = ImageEnhance.Color(working).enhance(self.sld_sat.value() / 10.0)

        blur_val = self.sld_blur.value() / 20.0 
        if blur_val > 0:
            working = working.filter(ImageFilter.GaussianBlur(blur_val))
        working = ImageEnhance.Sharpness(working).enhance(self.sld_sharp.value() / 10.0)

        if self.sld_sepia.value() > 0:
            bw_sepia = ImageOps.grayscale(working)
            sepia_img = ImageOps.colorize(bw_sepia, "#301e01", "#fbefdb")
            working = Image.blend(working, sepia_img, self.sld_sepia.value() / 100.0)

        if self.sld_vig.value() > 0:
            w, h = working.size
            mask = Image.new('L', (w, h), 0)
            draw = ImageDraw.Draw(mask)
            coverage = 1.3 - (self.sld_vig.value() / 100.0)
            left, top = (w * (1 - coverage)) / 2, (h * (1 - coverage)) / 2
            draw.ellipse([left, top, w - left, h - top], fill=255)
            mask = mask.filter(ImageFilter.GaussianBlur(radius=int(min(w, h) * 0.45)))
            working = Image.composite(working, Image.new('RGB', (w, h), (0, 0, 0)), mask)

        return working

    def request_preview(self):
        self.preview_timer.start(50)

    def process_preview(self):
        if not self.proxy_image: return
        self.display_image = self.apply_pipeline(self.proxy_image)
        self.update_display()

    def update_display(self):
        if self.display_image:
            byte_array = io.BytesIO()
            self.display_image.save(byte_array, format='PNG')
            qimage = QImage.fromData(byte_array.getvalue())
            pixmap = QPixmap.fromImage(qimage)
            scaled = pixmap.scaled(self.img_display.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.img_display.setPixmap(scaled)

    def process_final_render(self):
        if not self.original_full: return
        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            work_img = self.apply_pipeline(self.original_full)
            output_path = self.get_unique_path()
            
            save_params = {'quality': 95}
            if self.cb_keep_exif.isChecked():
                exif = self.original_full.info.get('exif')
                if exif: save_params['exif'] = exif

            if output_path.lower().endswith(('.jpg', '.jpeg')):
                if work_img.mode != "RGB": 
                    work_img = work_img.convert("RGB")
            
            work_img.save(output_path, **save_params)
            QMessageBox.information(self, "Success", f"Final image saved:\n{os.path.basename(output_path)}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Render failed: {e}")
        finally:
            QApplication.restoreOverrideCursor()

    def get_unique_path(self):
        directory = os.path.dirname(self.image_path)
        name_part, ext = os.path.splitext(os.path.basename(self.image_path))
        if "_adjust" in name_part: 
            name_part = name_part.split("_adjust")[0]
        
        counter = 1
        while True:
            new_filename = f"{name_part}_adjust{counter:02d}{ext}"
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
        if self.display_image: self.update_display()
        super().resizeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ex = QFastImageAdjust()
    ex.show()
    sys.exit(app.exec_())
