import sys
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import QPixmap

class FloatingImage(QWidget):
    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path
        self.drag_position = None
        self.original_pixmap = None
        self.current_scale = 1.0
        self.scale_step = 0.1
        self.initUI()

    def initUI(self):
        # 窗口设置：无边框、置顶、透明背景
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 加载原始图片
        self.original_pixmap = QPixmap(self.image_path)
        if self.original_pixmap.isNull():
            print(f"无法加载图片：{self.image_path}")
            sys.exit(1)

        # 创建标签显示图片
        self.label = QLabel(self)
        self.label.setAttribute(Qt.WA_TranslucentBackground)
        self.update_pixmap()  # 根据当前缩放比例更新显示

    def update_pixmap(self):
        """根据 current_scale 缩放图片并调整窗口大小"""
        if self.original_pixmap is None:
            return
        # 计算缩放后的尺寸（保持宽高比）
        new_width = int(self.original_pixmap.width() * self.current_scale)
        new_height = int(self.original_pixmap.height() * self.current_scale)
        scaled_pixmap = self.original_pixmap.scaled(new_width, new_height,
                                                    Qt.KeepAspectRatio,
                                                    Qt.SmoothTransformation)
        self.label.setPixmap(scaled_pixmap)
        # 调整标签和窗口大小以适应缩放后的图片
        self.label.resize(scaled_pixmap.width(), scaled_pixmap.height())
        self.resize(scaled_pixmap.width(), scaled_pixmap.height())

    def scale_image(self, delta):
        """缩放图片，delta为缩放增量（正数放大，负数缩小）"""
        new_scale = self.current_scale + delta
        # 限制缩放范围：0.1 ~ 5.0
        new_scale = max(0.1, min(5.0, new_scale))
        if new_scale != self.current_scale:
            self.current_scale = new_scale
            self.update_pixmap()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Escape:
            self.close()
        elif key == Qt.Key_Plus or key == Qt.Key_Equal:   # 放大（+ 或 =）
            self.scale_image(self.scale_step)
        elif key == Qt.Key_Minus:                         # 缩小（-）
            self.scale_image(-self.scale_step)
        else:
            super().keyPressEvent(event)

    def wheelEvent(self, event):
        """鼠标滚轮缩放（可选）"""
        delta = event.angleDelta().y()
        if delta > 0:
            self.scale_image(self.scale_step)   # 向上滚动放大
        else:
            self.scale_image(-self.scale_step)  # 向下滚动缩小

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FloatingImage("./pinkie.png")  # 请替换为实际图片路径
    window.show()
    sys.exit(app.exec_())