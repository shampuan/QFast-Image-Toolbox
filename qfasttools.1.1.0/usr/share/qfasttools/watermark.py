#!/usr/bin/env python3
import sys
import os
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QSlider, QRadioButton, 
                             QLineEdit, QComboBox, QGroupBox, QFrame, QButtonGroup, 
                             QListWidget, QListWidgetItem, QSpinBox, QCheckBox, 
                             QColorDialog, QMessageBox)
from PyQt5.QtGui import QPalette, QColor, QPixmap, QPainter, QFont, QPen, QFontDatabase, QIcon
from PyQt5.QtCore import Qt

class WatermarkTool(QWidget):
    def __init__(self):
        super().__init__()
        self.watermark_image_path = ""
        self.current_pixmap = None
        self.text_color = QColor(255, 255, 255)
        self.initUI()
        self.setAcceptDrops(True)

    def initUI(self):
        self.setWindowTitle('QFast - Watermark Studio')
        
        # Icon loading logic from 'icons' folder
        try:
            base_path = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(base_path, 'icons', 'watermark.png')
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception:
            pass

        self.resize(1000, 750)
        self.setMinimumSize(900, 650)
        self.apply_theme_logic()

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # --- LEFT PANEL: FILE LIST AND PREVIEW ---
        left_layout = QVBoxLayout()
        left_layout.setSpacing(5)

        self.file_list = QListWidget()
        self.file_list.setMaximumHeight(100)
        self.file_list.itemClicked.connect(self.load_selected_image)
        
        self.lbl_preview = QLabel("Drag and Drop Images Here")
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setFrameShape(QFrame.StyledPanel)
        self.lbl_preview.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333;")
        self.lbl_preview.setSizePolicy(self.lbl_preview.sizePolicy().Expanding, self.lbl_preview.sizePolicy().Expanding)
        
        left_layout.addWidget(QLabel("File List:"))
        left_layout.addWidget(self.file_list)
        left_layout.addWidget(self.lbl_preview)

        # --- RIGHT PANEL: TOOLS ---
        self.right_panel_widget = QWidget()
        self.right_panel_widget.setFixedWidth(280)
        right_panel = QVBoxLayout(self.right_panel_widget)
        right_panel.setContentsMargins(0, 0, 0, 0)
        right_panel.setSpacing(8)

        self.mode_group = QButtonGroup(self)

        # 1. Text Settings
        self.group_text = QGroupBox("Text Settings")
        text_lay = QVBoxLayout()
        self.radio_text = QRadioButton("Text Mode")
        self.radio_text.setChecked(True)
        self.mode_group.addButton(self.radio_text)
        
        self.input_text = QLineEdit()
        self.input_text.setPlaceholderText("Enter watermark text...")
        self.input_text.textChanged.connect(self.update_preview)
        
        style_lay = QHBoxLayout()
        self.check_bold = QCheckBox("Bold"); self.check_italic = QCheckBox("Italic"); self.check_under = QCheckBox("Underline")
        self.check_bold.setToolTip("Bold"); self.check_italic.setToolTip("Italic"); self.check_under.setToolTip("Underline")
        self.check_bold.stateChanged.connect(self.update_preview)
        self.check_italic.stateChanged.connect(self.update_preview)
        self.check_under.stateChanged.connect(self.update_preview)
        style_lay.addWidget(self.check_bold); style_lay.addWidget(self.check_italic); style_lay.addWidget(self.check_under)

        self.btn_color = QPushButton("Select Color")
        self.btn_color.clicked.connect(self.pick_color)
        
        self.combo_font = QComboBox()
        self.combo_font.addItems(QFontDatabase().families())
        self.combo_font.setCurrentText("Arial")
        self.combo_font.currentTextChanged.connect(self.update_preview)
        
        self.spin_font_size = QSpinBox()
        self.spin_font_size.setRange(10, 1000); self.spin_font_size.setValue(60)
        self.spin_font_size.valueChanged.connect(self.update_preview)
        
        text_lay.addWidget(self.radio_text); text_lay.addWidget(self.input_text); text_lay.addLayout(style_lay)
        text_lay.addWidget(self.btn_color); text_lay.addWidget(QLabel("Font Family:")); text_lay.addWidget(self.combo_font)
        text_lay.addWidget(QLabel("Font Size:")); text_lay.addWidget(self.spin_font_size)
        self.group_text.setLayout(text_lay)

        # 2. Image Settings
        self.group_image = QGroupBox("Image Settings")
        img_lay = QVBoxLayout()
        self.radio_image = QRadioButton("Image Mode")
        self.mode_group.addButton(self.radio_image)
        
        self.lbl_scale = QLabel("Logo Scale: %20")
        self.slider_scale = QSlider(Qt.Horizontal)
        self.slider_scale.setRange(1, 100); self.slider_scale.setValue(20)
        self.slider_scale.valueChanged.connect(self.update_preview)
        
        img_lay.addWidget(self.radio_image); img_lay.addWidget(self.lbl_scale); img_lay.addWidget(self.slider_scale)
        self.group_image.setLayout(img_lay)

        # 3. Common Settings
        self.group_common = QGroupBox("Position & Opacity")
        com_lay = QVBoxLayout()
        self.combo_pos = QComboBox()
        self.combo_pos.addItems(["Bottom Right", "Top Right", "Bottom Left", "Top Left", "Center"])
        self.combo_pos.currentIndexChanged.connect(self.update_preview)
        
        self.lbl_alpha = QLabel("Opacity: %70")
        self.slider_alpha = QSlider(Qt.Horizontal)
        self.slider_alpha.setRange(0, 100); self.slider_alpha.setValue(70)
        self.slider_alpha.valueChanged.connect(self.update_preview)
        
        com_lay.addWidget(QLabel("Position:")); com_lay.addWidget(self.combo_pos); com_lay.addWidget(self.lbl_alpha); com_lay.addWidget(self.slider_alpha)
        self.group_common.setLayout(com_lay)

        # 4. Watermark Drop Area
        self.drop_area_wm = QLabel(">>>  DROP LOGO HERE  <<<")
        self.drop_area_wm.setAlignment(Qt.AlignCenter)
        self.drop_area_wm.setMinimumHeight(60)
        self.drop_area_wm.setFrameShape(QFrame.Box)
        self.drop_area_wm.setStyleSheet("border: 1px dashed #777; color: white;")

        self.radio_text.toggled.connect(self.toggle_modes)
        self.radio_image.toggled.connect(self.update_preview)

        right_panel.addWidget(self.group_text)
        right_panel.addWidget(self.group_image)
        right_panel.addWidget(self.group_common)
        right_panel.addWidget(self.drop_area_wm)
        right_panel.addStretch()

        self.btn_doit = QPushButton("Do it!")
        self.btn_doit.setMinimumHeight(45)
        self.btn_doit.clicked.connect(self.process_all_files)
        right_panel.addWidget(self.btn_doit)

        main_layout.addLayout(left_layout, 1)
        main_layout.addWidget(self.right_panel_widget)
        self.toggle_modes()

    def apply_theme_logic(self):
        p = QPalette()
        p.setColor(QPalette.Window, QColor(40, 40, 40))
        p.setColor(QPalette.WindowText, Qt.white)
        p.setColor(QPalette.Base, QColor(30, 30, 30))
        p.setColor(QPalette.Text, Qt.white)
        p.setColor(QPalette.Button, QColor(60, 60, 60))
        p.setColor(QPalette.ButtonText, Qt.white)
        p.setColor(QPalette.Disabled, QPalette.WindowText, QColor(90, 90, 90))
        self.setPalette(p)

    def pick_color(self):
        color = QColorDialog.getColor(self.text_color, self, "Select Text Color")
        if color.isValid():
            self.text_color = color
            self.update_preview()

    def toggle_modes(self):
        is_text = self.radio_text.isChecked()
        self.input_text.setEnabled(is_text); self.combo_font.setEnabled(is_text)
        self.spin_font_size.setEnabled(is_text); self.check_bold.setEnabled(is_text)
        self.check_italic.setEnabled(is_text); self.check_under.setEnabled(is_text); self.btn_color.setEnabled(is_text)
        
        self.slider_scale.setEnabled(not is_text); self.lbl_scale.setEnabled(not is_text)
        self.update_preview()

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        pos = event.pos()
        
        logo_rect = self.drop_area_wm.geometry()
        logo_rect.moveTopLeft(self.right_panel_widget.mapTo(self, logo_rect.topLeft()))

        if logo_rect.contains(pos):
            if files[0].lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                self.watermark_image_path = files[0]
                self.radio_image.setChecked(True)
                self.drop_area_wm.setText(f"LOGO: {os.path.basename(files[0])}")
                self.update_preview()
        else:
            for f in files:
                if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    item = QListWidgetItem(os.path.basename(f))
                    item.setData(Qt.UserRole, f)
                    self.file_list.addItem(item)
            if self.file_list.count() > 0:
                self.file_list.setCurrentRow(self.file_list.count() - 1)
                self.load_selected_image(self.file_list.currentItem())

    def load_selected_image(self, item):
        path = item.data(Qt.UserRole)
        self.current_pixmap = QPixmap(path)
        self.update_preview()

    def process_all_files(self):
        count = self.file_list.count()
        if count == 0:
            QMessageBox.warning(self, "Error", "No files to process!")
            return

        success_count = 0
        for i in range(count):
            item = self.file_list.item(i)
            original_path = item.data(Qt.UserRole)
            
            pix = QPixmap(original_path)
            processed_pix = self.apply_watermark_logic(pix)
            
            if processed_pix:
                dir_name = os.path.dirname(original_path)
                base_name, ext = os.path.splitext(os.path.basename(original_path))
                
                counter = 1
                while True:
                    new_name = f"{base_name}.watermarked{counter}{ext}"
                    save_path = os.path.join(dir_name, new_name)
                    if not os.path.exists(save_path):
                        break
                    counter += 1
                
                if processed_pix.save(save_path):
                    success_count += 1

        QMessageBox.information(self, "Success", f"{success_count} files saved successfully.")

    def apply_watermark_logic(self, target_pixmap):
        if target_pixmap.isNull(): return None
        
        result_pixmap = target_pixmap.copy()
        painter = QPainter(result_pixmap)
        pos_type = self.combo_pos.currentText()
        alpha = self.slider_alpha.value() / 100.0
        margin = 40

        if self.radio_text.isChecked():
            text = self.input_text.text()
            if text:
                font = QFont(self.combo_font.currentText(), self.spin_font_size.value())
                font.setBold(self.check_bold.isChecked()); font.setItalic(self.check_italic.isChecked()); font.setUnderline(self.check_under.isChecked())
                painter.setFont(font)
                color = QColor(self.text_color.red(), self.text_color.green(), self.text_color.blue(), int(alpha * 255))
                painter.setPen(QPen(color))
                fm = painter.fontMetrics()
                
                # Pos mapping for international strings
                x, y = self.calculate_pos(result_pixmap.width(), result_pixmap.height(), fm.width(text), fm.height(), pos_type, margin)
                painter.drawText(x, y + fm.ascent(), text)
        else:
            if self.watermark_image_path:
                wm_pix = QPixmap(self.watermark_image_path)
                if not wm_pix.isNull():
                    scale = self.slider_scale.value() / 100.0
                    nw = int(result_pixmap.width() * scale)
                    wm_pix = wm_pix.scaledToWidth(nw, Qt.SmoothTransformation)
                    x, y = self.calculate_pos(result_pixmap.width(), result_pixmap.height(), wm_pix.width(), wm_pix.height(), pos_type, margin)
                    painter.setOpacity(alpha)
                    painter.drawPixmap(x, y, wm_pix)
        
        painter.end()
        return result_pixmap

    def update_preview(self):
        if self.current_pixmap is None: return
        self.lbl_alpha.setText(f"Opacity: %{self.slider_alpha.value()}")
        self.lbl_scale.setText(f"Logo Scale: %{self.slider_scale.value()}")
        
        preview_pix = self.apply_watermark_logic(self.current_pixmap)
        if preview_pix:
            scaled = preview_pix.scaled(self.lbl_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.lbl_preview.setPixmap(scaled)

    def calculate_pos(self, cw, ch, ow, oh, p, m):
        if p == "Bottom Right": return cw - ow - m, ch - oh - m
        if p == "Top Right": return cw - ow - m, m
        if p == "Bottom Left": return m, ch - oh - m
        if p == "Top Left": return m, m
        return (cw - ow) // 2, (ch - oh) // 2

    def resizeEvent(self, event):
        self.update_preview()
        super().resizeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = WatermarkTool(); ex.show(); sys.exit(app.exec_())