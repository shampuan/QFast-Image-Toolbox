#!/usr/bin/env python3

import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QRadioButton, QPushButton, 
                             QGroupBox, QMessageBox, QCheckBox, QFrame, QGridLayout)
from PyQt5.QtGui import QIcon, QPalette, QColor
from PyQt5.QtCore import Qt
from PIL import Image

# Debian/Pardus grafik uyumluluğu
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class QFastResizer(QWidget):
    def __init__(self, cli_files=None):
        super().__init__()
        self.selected_files = cli_files if cli_files else []
        self.apply_dark_theme() # Stil burada uygulanıyor
        self.initUI()
        
        if self.selected_files:
            self.update_drop_label_info()

    def apply_dark_theme(self):
        # q.py dosyasındaki birebir palet ayarları
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(40, 40, 40))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.AlternateBase, QColor(45, 45, 45))
        palette.setColor(QPalette.ToolTipBase, Qt.white)
        palette.setColor(QPalette.ToolTipText, Qt.white)
        palette.setColor(QPalette.Text, Qt.white)
        palette.setColor(QPalette.Button, QColor(55, 55, 55))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.BrightText, Qt.red)
        palette.setColor(QPalette.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        # Radyo düğmelerinin içindeki beyazlığı ve pasif metinleri düzelten ayarlar
        palette.setColor(QPalette.Disabled, QPalette.Text, QColor(127, 127, 127))
        palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(127, 127, 127))
        palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(127, 127, 127))
        palette.setColor(QPalette.Disabled, QPalette.Highlight, QColor(80, 80, 80))
        
        self.setPalette(palette)
        # Uygulama genelinde paleti ayarla ki MessageBox da etkilensin
        if QApplication.instance():
            QApplication.instance().setPalette(palette)

    def initUI(self):
        self.setWindowTitle('QFast Image Resizer')
        
        # İkon yolu güncellendi: icons/resize.png
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'icons', 'resize.png')
        self.setWindowIcon(QIcon(icon_path)) 
        
        self.setFixedWidth(500)
        main_layout = QVBoxLayout()

        # Sürükle-Bırak Alanı
        self.drop_label = QLabel('\n\nDrag-Drop Image(s) Here\n\n')
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setMinimumHeight(120) 
        self.drop_label.setStyleSheet("""
            border: 2px dashed #555555; border-radius: 10px;
            color: #aaaaaa; font-weight: bold; background-color: #2a2a2a;
        """)
        self.setAcceptDrops(True)
        main_layout.addWidget(self.drop_label)

        # Seçenekler Çerçevesi
        options_frame = QFrame()
        options_frame.setFrameShape(QFrame.StyledPanel)
        grid_layout = QGridLayout(options_frame)

        # Resolution Mode
        self.rb_resolution = QRadioButton("Resolution Mode")
        self.rb_resolution.setChecked(True)
        self.rb_resolution.toggled.connect(self.toggle_modes)
        grid_layout.addWidget(self.rb_resolution, 0, 0)

        grid_layout.addWidget(QLabel("Width (px):"), 1, 0)
        self.edit_width = QLineEdit()
        self.edit_width.setPlaceholderText("Width")
        grid_layout.addWidget(self.edit_width, 2, 0)

        grid_layout.addWidget(QLabel("Height (px):"), 3, 0)
        self.edit_height = QLineEdit()
        self.edit_height.setPlaceholderText("Height")
        grid_layout.addWidget(self.edit_height, 4, 0)

        self.cb_ratio_text = "Keep Aspect Ratio"
        self.cb_keep_ratio = QCheckBox(self.cb_ratio_text)
        self.cb_keep_ratio.setChecked(True)
        grid_layout.addWidget(self.cb_keep_ratio, 5, 0)

        # Percent Mode
        self.rb_percent = QRadioButton("Percent Mode")
        self.rb_percent.toggled.connect(self.toggle_modes)
        grid_layout.addWidget(self.rb_percent, 0, 1)

        grid_layout.addWidget(QLabel("Enter (%):"), 1, 1)
        self.edit_percent = QLineEdit()
        self.edit_percent.setPlaceholderText("Example: 50")
        grid_layout.addWidget(self.edit_percent, 2, 1)

        main_layout.addWidget(options_frame)

        # Metaveri kutucuğu
        self.cb_keep_exif = QCheckBox("Keep Metadata (EXIF)")
        self.cb_keep_exif.setChecked(True)
        self.cb_keep_exif.setStyleSheet("margin-left: 5px; font-weight: bold; color: #aaaaaa;")
        main_layout.addWidget(self.cb_keep_exif)

        # Resampling Ayarı
        resampling_group = QGroupBox("Resampling Method")
        resampling_group.setStyleSheet("QGroupBox { color: #aaaaaa; }")
        resampling_layout = QHBoxLayout()
        self.rb_smooth = QRadioButton("Smooth (LANCZOS)")
        self.rb_smooth.setChecked(True)
        self.rb_pixel = QRadioButton("Pixelated (NEAREST)")
        resampling_layout.addWidget(self.rb_smooth)
        resampling_layout.addWidget(self.rb_pixel)
        resampling_group.setLayout(resampling_layout)
        main_layout.addWidget(resampling_group)

        # Butonlar
        btn_layout = QHBoxLayout()
        self.btn_do = QPushButton('Do it!')
        self.btn_do.setFixedHeight(40)
        self.btn_do.setStyleSheet("""
            QPushButton { background-color: #1a639b; color: white; font-weight: bold; border-radius: 5px; }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.btn_do.clicked.connect(self.process_image)

        self.btn_about = QPushButton('About')
        self.btn_about.setFixedHeight(40)
        self.btn_about.clicked.connect(self.show_about)

        btn_layout.addWidget(self.btn_do)
        btn_layout.addWidget(self.btn_about)
        main_layout.addLayout(btn_layout)

        self.setLayout(main_layout)
        self.update_ui_states()

    def update_drop_label_info(self):
        count = len(self.selected_files)
        text = f"{count} images selected" if count > 1 else f"Selected: {os.path.basename(self.selected_files[0])}"
        self.drop_label.setText(f"\n\n{text}\n\n")
        self.drop_label.setStyleSheet("border: 2px solid #27ae60; color: #27ae60; background-color: #1e2a1e;")

    def toggle_modes(self):
        self.update_ui_states()
        if self.rb_resolution.isChecked(): self.edit_percent.clear()
        else: self.edit_width.clear(); self.edit_height.clear()

    def update_ui_states(self):
        res_active = self.rb_resolution.isChecked()
        self.edit_width.setEnabled(res_active); self.edit_height.setEnabled(res_active)
        self.cb_keep_ratio.setEnabled(res_active); self.edit_percent.setEnabled(not res_active)

    def reset_ui(self):
        self.selected_files = []
        self.drop_label.setText('\n\nDrag-Drop Image(s) Here\n\n')
        self.drop_label.setStyleSheet("border: 2px dashed #555555; border-radius: 10px; color: #aaaaaa; font-weight: bold; background-color: #2a2a2a;")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        self.selected_files = [u.toLocalFile() for u in event.mimeData().urls()]
        if self.selected_files: self.update_drop_label_info()

    def get_unique_path(self, directory, base_name, extension):
        counter = 0
        while True:
            candidate = f"{base_name}_resized{f'_{counter}' if counter > 0 else ''}{extension}"
            full_path = os.path.join(directory, candidate)
            if not os.path.exists(full_path): return full_path
            counter += 1

    def process_image(self, silent=False, cli_params=None):
        if not self.selected_files:
            if not silent: QMessageBox.warning(self, "Error", "No images selected!")
            return

        try:
            if cli_params:
                mode, w, h, target_dir, keep_exif = cli_params
                method = Image.LANCZOS
            else:
                mode = "r" if self.rb_resolution.isChecked() else "p"
                w = self.edit_width.text()
                h = self.edit_height.text()
                perc = self.edit_percent.text()
                method = Image.LANCZOS if self.rb_smooth.isChecked() else Image.NEAREST
                target_dir = None
                keep_exif = self.cb_keep_exif.isChecked()
                if mode == "r" and not (w or h):
                    QMessageBox.warning(self, "Warning", "Please enter width or height!")
                    return

            for file_path in self.selected_files:
                img = Image.open(file_path)
                orig_w, orig_h = img.size
                exif_data = img.info.get('exif') if keep_exif else None

                if mode == "r":
                    new_w = int(w) if w else orig_w
                    new_h = int(h) if h else int(orig_h * (new_w / orig_w))
                else:
                    val = perc if not cli_params else w
                    p = int(val) / 100
                    new_w, new_h = int(orig_w * p), int(orig_h * p)

                save_dir = target_dir if target_dir else os.path.dirname(file_path)
                base_name, ext = os.path.splitext(os.path.basename(file_path))
                out_path = self.get_unique_path(save_dir, base_name, ext)

                resized = img.resize((new_w, new_h), method)
                resized.save(out_path, exif=exif_data) if exif_data else resized.save(out_path)

            if not silent: QMessageBox.information(self, "Success", "Processing complete!")
        except Exception as e:
            if not silent: QMessageBox.critical(self, "Error", str(e))
            else: print(f"CLI Error: {e}")
        finally:
            if not silent: self.reset_ui()

    def show_about(self):
        about_msg = QMessageBox(self)
        about_msg.setWindowTitle("About QFast Image Resizer")
        
        # MessageBox'ın stil paletini zorla uygula
        about_msg.setPalette(self.palette())
        
        base_path = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(base_path, 'icons', 'resize.png')
        logo_html = f"<center><img src='{icon_path}' width='64' height='64'></center>" if os.path.exists(icon_path) else ""
        content = f"""
        {logo_html}
        <center><h2 style='color:#1a639b;'>QFast Image Resizer</h2></center>
        <div style='text-align: left; margin-left: 20px; color: white;'>
            <p><b>License:</b> GNU GPLv3<br>
            <b>Language:</b> Python3<br>
            <b>UI:</b> Qt5<br>
            <b>Author:</b> A. Serhat KILIÇOĞLU (shampuan)<br>
            <b>Github:</b> <a href='https://www.github.com/shampuan' style='color:#2980b9;'>www.github.com/shampuan</a></p>
        </div>
        <hr>
        <center style='color: #aaaaaa;'>
            <p>This program was prepared to resize your images quickly.</p>
            <p><i>This program comes with no warranty.</i></p>
            <p>Copyright © 2025 - A. Serhat KILIÇOĞLU</p>
        </center>
        """
        about_msg.setTextFormat(Qt.RichText)
        about_msg.setText(content)
        about_msg.exec_()

def print_help():
    help_text = """
QFast Image Resizer - CLI Help Guide
------------------------------------
Usage: qfast [mode] [parameters] [source_file] [target_directory(optional)]

Modes:
  r : Resolution Mode (Pixel based)
  p : Percent Mode (Percentage based)

Parameters:
  wXXX : Set Width (e.g., w800) or Percentage (e.g., w50)
  hXXX : Set Height (e.g., h600) - Only for Resolution Mode
  m    : Keep Metadata (EXIF)

Examples:
  qfast r w800 photo.jpg           -> Resize photo to 800px width (aspect ratio kept)
  qfast r w1920 h1080 m photo.jpg  -> Resize to 1920x1080 and keep metadata
  qfast p w50 photo.jpg            -> Resize photo to 50% of its original size
  qfast r w400 photo.jpg /tmp/     -> Resize and save to /tmp directory
------------------------------------
Author: A. Serhat KILICOGLU (shampuan)
    """
    print(help_text)

def run_cli(args):
    try:
        if not args or args[0].lower() in ['-h', '--help', 'help']:
            print_help()
            return

        mode = args[0].lower()
        if mode not in ['r', 'p']:
            raise Exception("Invalid mode! Use 'r' for Resolution or 'p' for Percent.")

        width = None; height = None; source = None; target = None; keep_exif = False

        for arg in args[1:]:
            a = arg.lower()
            if a.startswith('w'): width = a.replace('w', '')
            elif a.startswith('h'): height = a.replace('h', '')
            elif a == 'm': keep_exif = True
            elif os.path.isfile(arg): source = arg
            elif os.path.isdir(arg): target = arg

        if not source:
            raise Exception("Source file not found or not specified.")
        if not width:
            raise Exception("Width or Percentage (wXXX) must be specified.")
        
        app = QApplication(sys.argv)
        app.setStyle("Fusion")
        logic = QFastResizer(cli_files=[source])
        logic.process_image(silent=True, cli_params=(mode, width, height, target, keep_exif))
        print(f"SUCCESS: Processed {os.path.basename(source)}")
    except Exception as e:
        print(f"CLI Error: {e}")
        print("Type 'qfast help' for usage instructions.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Dark theme desteği için Fusion stili şarttır
    if len(sys.argv) > 1 and (sys.argv[1].lower() in ['r', 'p', 'help', '-h', '--help']):
        run_cli(sys.argv[1:])
    else:
        files = sys.argv[1:] if len(sys.argv) > 1 else None
        ex = QFastResizer(cli_files=files)
        ex.show()
        sys.exit(app.exec_())