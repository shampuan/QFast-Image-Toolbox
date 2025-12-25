#!/usr/bin/env python3
import sys
import os
import qrcode
from PIL import Image
from pyzbar.pyzbar import decode
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QTextEdit, QFileDialog, 
                             QMessageBox, QFrame)
from PyQt5.QtGui import QPixmap, QColor, QPalette, QIcon
from PyQt5.QtCore import Qt

# Debian/Pardus grafik uyumluluğu
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class QRTool(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setAcceptDrops(True)
        self.current_qr_img = None
        self.logo_path = None

    def initUI(self):
        self.setWindowTitle('QFast QR Tool')
        self.setFixedSize(850, 520)
        
        # 1- İkon ayarı (icons/qrtool.png)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        icon_path = os.path.join(script_dir, "icons", "qrtool.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.apply_dark_theme()

        main_layout = QHBoxLayout(self)

        # Yazı rengi stili (Beyaz metinler için)
        label_style = "color: white;"

        # --- LEFT PANEL: GENERATOR ---
        left_frame = QFrame()
        left_frame.setFrameShape(QFrame.StyledPanel)
        left_layout = QVBoxLayout(left_frame)

        lbl_input = QLabel("Enter Text or Link:")
        lbl_input.setStyleSheet(label_style)
        left_layout.addWidget(lbl_input)
        
        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText("Type content to be converted to QR code...")
        self.text_input.setMaximumHeight(80)
        self.text_input.setStyleSheet("color: white; background-color: #222;")
        left_layout.addWidget(self.text_input)

        self.btn_select_logo = QPushButton("Select Center Logo (Optional)")
        self.btn_select_logo.clicked.connect(self.select_logo)
        left_layout.addWidget(self.btn_select_logo)
        
        self.label_logo_info = QLabel("No Logo Selected")
        self.label_logo_info.setStyleSheet("color: #888; font-size: 8pt;")
        left_layout.addWidget(self.label_logo_info)

        self.btn_generate = QPushButton("GENERATE QR")
        self.btn_generate.setFixedHeight(40)
        self.btn_generate.clicked.connect(self.generate_qr)
        left_layout.addWidget(self.btn_generate)

        self.qr_preview = QLabel("Preview")
        self.qr_preview.setAlignment(Qt.AlignCenter)
        self.qr_preview.setFixedSize(220, 220)
        self.qr_preview.setStyleSheet("border: 1px dashed #666; background: #222; margin-top: 5px; color: white;")
        left_layout.addWidget(self.qr_preview, alignment=Qt.AlignCenter)

        self.btn_save = QPushButton("SAVE AS PNG")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.save_qr)
        left_layout.addWidget(self.btn_save)

        # --- RIGHT PANEL: READER ---
        right_frame = QFrame()
        right_frame.setFrameShape(QFrame.StyledPanel)
        right_layout = QVBoxLayout(right_frame)

        lbl_reader = QLabel("QR Reader:")
        lbl_reader.setStyleSheet(label_style)
        right_layout.addWidget(lbl_reader)
        
        self.label_drop = QLabel("Drag & Drop Image Here")
        self.label_drop.setAlignment(Qt.AlignCenter)
        self.label_drop.setStyleSheet("border: 2px dashed #555; padding: 20px; background: #2b2b2b; color: #aaaaaa;")
        self.label_drop.setMinimumHeight(180)
        right_layout.addWidget(self.label_drop)

        self.btn_open = QPushButton("SELECT FILE")
        self.btn_open.clicked.connect(self.open_qr)
        right_layout.addWidget(self.btn_open)

        lbl_result = QLabel("Decoded Result:")
        lbl_result.setStyleSheet(label_style)
        right_layout.addWidget(lbl_result)
        
        self.text_output = QTextEdit()
        self.text_output.setReadOnly(True)
        self.text_output.setMaximumHeight(100)
        self.text_output.setStyleSheet("background-color: #1e1e1e; color: #00ff00;")
        right_layout.addWidget(self.text_output)

        self.btn_copy = QPushButton("COPY RESULT")
        self.btn_copy.clicked.connect(self.copy_output)
        right_layout.addWidget(self.btn_copy)

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

    def select_logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Logo", "", "Image Files (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self.logo_path = path
            self.label_logo_info.setText(f"Selected: {os.path.basename(path)}")

    def generate_qr(self):
        data = self.text_input.toPlainText().strip()
        if not data: return

        qr = qrcode.QRCode(version=1, box_size=10, border=4, error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.add_data(data)
        qr.make(fit=True)

        qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGBA')
        
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                logo = Image.open(self.logo_path).convert("RGBA")
                qr_width, qr_height = qr_img.size
                logo_max_size = int(qr_width * 0.22) 
                logo.thumbnail((logo_max_size, logo_max_size), Image.LANCZOS)
                
                logo_w, logo_h = logo.size
                padding = 6 
                bg_w, bg_h = logo_w + padding, logo_h + padding
                white_bg = Image.new("RGBA", (bg_w, bg_h), "white")
                
                bg_pos = ((qr_width - bg_w) // 2, (qr_height - bg_h) // 2)
                logo_pos = ((qr_width - logo_w) // 2, (qr_height - logo_h) // 2)
                
                qr_img.paste(white_bg, bg_pos)
                qr_img.paste(logo, logo_pos, mask=logo)
            except Exception as e:
                QMessageBox.warning(self, "Logo Error", str(e))

        self.current_qr_img = qr_img
        temp_path = "temp_qr_preview.png"
        self.current_qr_img.save(temp_path)
        self.qr_preview.setPixmap(QPixmap(temp_path).scaled(220, 220, Qt.KeepAspectRatio))
        self.btn_save.setEnabled(True)
        if os.path.exists(temp_path): os.remove(temp_path)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.decode_qr_image(files[0])

    def save_qr(self):
        if not self.current_qr_img: return
        options = QFileDialog.Options()
        options |= QFileDialog.DontConfirmOverwrite 
        file_path, _ = QFileDialog.getSaveFileName(self, "Save", "qrcode.png", "PNG Files (*.png)", options=options)
        if not file_path: return

        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        final_path = os.path.join(directory, filename)
        counter = 1
        while os.path.exists(final_path):
            final_path = os.path.join(directory, f"{name}_{counter}{ext}")
            counter += 1

        self.current_qr_img.save(final_path)
        QMessageBox.information(self, "Success", f"Saved: {os.path.basename(final_path)}")

    def open_qr(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path: self.decode_qr_image(path)

    def decode_qr_image(self, path):
        try:
            img = Image.open(path)
            decoded_objects = decode(img)
            if decoded_objects:
                result = decoded_objects[0].data.decode('utf-8')
                self.text_output.setText(result)
                self.label_drop.setText(f"Read: {os.path.basename(path)}")
            else:
                self.text_output.setText("No QR Code found!")
                self.label_drop.setText("QR Not Found")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def copy_output(self):
        QApplication.clipboard().setText(self.text_output.toPlainText())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = QRTool()
    win.show()
    sys.exit(app.exec_())
