#!/usr/bin/env python3
import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QListWidget, QComboBox, 
                             QCheckBox, QProgressBar, QFileDialog, QMessageBox, QSlider, QListWidgetItem, QGroupBox)
from PyQt5.QtGui import QPalette, QColor, QBrush, QIcon
from PyQt5.QtCore import Qt
from PIL import Image

# Debian/Pardus grafik uyumluluğu
os.environ['QT_QPA_PLATFORM'] = 'xcb'

try:
    import pillow_avif
except ImportError:
    pass

class ConverterTool(QWidget):
    def __init__(self):
        super().__init__()
        self.dest_path = ""
        self.initUI()
        self.setAcceptDrops(True)

    def initUI(self):
        self.setWindowTitle('QFast - Smart Format Converter')
        self.setFixedSize(850, 650)
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "icons", "format.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.apply_theme_logic()

        main_layout = QHBoxLayout(self)

        # --- LEFT PANEL ---
        left_layout = QVBoxLayout()
        self.label_info = QLabel("Drag & Drop or Add Files")
        self.label_info.setStyleSheet("color: #aaaaaa; border: 2px dashed #555; padding: 10px;")
        self.label_info.setAlignment(Qt.AlignCenter)
        
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(QListWidget.MultiSelection)
        self.file_list.setStyleSheet("background-color: #252525; border: 1px solid #444; color: #eee;")

        btn_list_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add Files")
        self.btn_add.clicked.connect(self.open_file_dialog)
        self.btn_remove = QPushButton("Remove Selected")
        self.btn_remove.clicked.connect(self.remove_files)
        self.btn_clear = QPushButton("Clear List")
        self.btn_clear.clicked.connect(self.file_list.clear)
        
        btn_list_layout.addWidget(self.btn_add)
        btn_list_layout.addWidget(self.btn_remove)
        btn_list_layout.addWidget(self.btn_clear)

        left_layout.addWidget(self.label_info)
        left_layout.addWidget(self.file_list)
        left_layout.addLayout(btn_list_layout)

        # --- RIGHT PANEL ---
        right_layout = QVBoxLayout()
        group_settings = QGroupBox("Conversion Settings")
        settings_layout = QVBoxLayout()
        settings_layout.setSpacing(12)

        # --- RESIZE SECTION ---
        self.check_resize = QCheckBox("Enable Resize (%)")
        self.check_resize.setChecked(False)
        self.check_resize.toggled.connect(self.toggle_resize_slider)
        settings_layout.addWidget(self.check_resize)

        self.label_resize = QLabel("Scale: 100%")
        settings_layout.addWidget(self.label_resize)
        
        self.slider_resize = QSlider(Qt.Horizontal)
        self.slider_resize.setRange(10, 100)
        self.slider_resize.setValue(100)
        self.slider_resize.valueChanged.connect(self.update_resize_label)
        settings_layout.addWidget(self.slider_resize)

        # Başlangıç durumu (Kodun manuel tetiklenmesi yerine ilk ayar)
        self.toggle_resize_slider(False) 

        settings_layout.addSpacing(5)

        # --- OTHER SETTINGS ---
        settings_layout.addWidget(QLabel("Target Format:"))
        self.combo_format = QComboBox()
        self.combo_format.addItems(["JPEG", "PNG", "WebP", "AVIF", "BMP", "PDF"])
        self.combo_format.currentTextChanged.connect(self.toggle_options)
        settings_layout.addWidget(self.combo_format)

        self.quality_label = QLabel("Quality / Effort: 85%")
        settings_layout.addWidget(self.quality_label)
        self.slider_quality = QSlider(Qt.Horizontal)
        self.slider_quality.setRange(1, 100)
        self.slider_quality.setValue(85)
        self.slider_quality.valueChanged.connect(self.update_quality_label)
        settings_layout.addWidget(self.slider_quality)

        self.check_merge_pdf = QCheckBox("Merge into a single PDF")
        self.check_merge_pdf.setVisible(False)
        settings_layout.addWidget(self.check_merge_pdf)

        self.check_exif = QCheckBox("Preserve EXIF Data")
        self.check_exif.setChecked(True)
        settings_layout.addWidget(self.check_exif)

        settings_layout.addSpacing(10)
        self.check_default_dir = QCheckBox("Save to source folder")
        self.check_default_dir.setChecked(True)
        self.check_default_dir.toggled.connect(self.toggle_folder_button)
        settings_layout.addWidget(self.check_default_dir)

        self.btn_dest = QPushButton("Select Output Folder")
        self.btn_dest.setEnabled(False)
        self.btn_dest.clicked.connect(self.select_dest_folder)
        settings_layout.addWidget(self.btn_dest)
        
        self.label_dest = QLabel("Location: Source Folder")
        self.label_dest.setWordWrap(True)
        self.label_dest.setStyleSheet("font-size: 8pt; color: #888;")
        settings_layout.addWidget(self.label_dest)

        group_settings.setLayout(settings_layout)
        right_layout.addWidget(group_settings)

        right_layout.addStretch()

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_layout.addWidget(self.progress_bar)

        self.btn_convert = QPushButton("DO IT!")
        self.btn_convert.setMinimumHeight(50)
        self.btn_convert.clicked.connect(self.start_conversion)
        right_layout.addWidget(self.btn_convert)

        main_layout.addLayout(left_layout, 60)
        main_layout.addLayout(right_layout, 40)

    def apply_theme_logic(self):
        p = QPalette()
        p.setColor(QPalette.Window, QColor(40, 40, 40))
        p.setColor(QPalette.WindowText, Qt.white)
        p.setColor(QPalette.Base, QColor(30, 30, 30))
        p.setColor(QPalette.Text, Qt.white)
        p.setColor(QPalette.Button, QColor(60, 60, 60))
        p.setColor(QPalette.ButtonText, Qt.white)
        p.setColor(QPalette.Highlight, QColor(52, 152, 219))
        p.setColor(QPalette.HighlightedText, Qt.white)
        
        # Devre dışı (Disabled) bileşenler için gri tonlar
        p.setColor(QPalette.Disabled, QPalette.WindowText, QColor(100, 100, 100))
        p.setColor(QPalette.Disabled, QPalette.Text, QColor(100, 100, 100))
        p.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(100, 100, 100))
        p.setColor(QPalette.Disabled, QPalette.Base, QColor(45, 45, 45))
        
        self.setPalette(p)

    def toggle_resize_slider(self, checked):
        # Sadece Qt'nin kendi mekanizmasını kullanıyoruz, yapay stil (setStyleSheet) yok!
        self.slider_resize.setEnabled(checked)
        self.label_resize.setEnabled(checked)

    def update_resize_label(self, val):
        self.label_resize.setText(f"Scale: {val}%")

    def update_quality_label(self, val):
        fmt = self.combo_format.currentText()
        if fmt == "PNG":
            level = int(val / 11)
            self.quality_label.setText(f"Compression Effort: {level} (0-9)")
        else:
            self.quality_label.setText(f"Quality: {val}%")

    def toggle_options(self, fmt):
        self.check_merge_pdf.setVisible(fmt == "PDF")
        self.slider_quality.setEnabled(fmt not in ["PDF", "BMP"])
        self.update_quality_label(self.slider_quality.value())

    def toggle_folder_button(self, checked):
        self.btn_dest.setEnabled(not checked)
        if checked:
            self.label_dest.setText("Location: Source Folder")
            self.dest_path = ""

    def select_dest_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.dest_path = folder
            self.label_dest.setText(f"Location: {folder}")

    def add_to_list(self, path):
        valid_extensions = ('.png', '.jpg', '.jpeg', '.webp', '.avif', '.bmp', '.tiff')
        if path.lower().endswith(valid_extensions):
            file_name = os.path.basename(path)
            dir_name = os.path.dirname(path)
            display_text = f"{file_name}  —  ({dir_name})"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, path)
            item.setForeground(QBrush(QColor(220, 220, 220))) 
            self.file_list.addItem(item)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()

    def dropEvent(self, event):
        for u in event.mimeData().urls():
            f = u.toLocalFile()
            self.add_to_list(f)

    def open_file_dialog(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", "Images (*.png *.jpg *.jpeg *.webp *.avif *.bmp *.tiff);;All Files (*)")
        for f in files: self.add_to_list(f)

    def remove_files(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))

    def start_conversion(self):
        count = self.file_list.count()
        if count == 0:
            QMessageBox.warning(self, "Warning", "Please add some files first.")
            return

        target_fmt = self.combo_format.currentText()
        quality = self.slider_quality.value()
        resize_scale = self.slider_resize.value() if self.check_resize.isChecked() else 100
        
        self.progress_bar.setMaximum(count)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        QApplication.processEvents()

        if target_fmt == "PDF" and self.check_merge_pdf.isChecked():
            self.merge_to_pdf(resize_scale)
        else:
            success = 0
            for i in range(count):
                original_path = self.file_list.item(i).data(Qt.UserRole)
                if self.process_single_image(original_path, target_fmt, quality, resize_scale):
                    success += 1
                self.progress_bar.setValue(i + 1)
                QApplication.processEvents()
            
            QMessageBox.information(self, "Finished", f"{success} files converted successfully.")
        
        self.progress_bar.setVisible(False)

    def process_single_image(self, path, fmt, qual, scale):
        try:
            img = Image.open(path)
            if scale < 100:
                new_size = (max(1, int(img.width * (scale/100))), max(1, int(img.height * (scale/100))))
                img = img.resize(new_size, Image.Resampling.LANCZOS)

            if fmt == "JPEG":
                if img.mode in ("RGBA", "P"):
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    mask = img.split()[3] if img.mode == "RGBA" else None
                    background.paste(img, mask=mask)
                    img = background
                else:
                    img = img.convert("RGB")
            elif fmt in ["PNG", "WebP", "AVIF"]:
                if img.mode not in ("RGBA", "RGB", "P"):
                    img = img.convert("RGBA")

            out_dir = self.dest_path if (self.dest_path and not self.check_default_dir.isChecked()) else os.path.dirname(path)
            base_name = os.path.splitext(os.path.basename(path))[0]
            
            c = 1
            while True:
                new_name = f"{base_name}.converted{c}.{fmt.lower()}"
                final_out = os.path.join(out_dir, new_name)
                if not os.path.exists(final_out): break
                c = c + 1

            save_args = {"format": fmt}
            if fmt == "PNG":
                save_args["optimize"] = True
                save_args["compress_level"] = max(0, min(9, int(qual / 11)))
            elif fmt in ["JPEG", "WebP", "AVIF"]:
                save_args["optimize"] = True
                save_args["quality"] = qual

            if self.check_exif.isChecked() and "exif" in img.info:
                save_args["exif"] = img.info["exif"]
            
            img.save(final_out, **save_args)
            return True
        except Exception:
            return False

    def merge_to_pdf(self, scale):
        try:
            pdf_list = []
            for i in range(self.file_list.count()):
                path = self.file_list.item(i).data(Qt.UserRole)
                img = Image.open(path).convert("RGB")
                if scale < 100:
                    new_size = (max(1, int(img.width * (scale/100))), max(1, int(img.height * (scale/100))))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                pdf_list.append(img)
            
            save_path, _ = QFileDialog.getSaveFileName(self, "Save as PDF", "merged.pdf", "*.pdf")
            if save_path:
                pdf_list[0].save(save_path, save_all=True, append_images=pdf_list[1:])
                QMessageBox.information(self, "Success", "PDF created successfully.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ConverterTool()
    win.show()
    sys.exit(app.exec_())
