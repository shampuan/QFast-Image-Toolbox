#!/usr/bin/env python3
import sys
import os
import io
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QMessageBox, QSlider, 
                             QGroupBox, QFrame, QCheckBox, QLineEdit, 
                             QFontComboBox, QSpinBox, QColorDialog)
from PyQt5.QtGui import QPixmap, QImage, QCursor, QPalette, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QTimer, QPoint
from PIL import Image, ImageDraw, ImageFont
import sip

# Debian/Pardus grafik uyumluluğu
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class TextLabel(QLabel):
    """Resim üzerinde tıklama konumunu yakalayan özel etiket"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.parent.proxy_image:
            # Tıklanan noktayı resim koordinatlarına çevir
            ratio_w = self.parent.proxy_image.width / self.width()
            ratio_h = self.parent.proxy_image.height / self.height()
            
            # Tıklanan yerin proxy üzerindeki koordinatı
            self.parent.text_pos = (int(event.x() * ratio_w), int(event.y() * ratio_h))
            self.parent.request_preview()

class QFastAddText(QWidget):
    def __init__(self, target_file=None):
        super().__init__()
        self.image_path = target_file
        self.original_full = None
        self.proxy_image = None
        self.display_image = None
        self.text_pos = (50, 50) # Varsayılan başlangıç
        
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.process_preview)
        
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
        self.setPalette(palette)

    def initUI(self):
        self.apply_dark_theme()
        self.setWindowTitle('QFast Add Text Tool')
        
        # Dinamik ikon yolu (icons/addtext.png)
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'icons', 'addtext.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.setMinimumSize(1200, 800)
        
        main_layout = QHBoxLayout(self)

        # SOL: Önizleme
        self.img_display = TextLabel(self)
        self.img_display.setAlignment(Qt.AlignCenter)
        self.img_display.setFrameShape(QFrame.StyledPanel)
        self.img_display.setStyleSheet("border: 2px dashed #666; background-color: #222;")
        self.setAcceptDrops(True)
        main_layout.addWidget(self.img_display, stretch=4)

        # SAĞ: Kontrol Paneli
        side_panel = QVBoxLayout()

        # Metin Girişi
        text_group = QGroupBox("Text Content")
        text_lay = QVBoxLayout()
        self.input_text = QLineEdit()
        self.input_text.setPlaceholderText("Type something...")
        self.input_text.textChanged.connect(self.request_preview)
        text_lay.addWidget(self.input_text)
        text_group.setLayout(text_lay)

        # Font Ayarları
        font_group = QGroupBox("Typography")
        font_lay = QVBoxLayout()
        
        self.combo_font = QFontComboBox()
        self.combo_font.currentFontChanged.connect(self.request_preview)
        
        self.spin_size = QSpinBox()
        self.spin_size.setRange(10, 500)
        self.spin_size.setValue(40)
        self.spin_size.valueChanged.connect(self.request_preview)
        
        style_lay = QHBoxLayout()
        self.btn_bold = QPushButton("B")
        self.btn_bold.setCheckable(True)
        self.btn_bold.setFixedWidth(40)
        self.btn_bold.clicked.connect(self.request_preview)
        
        self.btn_italic = QPushButton("I")
        self.btn_italic.setCheckable(True)
        self.btn_italic.setFixedWidth(40)
        self.btn_italic.clicked.connect(self.request_preview)
        
        self.btn_color = QPushButton("Color")
        self.selected_color = QColor(Qt.white)
        self.btn_color.clicked.connect(self.pick_color)
        
        style_lay.addWidget(self.btn_bold)
        style_lay.addWidget(self.btn_italic)
        style_lay.addWidget(self.btn_color)
        
        font_lay.addWidget(QLabel("Font Family:"))
        font_lay.addWidget(self.combo_font)
        font_lay.addWidget(QLabel("Size:"))
        font_lay.addWidget(self.spin_size)
        font_lay.addLayout(style_lay)
        font_group.setLayout(font_lay)

        # Metaveri kutucuğu
        self.cb_keep_exif = QCheckBox("Keep Metadata (EXIF)")
        self.cb_keep_exif.setChecked(True)
        self.cb_keep_exif.setStyleSheet("font-weight: bold; color: #aaaaaa; margin-top: 10px;")
        
        # Alt Bilgi ve Buton
        self.info_label = QLabel("Click on image to place text")
        self.btn_do_it = QPushButton("BURN TEXT TO IMAGE")
        self.btn_do_it.setFixedHeight(60)
        self.btn_do_it.setEnabled(False)
        self.btn_do_it.clicked.connect(self.process_final_render)

        side_panel.addWidget(text_group)
        side_panel.addWidget(font_group)
        side_panel.addWidget(self.cb_keep_exif)
        side_panel.addStretch()
        side_panel.addWidget(self.info_label)
        side_panel.addWidget(side_panel.itemAt(side_panel.count()-1).widget()) if side_panel.count() > 5 else None # Dummy check
        side_panel.addWidget(self.btn_do_it)
        
        main_layout.addLayout(side_panel, stretch=1)

    def pick_color(self):
        color = QColorDialog.getColor(self.selected_color, self, "Select Text Color")
        if color.isValid():
            self.selected_color = color
            self.request_preview()

    def load_image(self, path):
        try:
            self.image_path = path
            self.original_full = Image.open(path)
            w, h = self.original_full.size
            self.proxy_image = self.original_full.resize((w//4, h//4), Image.LANCZOS)
            if self.proxy_image.mode != "RGB": self.proxy_image = self.proxy_image.convert("RGB")
            self.btn_do_it.setEnabled(True)
            self.request_preview()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Load failed: {e}")

    def draw_text_on_image(self, image, is_proxy=True):
        txt = self.input_text.text()
        if not txt: return image
        
        working = image.copy()
        draw = ImageDraw.Draw(working)
        
        font_size = self.spin_size.value()
        if is_proxy: font_size = font_size // 4
        
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
        except:
            font = ImageFont.load_default()

        color = (self.selected_color.red(), self.selected_color.green(), self.selected_color.blue())
        pos = self.text_pos
        
        draw.text(pos, txt, fill=color, font=font)
        return working

    def request_preview(self):
        self.preview_timer.start(20)

    def process_preview(self):
        if not self.proxy_image: return
        self.display_image = self.draw_text_on_image(self.proxy_image, is_proxy=True)
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
            keep_exif = self.cb_keep_exif.isChecked()
            exif_data = self.original_full.info.get('exif') if keep_exif else None

            scale = 4
            orig_pos = (self.text_pos[0] * scale, self.text_pos[1] * scale)
            
            work_img = self.original_full.copy()
            draw = ImageDraw.Draw(work_img)
            
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", self.spin_size.value())
            except:
                font = ImageFont.load_default()
            
            color = (self.selected_color.red(), self.selected_color.green(), self.selected_color.blue())
            draw.text(orig_pos, self.input_text.text(), fill=color, font=font)

            output_path = self.get_unique_path()
            
            if exif_data:
                work_img.save(output_path, quality=95, exif=exif_data)
            else:
                work_img.save(output_path, quality=95)

            QMessageBox.information(self, "Success", f"Text added and saved:\n{os.path.basename(output_path)}")
        finally:
            QApplication.restoreOverrideCursor()

    def get_unique_path(self):
        directory = os.path.dirname(self.image_path)
        name_part, ext = os.path.splitext(os.path.basename(self.image_path))
        counter = 1
        while True:
            suffix = f"_text{counter:02d}"
            new_filename = f"{name_part}{suffix}{ext}"
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ex = QFastAddText()
    ex.show()
    sys.exit(app.exec_())
