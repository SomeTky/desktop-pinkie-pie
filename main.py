import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt
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

        self.initUI()

    def initUI(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.label = QLabel(self)
        self.label.setAttribute(Qt.WA_TranslucentBackground)
        self.label.setAlignment(Qt.AlignCenter)

        self.load_media()

    def load_media(self):
        movie = QMovie(self.image_path)
        if movie.isValid() and movie.frameCount() > 1:
            # 是动画 GIF
            self.is_movie = True
            self.movie = movie
            first_frame = movie.currentPixmap()
            if not first_frame.isNull():
                # 第一帧有效，直接使用
                self.original_size = (first_frame.width(), first_frame.height())
                self.current_scale = 1.0
                self.update_geometry_for_movie()
                self.movie.frameChanged.connect(self.on_frame_changed)
                self.movie.start()
            else:
                # 第一帧暂无效，等待第一帧加载完成
                self.movie.frameChanged.connect(self._on_first_frame_ready)
                self.movie.start()
        else:
            # 静态图片
            self.is_movie = False
            pixmap = QPixmap(self.image_path)
            if pixmap.isNull():
                print(f"无法加载图片：{self.image_path}")
                sys.exit(1)
            self.original_size = (pixmap.width(), pixmap.height())
            self.original_pixmap = pixmap
            self.update_pixmap()

    def _on_first_frame_ready(self, frame_number):
        """等待第一帧有效时调用，仅执行一次"""
        if self.original_size is not None:
            return
        pix = self.movie.currentPixmap()
        if not pix.isNull():
            self.original_size = (pix.width(), pix.height())
            # 断开此一次性连接
            self.movie.frameChanged.disconnect(self._on_first_frame_ready)
            # 连接正常的帧更新信号
            self.movie.frameChanged.connect(self.on_frame_changed)
            # 设置初始缩放并更新窗口
            self.current_scale = 1.0
            self.update_geometry_for_movie()
            # 动画已经在 start() 中运行，无需再 start

    def update_pixmap(self):
        """静态图片缩放"""
        if self.is_movie or not hasattr(self, 'original_pixmap'):
            return
        new_width = int(self.original_size[0] * self.current_scale)
        new_height = int(self.original_size[1] * self.current_scale)
        scaled_pixmap = self.original_pixmap.scaled(new_width, new_height,
                                                    Qt.KeepAspectRatio,
                                                    Qt.SmoothTransformation)
        self.label.setPixmap(scaled_pixmap)
        self.label.resize(scaled_pixmap.width(), scaled_pixmap.height())
        self.resize(scaled_pixmap.width(), scaled_pixmap.height())

    def update_geometry_for_movie(self):
        """动画：根据 current_scale 调整窗口大小"""
        if not self.is_movie or self.original_size is None:
            return
        new_width = int(self.original_size[0] * self.current_scale)
        new_height = int(self.original_size[1] * self.current_scale)
        self.label.resize(new_width, new_height)
        self.resize(new_width, new_height)
        self.force_update_movie_frame()

    def force_update_movie_frame(self):
        """强制刷新当前帧到缩放后的尺寸"""
        if not self.is_movie or self.movie is None or self.original_size is None:
            return
        current_frame = self.movie.currentPixmap()
        if not current_frame.isNull():
            target_w = int(self.original_size[0] * self.current_scale)
            target_h = int(self.original_size[1] * self.current_scale)
            scaled_frame = current_frame.scaled(target_w, target_h,
                                                Qt.KeepAspectRatio,
                                                Qt.SmoothTransformation)
            self.label.setPixmap(scaled_frame)

    def on_frame_changed(self):
        """动画帧变化时缩放并显示"""
        if not self.is_movie or self.original_size is None:
            return
        current_frame = self.movie.currentPixmap()
        if not current_frame.isNull():
            target_w = int(self.original_size[0] * self.current_scale)
            target_h = int(self.original_size[1] * self.current_scale)
            scaled_frame = current_frame.scaled(target_w, target_h,
                                                Qt.KeepAspectRatio,
                                                Qt.SmoothTransformation)
            self.label.setPixmap(scaled_frame)

    def scale_image(self, delta):
        new_scale = self.current_scale + delta
        new_scale = max(0.1, min(5.0, new_scale))
        if abs(new_scale - self.current_scale) < 1e-6:
            return
        self.current_scale = new_scale
        if self.is_movie:
            self.update_geometry_for_movie()
        else:
            self.update_pixmap()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.close()
        elif key == Qt.Key_Plus or key == Qt.Key_Equal:
            self.scale_image(self.scale_step)
        elif key == Qt.Key_Minus:
            self.scale_image(-self.scale_step)
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.scale_image(self.scale_step)
        else:
            self.scale_image(-self.scale_step)

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
        if self.is_movie and self.movie is not None:
            self.movie.stop()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FloatingImage("./pinkie.gif")  # 支持 .gif 和静态图片
    window.show()
    sys.exit(app.exec_())