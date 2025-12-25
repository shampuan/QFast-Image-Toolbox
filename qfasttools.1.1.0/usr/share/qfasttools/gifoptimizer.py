#!/usr/bin/env python3
import sys
import os
from PIL import Image, ImageSequence
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QMessageBox, 
                             QFrame, QSlider, QCheckBox, QGroupBox)
from PyQt5.QtGui import QColor, QPalette, QMovie, QIcon # QIcon eklendi
from PyQt5.QtCore import Qt, QTimer

# Debian/Pardus grafik uyumluluğu
os.environ['QT_QPA_PLATFORM'] = 'xcb'

class GifOptimizer(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.setAcceptDrops(True)
        self.input_path = None

    def initUI(self):
        self.setWindowTitle('QFast Ultimate GIF Optimizer')
        self.setFixedSize(950, 700)
        
        # İkon Çağırma Mantığı
        script_dir = os.path.dirname(os.path.abspath(__file__))
        # icons klasörü altındaki gifoptimizer.png dosyasına erişim
        icon_path = os.path.join(script_dir, "icons", "gifoptimizer.png") 
        
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        self.apply_theme_logic()

        main_layout = QHBoxLayout(self)

        # --- SOL PANEL ---
        left_panel = QVBoxLayout()
        self.label_preview = QLabel("Drag - Drop GIF Here")
        self.label_preview.setAlignment(Qt.AlignCenter)
        self.label_preview.setFrameShape(QFrame.StyledPanel)
        self.label_preview.setMinimumSize(500, 480)
        left_panel.addWidget(self.label_preview)

        self.info_box = QGroupBox("Original GIF Analysis")
        info_layout = QVBoxLayout()
        self.lbl_info_res = QLabel("Resolution: -")
        self.lbl_info_frames = QLabel("Total Frames: -")
        self.lbl_info_colors = QLabel("Color Count: -")
        self.lbl_info_size = QLabel("File Size: -")
        info_layout.addWidget(self.lbl_info_res)
        info_layout.addWidget(self.lbl_info_frames)
        info_layout.addWidget(self.lbl_info_colors)
        info_layout.addWidget(self.lbl_info_size)
        self.info_box.setLayout(info_layout)
        left_panel.addWidget(self.info_box)
        
        # --- SAĞ PANEL ---
        right_panel = QVBoxLayout()
        
        group_controls = QGroupBox("Optimization Settings")
        ctrl_layout = QVBoxLayout()

        ctrl_layout.addWidget(QLabel("Resize scale (%):"))
        self.slider_scale = self.create_slider(10, 100, 100, 10)
        self.lbl_scale = QLabel("100%")
        ctrl_layout.addWidget(self.slider_scale); ctrl_layout.addWidget(self.lbl_scale)

        ctrl_layout.addWidget(QLabel("Color count:"))
        self.slider_colors = self.create_slider(2, 256, 256, 25)
        self.lbl_colors = QLabel("256 colors")
        ctrl_layout.addWidget(self.slider_colors); ctrl_layout.addWidget(self.lbl_colors)

        ctrl_layout.addWidget(QLabel("Frame skip (0 = None):"))
        self.slider_skip = self.create_slider(1, 10, 1, 1)
        self.lbl_skip = QLabel("0")
        ctrl_layout.addWidget(self.slider_skip); ctrl_layout.addWidget(self.lbl_skip)

        ctrl_layout.addWidget(QLabel("Speed multiplier:"))
        self.slider_speed = self.create_slider(5, 30, 10, 5)
        self.lbl_speed = QLabel("1.0x")
        ctrl_layout.addWidget(self.slider_speed); ctrl_layout.addWidget(self.lbl_speed)

        self.check_gray = QCheckBox("Grayscale mode")
        ctrl_layout.addWidget(self.check_gray)

        group_controls.setLayout(ctrl_layout)
        right_panel.addWidget(group_controls)

        self.slider_scale.valueChanged.connect(lambda v: self.lbl_scale.setText(f"{v}%"))
        self.slider_colors.valueChanged.connect(lambda v: self.lbl_colors.setText(f"{v} colors"))
        self.slider_skip.valueChanged.connect(lambda v: self.lbl_skip.setText(f"{v-1}"))
        self.slider_speed.valueChanged.connect(lambda v: self.lbl_speed.setText(f"{v/10.0}x"))

        right_panel.addStretch()

        self.btn_optimize = QPushButton("Optimize and Save")
        self.btn_optimize.setFixedHeight(50)
        self.btn_optimize.setEnabled(False)
        self.btn_optimize.clicked.connect(self.optimize_gif)
        right_panel.addWidget(self.btn_optimize)

        main_layout.addLayout(left_panel, 60); main_layout.addLayout(right_panel, 40)

    def create_slider(self, min_v, max_v, curr_v, interval):
        s = QSlider(Qt.Horizontal)
        s.setRange(min_v, max_v)
        s.setValue(curr_v)
        s.setTickPosition(QSlider.TicksBelow)
        s.setTickInterval(interval)
        s.setStyleSheet("QSlider::tick-config { color: white; }")
        return s

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
        p.setColor(QPalette.Light, Qt.white)
        p.setColor(QPalette.Mid, Qt.white)
        self.setPalette(p)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): event.accept()

    def dropEvent(self, event):
        path = event.mimeData().urls()[0].toLocalFile()
        if path.lower().endswith('.gif'): self.load_gif(path)

    def load_gif(self, path):
        self.input_path = path
        try:
            with Image.open(path) as img:
                f_count = sum(1 for _ in ImageSequence.Iterator(img))
                img.seek(0)
                frame_p = img.convert("P")
                colors = frame_p.getcolors()
                color_count = len(colors) if colors else "256+"
                
                self.lbl_info_res.setText(f"Resolution: {img.width}x{img.height}")
                self.lbl_info_frames.setText(f"Total Frames: {f_count}")
                self.lbl_info_colors.setText(f"Color Count: {color_count}")
                self.lbl_info_size.setText(f"File Size: {os.path.getsize(path)/(1024*1024):.2f} MB")
        except: pass
        self.movie = QMovie(path)
        self.label_preview.setMovie(self.movie)
        self.movie.setScaledSize(self.label_preview.size().scaled(480, 480, Qt.KeepAspectRatio))
        self.movie.start()
        self.btn_optimize.setEnabled(True)

    def optimize_gif(self):
        if not self.input_path: return
        folder = os.path.dirname(self.input_path)
        base_name_orig = os.path.splitext(os.path.basename(self.input_path))[0]
        
        counter = 1
        output_path = os.path.join(folder, f"{base_name_orig}_optimized_{counter}.gif")
        while os.path.exists(output_path):
            counter += 1
            output_path = os.path.join(folder, f"{base_name_orig}_optimized_{counter}.gif")

        try:
            with Image.open(self.input_path) as img:
                scale = self.slider_scale.value() / 100.0
                num_colors = self.slider_colors.value()
                skip_step = self.slider_skip.value()
                speed_f = self.slider_speed.value() / 10.0

                frames = []; durations = []
                for i, frame in enumerate(ImageSequence.Iterator(img)):
                    if i % skip_step != 0: continue
                    d = frame.info.get('duration', 100)
                    durations.append(max(20, int((d * skip_step) / speed_f)))
                    if scale < 1.0:
                        frame = frame.resize((int(frame.width * scale), int(frame.height * scale)), Image.Resampling.LANCZOS)
                    if self.check_gray.isChecked(): frame = frame.convert("L")
                    frame = frame.convert("P", palette=Image.Palette.ADAPTIVE, colors=num_colors)
                    frames.append(frame)

                frames[0].save(output_path, save_all=True, append_images=frames[1:],
                    optimize=True, duration=durations, loop=img.info.get('loop', 0), disposal=2)
            
            self.btn_optimize.setText("DONE! Check Folder")
            QTimer.singleShot(3000, lambda: self.btn_optimize.setText("Optimize and Save"))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv); window = GifOptimizer(); window.show(); sys.exit(app.exec_())
