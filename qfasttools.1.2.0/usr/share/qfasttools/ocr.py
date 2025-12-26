#!/usr/bin/env python3
import sys
import os
import subprocess
import tempfile
import re
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QTextEdit, QFileDialog, 
                             QMessageBox, QFrame, QComboBox)
from PyQt5.QtGui import QPixmap, QColor, QPalette, QIcon
from PyQt5.QtCore import Qt

class OCRTool(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setAcceptDrops(True)
        self.input_path = None

    def initUI(self):
        self.setWindowTitle('QFast OCR Tool')
        self.setFixedSize(850, 520)
        
        # İkon ekleme bölümü
        script_dir = os.path.dirname(os.path.realpath(__file__))
        icon_path = os.path.join(script_dir, "icons", "ocr.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
            
        self.apply_dark_theme()

        main_layout = QHBoxLayout(self)

        # --- LEFT SECTION ---
        left_frame = QFrame()
        left_frame.setFrameShape(QFrame.StyledPanel)
        left_layout = QVBoxLayout(left_frame)

        self.label_image = QLabel("Drag & Drop Image Here")
        self.label_image.setAlignment(Qt.AlignCenter)
        self.label_image.setStyleSheet("border: 2px dashed #555; background: #222; color: #bbb;")
        self.label_image.setMinimumSize(400, 450)
        left_layout.addWidget(self.label_image)

        # --- RIGHT SECTION ---
        right_frame = QFrame()
        right_frame.setFrameShape(QFrame.StyledPanel)
        right_frame.setFixedWidth(380)
        right_layout = QVBoxLayout(right_frame)

        right_layout.addWidget(QLabel("Extracted Text:"))
        self.text_output = QTextEdit()
        # Yazı rengini beyaza sabitleyip arka planı koyulaştırıyoruz
        self.text_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #444;
                font-size: 10pt;
            }
        """)
        self.text_output.setPlaceholderText("Text will appear here...")
        right_layout.addWidget(self.text_output)

        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Language:"))
        self.combo_lang = QComboBox()
        self.combo_lang.addItems(["English (eng)", "Turkish (tur)"])
        lang_layout.addWidget(self.combo_lang)
        right_layout.addLayout(lang_layout)

        right_layout.addSpacing(10)

        self.btn_scan = QPushButton("Scan Text")
        self.btn_scan.setFixedHeight(40)
        self.btn_scan.setEnabled(False)
        self.btn_scan.clicked.connect(self.perform_ocr)
        right_layout.addWidget(self.btn_scan)

        btn_copy = QPushButton("Copy to Clipboard")
        btn_copy.clicked.connect(self.copy_text)
        right_layout.addWidget(btn_copy)

        btn_save = QPushButton("Save as .txt")
        btn_save.clicked.connect(self.save_text)
        right_layout.addWidget(btn_save)

        btn_clear = QPushButton("Clear")
        btn_clear.clicked.connect(self.clear_all)
        right_layout.addWidget(btn_clear)

        main_layout.addWidget(left_frame)
        main_layout.addWidget(right_frame)

    def apply_dark_theme(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(40, 40, 40))
        palette.setColor(QPalette.WindowText, Qt.white)
        palette.setColor(QPalette.Base, QColor(30, 30, 30))
        palette.setColor(QPalette.Button, QColor(60, 60, 60))
        palette.setColor(QPalette.ButtonText, Qt.white)
        # Combobox ve Label metinleri için ek koruma
        palette.setColor(QPalette.Text, Qt.white) 
        self.setPalette(palette)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()
        else: event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files: self.load_image(files[0])

    def load_image(self, path):
        self.input_path = path
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.label_image.setPixmap(pixmap.scaled(self.label_image.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
            self.label_image.setText("")
            self.btn_scan.setEnabled(True)

    def clean_text(self, raw_text):
        """Mizanpaj hatalarını ve gereksiz boşlukları temizler."""
        # 1. Satır sonlarındaki gereksiz enter'ları kaldır (paragrafları korumaya çalışarak)
        # İki enter üst üste gelmemişse bunları tek bir boşluğa çevirir
        cleaned = re.sub(r'(?<!\n)\n(?!\n)', ' ', raw_text)
        
        # 2. Birden fazla boşluğu teke indir
        cleaned = re.sub(r' +', ' ', cleaned)
        
        # 3. Kenarlardaki boşlukları temizle
        cleaned = cleaned.strip()
        
        return cleaned

    def perform_ocr(self):
        if not self.input_path: return
        lang = self.combo_lang.currentText().split('(')[1].replace(')', '')
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_base = os.path.join(temp_dir, "ocr_res")
            try:
                # Tesseract çalıştırılırken 'quiet' modda çalışması için stderr yönlendirilebilir
                subprocess.run(['tesseract', self.input_path, output_base, '-l', lang], 
                               check=True, capture_output=True)
                
                result_file = output_base + ".txt"
                if os.path.exists(result_file):
                    with open(result_file, 'r', encoding='utf-8') as f:
                        raw_text = f.read()
                        # Metni mizanpaj hatalarından arındırıyoruz
                        final_text = self.clean_text(raw_text)
                        self.text_output.setText(final_text if final_text else "No text found!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"OCR failed: {str(e)}")

    def copy_text(self):
        QApplication.clipboard().setText(self.text_output.toPlainText())

    def save_text(self):
        content = self.text_output.toPlainText()
        if not content: return
        dir_name = os.path.dirname(self.input_path) if self.input_path else ""
        base_name = os.path.splitext(os.path.basename(self.input_path))[0] if self.input_path else "scanned"
        path, _ = QFileDialog.getSaveFileName(self, "Save Text", os.path.join(dir_name, f"{base_name}.txt"), "Text Files (*.txt)")
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

    def clear_all(self):
        self.label_image.clear()
        self.label_image.setText("Drag & Drop Image Here")
        self.text_output.clear()
        self.input_path = None
        self.btn_scan.setEnabled(False)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = OCRTool()
    window.show()
    sys.exit(app.exec_())