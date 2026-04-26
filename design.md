现在一共有9张图，给每个图片名一个名字，然后在去设计一下不同交互情况下显示的gif。
---
先去测试一下目前的程序直接换图能不能很好的适配
---
设计分为三种操作：
- 点击
- 默认状态



def mousePressEvent(self, event):
    if event.button() == Qt.LeftButton:
        self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
        self.press_pos = event.globalPos()

def mouseReleaseEvent(self, event):
    if event.button() == Qt.LeftButton:
        # 判断是不是“点击”（移动很小）
        if (event.globalPos() - self.press_pos).manhattanLength() < 5:
            self.change_media(1)

    self.drag_position = None