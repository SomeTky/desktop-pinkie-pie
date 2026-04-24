import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QMovie

class FloatingImage(QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.drag_position = None
        self.current_scale = 1.0
        self.scale_step = 0.1

        self.is_movie = False
        self.movie = None
        self.original_size = None
        self.original_pixmap = None

        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 修复高DPI模糊
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)

        self.label = QLabel(self)
        self.label.setAttribute(Qt.WA_TranslucentBackground)
        self.label.setAlignment(Qt.AlignCenter)
        # 修复透明背景&闪烁
        self.label.setAutoFillBackground(False)
        self.label.setScaledContents(False)

        self.load_media()

    def load_media(self):
        movie = QMovie(self.image_path)
        if movie.isValid() and movie.frameCount() > 1:
            self.is_movie = True
            self.movie = movie
            first_frame = movie.currentPixmap()
            if not first_frame.isNull():
                self.original_size = (first_frame.width(), first_frame.height())
                self.current_scale = 1.0
                self.update_geometry_for_movie()
                self.movie.frameChanged.connect(self.on_frame_changed)
                self.movie.start()
            else:
                self.movie.frameChanged.connect(self._on_first_frame_ready)
                self.movie.start()
        else:
            self.is_movie = False
            pixmap = QPixmap(self.image_path)
            if pixmap.isNull():
                print(f"无法加载图片：{self.image_path}")
                sys.exit(1)
            self.original_size = (pixmap.width(), pixmap.height())
            self.original_pixmap = pixmap
            self.update_pixmap()

    def _on_first_frame_ready(self, frame_number):
        if self.original_size is not None:
            return
        pix = self.movie.currentPixmap()
        if not pix.isNull():
            self.original_size = (pix.width(), pix.height())
            self.movie.frameChanged.disconnect(self._on_first_frame_ready)
            self.movie.frameChanged.connect(self.on_frame_changed)
            self.current_scale = 1.0
            self.update_geometry_for_movie()
            # 立即显示第一帧，避免空白
            self.on_frame_changed()

    # ====================== 修复：缺失的核心函数 ======================
    def update_geometry_for_movie(self):
        """同步GIF窗口大小 —— 你之前没写这个！"""
        if not self.original_size:
            return
        w = int(self.original_size[0] * self.current_scale)
        h = int(self.original_size[1] * self.current_scale)
        self.label.resize(w, h)
        self.resize(w, h)

    def update_pixmap(self):
        """静态图片缩放（无闪烁版）"""
        if self.is_movie or not self.original_pixmap:
            return
        new_w = int(self.original_size[0] * self.current_scale)
        new_h = int(self.original_size[1] * self.current_scale)
        scaled = self.original_pixmap.scaled(new_w, new_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(scaled)
        self.label.resize(new_w, new_h)
        self.resize(new_w, new_h)

    def force_update_movie_frame(self):
        """强制刷新当前帧（删除clear，彻底消除闪烁）"""
        if not self.is_movie or not self.movie or not self.original_size:
            return
        current = self.movie.currentPixmap()
        if current.isNull():
            return
        w = int(self.original_size[0] * self.current_scale)
        h = int(self.original_size[1] * self.current_scale)
        scaled = current.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(scaled)

    def on_frame_changed(self):
        """GIF帧更新（删除clear，彻底修复闪烁）"""
        if not self.is_movie or not self.original_size:
            return
        current = self.movie.currentPixmap()
        if current.isNull():
            return
        w = int(self.original_size[0] * self.current_scale)
        h = int(self.original_size[1] * self.current_scale)
        scaled = current.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.label.setPixmap(scaled)
        self.setMask(scaled.mask())

    def scale_image(self, delta):
        new_scale = self.current_scale + delta
        new_scale = max(0.2, min(5.0, new_scale))  # 提高最小尺寸，避免缩成点
        if abs(new_scale - self.current_scale) < 1e-6:
            return
        self.current_scale = new_scale
        if self.is_movie:
            self.update_geometry_for_movie()
            self.force_update_movie_frame()
        else:
            self.update_pixmap()

    # ====================== 事件函数不变 ======================
    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.close()
        elif key in (Qt.Key_Plus, Qt.Key_Equal):
            self.scale_image(self.scale_step)
        elif key == Qt.Key_Minus:
            self.scale_image(-self.scale_step)
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.scale_image(self.scale_step if delta > 0 else -self.scale_step)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_position = None

    def closeEvent(self, event):
        if self.movie:
            self.movie.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FloatingImage("./pinkie.gif")
    window.show()
    sys.exit(app.exec_())