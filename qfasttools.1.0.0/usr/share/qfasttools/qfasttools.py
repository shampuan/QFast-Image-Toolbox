#!/usr/bin/env python3
import sys
import os
import subprocess
import ctypes
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QGridLayout, QMessageBox)
from PyQt5.QtGui import QIcon, QPalette, QColor, QPixmap
from PyQt5.QtCore import Qt, QSize

# --- İKON SORUNUNU ÇÖZEN SATIRLAR ---
myappid = 'shampuan.qfasttools.v1' 
try:
    # Linux/X11 üzerinde WM_CLASS ataması yaparak panel ikonunu bağlar
    ctypes.CDLL('libX11.so.6').XStoreName
except:
    pass
# -----------------------------------

class QFastMain(QWidget):
    def __init__(self):
        super().__init__()
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.icon_dir = os.path.join(self.base_dir, "icons")
        self.initUI()

    def initUI(self):
        self.apply_dark_theme()
        self.setWindowTitle('QFast Image Toolbox')
        self.setFixedSize(620, 480) 

        # Pencere İkonu
        self.icon_path = os.path.join(self.icon_dir, "QFastTools.png")
        self.setWindowIcon(QIcon(self.icon_path))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(0) 

        # LOGO
        if os.path.exists(self.icon_path):
            logo_label = QLabel()
            logo_pixmap = QPixmap(self.icon_path)
            logo_label.setPixmap(logo_pixmap.scaled(90, 90, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            logo_label.setAlignment(Qt.AlignCenter)
            logo_label.setStyleSheet("margin-bottom: 5px;")
            main_layout.addWidget(logo_label)

        # BAŞLIK
        header = QLabel("Image Manipulation Suite")
        header.setStyleSheet("""
            font-weight: bold; 
            color: #aaaaaa; 
            font-size: 18pt; 
            margin-bottom: 15px; 
        """)
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)

        # Izgara Düzeni (Grid)
        grid_layout = QGridLayout()
        grid_layout.setSpacing(8)

        # Buton Listesi ve Sıralaması
        tools = [
            ("Resize", "resize.py", "resize.png"),
            ("Crop", "crop.py", "crop.png"),
            ("Duplicate", "duplicate.py", "duplicate.png"),
            ("Adjust", "adjust.py", "adjust.png"),
            ("Flip/Rotate", "fliprotate.py", "flip-rotate.png"),
            ("Add Text", "addtext.py", "addtext.png"),
            ("Invert", "invert.py", "invert.png"),
            ("Censor", "censor.py", "censor.png"),
            ("EXIF Clean", "removeexif.py", "deleteexif.png")
        ]

        row, col = 0, 0
        for text, file_name, icon_file in tools:
            btn = QPushButton(f"  {text}")
            btn.setMinimumHeight(75)
            btn.setStyleSheet("QPushButton { text-align: left; padding-left: 10px; font-weight: bold; }")
            
            icon_button_path = os.path.join(self.icon_dir, icon_file)
            if os.path.exists(icon_button_path):
                btn.setIcon(QIcon(icon_button_path))
                btn.setIconSize(QSize(48, 48))
            
            btn.clicked.connect(lambda checked, f=file_name: self.run_tool(f))
            grid_layout.addWidget(btn, row, col)
            col += 1
            if col > 2:
                col = 0
                row += 1

        main_layout.addLayout(grid_layout)
        main_layout.addSpacing(20) 

        # Alt Butonlar
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        
        btn_lang = QPushButton("Language")
        btn_lang.setFixedWidth(85)
        btn_lang.clicked.connect(self.show_language_warning)
        
        btn_about = QPushButton("About")
        btn_about.setFixedWidth(85)
        btn_about.clicked.connect(self.show_about)
        
        bottom_layout.addWidget(btn_lang)
        bottom_layout.addWidget(btn_about)
        main_layout.addLayout(bottom_layout)

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(40, 40, 40))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Button, QColor(55, 55, 55))
        palette.setColor(QPalette.ButtonText, Qt.white)
        palette.setColor(QPalette.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.Text, Qt.white)
        QApplication.setPalette(palette)

    def run_tool(self, file_name):
        script_path = os.path.join(self.base_dir, file_name)
        if os.path.exists(script_path):
            try:
                subprocess.Popen([sys.executable, script_path])
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not start the tool: {str(e)}")
        else:
            QMessageBox.information(self, "Missing File", f"The file '{file_name}' was not found.")

    def show_language_warning(self):
        # Çok dilli uyarı mesajı
        lang_text = (
            "Maalesef henüz dinamik dil desteği mevcut değil.\n"
            "Unfortunately, dynamic language support is not yet available.\n"
            "Leider ist die dynamische Sprachunterstützung noch nicht verfügbar.\n"
            "Malheureusement, le support linguistique dynamique n'est pas encore disponible.\n"
            "Purtroppo il supporto linguistico dinamico non è ancora disponibile.\n"
            "К сожалению, динамическая языковая поддержка пока недоступна.\n"
            "残念ながら、動的な言語サポートはまだ利用できません。\n"
            "很遗憾，目前还不支持动态语言。\n"
            "안타깝게도 아직 동적 언어 지원을 사용할 수 없습니다."
        )
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Language")
        msg.setIcon(QMessageBox.Information)
        msg.setText(lang_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.button(QMessageBox.Ok).setText("OK")
        msg.exec_()

    def show_about(self):
        about_text = """
        <h2 style='color: #aaaaaa;'>About QFast Image Toolbox</h2>
        <p><b>Version:</b> 1.0.0<br>
        <b>License:</b> GNU GPLv3<br>
        <b>GUI:</b> PyQt5<br>
        <b>Language:</b> Python3<br>
        <b>Developer:</b> A. Serhat KILIÇOĞLU (shampuan)<br>
        <b>Github:</b> <a href='https://www.github.com/shampuan' style='color: #4a9eff;'>www.github.com/shampuan</a></p>
        
        <p>This is a fast and practical set of tools where you can make many <br>
        adjustments to your images.</p>
        
        <p><i>This program comes with absolutely no warranty.</i></p>
        
        <p>Copyright © 2025 - A. Serhat KILIÇOĞLU</p>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("About")
        
        if os.path.exists(self.icon_path):
            pixmap = QPixmap(self.icon_path).scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            msg.setIconPixmap(pixmap)
            
        msg.setTextFormat(Qt.RichText)
        msg.setText(about_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.button(QMessageBox.Ok).setText("OK")
        msg.exec_()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setDesktopFileName("qfasttools.desktop")
    app.setStyle("Fusion")
    ex = QFastMain()
    ex.show()
    sys.exit(app.exec_())
