# 文件名: ui/views/map_manager/delegates.py

import os
from PyQt6.QtWidgets import QStyledItemDelegate, QStyle
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QPainter

try:
    from PIL import Image
    import io

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def load_pixmap_safely(path):
    """
    使用Pillow安全地加载图片，移除iCCP块以避免libpng警告。
    如果Pillow不可用或加载失败，则回退到Qt原生加载。
    """
    if not PIL_AVAILABLE or not os.path.exists(path):
        return QPixmap(path)  # Fallback to Qt if PIL is not there or file doesnt exist
    try:
        img = Image.open(path)
        # 如果图片包含ICC Profile，则移除它
        if "icc_profile" in img.info:
            del img.info["icc_profile"]

        # 将Pillow Image对象转换为Qt Pixmap，不保存到磁盘
        byte_array = io.BytesIO()
        img.save(byte_array, format='PNG')
        pixmap = QPixmap()
        pixmap.loadFromData(byte_array.getvalue())
        return pixmap
    except Exception:
        # 如果Pillow处理失败，回退到Qt原生加载
        return QPixmap(path)


class ThumbnailDelegate(QStyledItemDelegate):
    """
    一个自定义的委托，用于在表格单元格中绘制地图缩略图，
    并根据需要叠加“反向”图标。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.reverse_icon = QPixmap("assets/icons/reverse_icon.png")
        if self.reverse_icon.isNull():
            print("警告: 未找到反向地图图标 assets/icons/reverse_icon.png")

    def paint(self, painter: QPainter, option, index):
        # 从项数据中获取缩略图路径和是否为反向图的标志
        thumb_path = index.data(Qt.ItemDataRole.UserRole)
        is_reverse = index.data(Qt.ItemDataRole.UserRole + 1)

        has_thumbnail = thumb_path and os.path.exists(thumb_path)

        painter.save()

        # 绘制背景（选中时高亮，否则为浅灰色）
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        else:
            painter.fillRect(option.rect, Qt.GlobalColor.lightGray)

        # 如果缩略图存在，则将其绘制在单元格中央
        if has_thumbnail:
            pixmap = load_pixmap_safely(thumb_path)
            target_rect = option.rect
            pixmap_scaled = pixmap.scaled(target_rect.size(), Qt.AspectRatioMode.KeepAspectRatio,
                                          Qt.TransformationMode.SmoothTransformation)

            # 计算居中位置
            x = target_rect.x() + (target_rect.width() - pixmap_scaled.width()) / 2
            y = target_rect.y() + (target_rect.height() - pixmap_scaled.height()) / 2

            painter.drawPixmap(int(x), int(y), pixmap_scaled)

        # 只要是反向图，就尝试在右下角绘制叠加图标
        if is_reverse and not self.reverse_icon.isNull():
            icon_size = 36
            icon_x = option.rect.right() - icon_size - 2
            icon_y = option.rect.bottom() - icon_size - 2
            painter.drawPixmap(icon_x, icon_y,
                               self.reverse_icon.scaled(icon_size, icon_size, Qt.AspectRatioMode.KeepAspectRatio))

        painter.restore()