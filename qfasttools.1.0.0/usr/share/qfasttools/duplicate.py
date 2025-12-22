#!/usr/bin/env python3
import sys
import os
import io
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QMessageBox, QSlider, 
                             QGroupBox, QFrame, QCheckBox, QComboBox)
from PyQt5.QtGui import QPixmap, QImage, QCursor, QPalette, QColor, QIcon
from PyQt5.QtCore import Qt, QTimer
from PIL import Image
import sip

# Debian/Pardus grafik uyumluluğu
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class QFastPhotoDuplicator(QWidget):
    def __init__(self, target_file=None):
        super().__init__()
        self.image_path = target_file
        self.original_full = None
        self.proxy_image = None
        self.display_image = None
        
        self.preview_timer = QTimer()
        self.preview_timer.setSingleShot(True)
        self.preview_timer.timeout.connect(self.process_preview)
        
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
        self.setWindowTitle('QFast Photo Duplicator')
        
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'icons', 'duplicate.png')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.setMinimumSize(1000, 750)
        
        main_layout = QHBoxLayout(self)

        # SOL: Önizleme
        self.img_display = QLabel("Drop Photo Here")
        self.img_display.setAlignment(Qt.AlignCenter)
        self.img_display.setFrameShape(QFrame.StyledPanel)
        self.img_display.setStyleSheet("border: 2px dashed #666; background-color: #222; color: #888;")
        self.setAcceptDrops(True)
        main_layout.addWidget(self.img_display, stretch=4)

        # SAĞ: Kontrol Paneli
        side_panel = QVBoxLayout()

        adj_group = QGroupBox("Duplication Settings")
        adj_lay = QVBoxLayout()
        
        # Dizilim Seçeneği
        adj_lay.addWidget(QLabel("Select Layout"))
        self.combo_layout = QComboBox()
        self.layouts = {
            "4 Photos (2x2)": (2, 2),
            "6 Photos (2x3)": (2, 3),
            "8 Photos (2x4)": (2, 4),
            "9 Photos (3x3)": (3, 3),
            "12 Photos (3x4)": (3, 4),
            "16 Photos (4x4)": (4, 4)
        }
        self.combo_layout.addItems(self.layouts.keys())
        self.combo_layout.currentIndexChanged.connect(self.request_preview)
        adj_lay.addWidget(self.combo_layout)

        # Boşluk (Artık % bazında çalışıyor)
        adj_lay.addWidget(QLabel("Spacing (%)"))
        self.sld_spacing = QSlider(Qt.Horizontal)
        self.sld_spacing.setRange(0, 50) # %0 ile %50 arası makul bir boşluk
        self.sld_spacing.setValue(5)
        self.sld_spacing.valueChanged.connect(self.request_preview)
        adj_lay.addWidget(self.sld_spacing)

        # Arka Plan
        self.cb_white_border = QCheckBox("White Background")
        self.cb_white_border.setChecked(True)
        self.cb_white_border.stateChanged.connect(self.request_preview)
        adj_lay.addWidget(self.cb_white_border)

        adj_group.setLayout(adj_lay)

        self.cb_keep_exif = QCheckBox("Keep Metadata (EXIF)")
        self.cb_keep_exif.setChecked(True)
        self.cb_keep_exif.setStyleSheet("font-weight: bold; color: #aaaaaa; margin-top: 10px;")

        self.btn_do_it = QPushButton("SAVE FINAL SHEET")
        self.btn_do_it.setFixedHeight(60)
        self.btn_do_it.setEnabled(False)
        self.btn_do_it.clicked.connect(self.process_final_render)

        side_panel.addWidget(adj_group)
        side_panel.addWidget(self.cb_keep_exif)
        side_panel.addStretch()
        side_panel.addWidget(self.btn_do_it)
        
        main_layout.addLayout(side_panel, stretch=1)

    def load_image(self, path):
        try:
            self.image_path = path
            self.original_full = Image.open(path)
            w, h = self.original_full.size
            # Proxy boyutu (Işık/Kontrast modülündeki gibi)
            self.proxy_image = self.original_full.resize((w//5, h//5), Image.LANCZOS)
            self.btn_do_it.setEnabled(True)
            self.request_preview()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Load failed: {e}")

    def create_multi_layout(self, source_img):
        w, h = source_img.size
        
        # BOŞLUK HESAPLAMA: Piksel yerine fotoğraf genişliğinin yüzdesi (%)
        # Bu sayede proxy resimde de orijinal resimde de oran aynı kalır.
        spacing_percent = self.sld_spacing.value() / 100.0
        spacing_px = int(w * spacing_percent)
        
        selected_text = self.combo_layout.currentText()
        rows, cols = self.layouts[selected_text]
        
        bg_color = (255, 255, 255) if self.cb_white_border.isChecked() else (0, 0, 0)
        
        # Toplam boyutları hesapla
        total_w = (w * cols) + (spacing_px * (cols + 1))
        total_h = (h * rows) + (spacing_px * (rows + 1))
        
        canvas = Image.new('RGB', (total_w, total_h), bg_color)
        
        for r in range(rows):
            for c in range(cols):
                x = spacing_px + (c * (w + spacing_px))
                y = spacing_px + (r * (h + spacing_px))
                canvas.paste(source_img, (x, y))
        
        return canvas

    def request_preview(self):
        self.preview_timer.start(50)

    def process_preview(self):
        if not self.proxy_image: return
        self.display_image = self.create_multi_layout(self.proxy_image)
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
            # Orijinal resim üzerinden render alındığında spacing_px otomatik olarak artacak
            work_img = self.create_multi_layout(self.original_full)
            output_path = self.get_unique_path()
            
            save_params = {}
            if self.cb_keep_exif.isChecked():
                exif = self.original_full.info.get('exif')
                if exif: save_params['exif'] = exif

            work_img.save(output_path, quality=95, **save_params)
            QMessageBox.information(self, "Success", f"Photo sheet saved as:\n{os.path.basename(output_path)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Render failed: {e}")
        finally:
            QApplication.restoreOverrideCursor()

    def get_unique_path(self):
        directory = os.path.dirname(self.image_path)
        name_part, ext = os.path.splitext(os.path.basename(self.image_path))
        if "_sheet" in name_part: name_part = name_part.split("_sheet")[0]
        
        counter = 1
        while True:
            new_filename = f"{name_part}_sheet{counter:02d}{ext if ext else '.jpg'}"
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
    ex = QFastPhotoDuplicator()
    ex.show()
    sys.exit(app.exec_())