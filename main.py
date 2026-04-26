import sys
import random
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QMovie


click_actions = [
    'DontTouchMe.gif',
    'HappyPig.gif',
    'mock.gif',
    'Running.gif',
    'WalkFastSad.gif'
]
static_actions = [
    'EatHandSad.gif',
    'HideLaugh.gif',
    'JumpHappy.gif',
    'JumpExcitied.gif',
]

class FloatingImage(QWidget):
    def __init__(self):
        super().__init__()
        self.image_path = random.choice(static_actions)
        self.drag_position = None
        self.current_scale = 1.0
        self.scale_step = 0.1

        self.press_pos = None
        self.moved = False
        self.original_size = None
        self.original_pixmap = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.change_media)  # 到时间就调用换图函数
        self.timer.start(10000)  # 10000ms = 10秒

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

    # ✅ 新增：统一缩放入口
    def apply_scale(self):
        """统一应用缩放（GIF + 静态图）"""
        if not self.original_size:
            return

        w = int(self.original_size[0] * self.current_scale)
        h = int(self.original_size[1] * self.current_scale)

        self.label.resize(w, h)
        self.resize(w, h)

        if self.is_movie:
            self.force_update_movie_frame()
        else:
            if self.original_pixmap:
                scaled = self.original_pixmap.scaled(
                    w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self.label.setPixmap(scaled)

    def change_media(self, choice=0):
        '''
        如果choice是0，从static_actions里面选动作，否则从click_action中选
        '''
        # 随机选一张（注意这里有个坑👇）
        if choice == 0:
            self.image_path = random.choice(static_actions)
        else:
            self.image_path = random.choice(click_actions)

        # 如果是GIF，先停掉旧的
        if self.movie:
            self.movie.stop()
            self.movie = None

        self.original_size = None
        self.original_pixmap = None

        # 重新加载
        self.load_media()

        # ⭐关键：延迟应用缩放（防止还没加载完成）
        QTimer.singleShot(0, self.apply_scale)

    def load_media(self):
        movie = QMovie(self.image_path)
        if movie.isValid() and movie.frameCount() > 1:
            self.is_movie = True
            self.movie = movie
            first_frame = movie.currentPixmap()
            if not first_frame.isNull():
                self.original_size = (first_frame.width(), first_frame.height())
                # 删除了原来的 self.current_scale = 1.0，保持当前缩放
                self.apply_scale()  # 统一缩放显示
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
            self.apply_scale()  # 统一缩放显示

    def _on_first_frame_ready(self, frame_number):
        if self.original_size is not None:
            return
        pix = self.movie.currentPixmap()
        if not pix.isNull():
            self.original_size = (pix.width(), pix.height())
            self.movie.frameChanged.disconnect(self._on_first_frame_ready)
            self.movie.frameChanged.connect(self.on_frame_changed)
            # 删除了原来的 self.current_scale = 1.0，保持当前缩放
            self.apply_scale()  # 统一缩放窗口和画面
            # 立即显示第一帧，避免空白
            self.on_frame_changed()

    def force_update_movie_frame(self):
        """强制刷新当前帧（用于缩放时立即更新GIF画面）"""
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
        """GIF帧更新"""
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
        self.apply_scale()  # 统一应用缩放

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
            self.press_pos = event.globalPos()
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.moved = False
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self.move(event.globalPos() - self.drag_position)

            # 判断是否发生“拖动”
            if (event.globalPos() - self.press_pos).manhattanLength() > 5:
                self.moved = True

            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            # 没有明显拖动 => 才算点击
            if not self.moved:
                self.change_media(1)

        self.drag_position = None
        self.press_pos = None
        self.moved = False

    # def closeEvent(self, event):
    #     if self.movie:
    #         self.movie.stop()
    #     event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FloatingImage()
    window.show()
    sys.exit(app.exec_())