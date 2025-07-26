# 文件名: ui/views/map_manager/map_card.py
import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QCheckBox
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QPoint
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor, QBrush, QPolygon
from core.language_service_placeholder import i18n
from .delegates import load_pixmap_safely


class MapCardWidget(QWidget):
    selection_changed = pyqtSignal(str, bool)

    def __init__(self, map_data, is_reverse, parent=None):
        # ... (代码不变) ...
        super().__init__(parent);
        self.map_data = map_data;
        self.is_reverse = is_reverse
        self.setFixedSize(222, 180);
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0);
        main_layout.setSpacing(0)
        self.image_label = QLabel();
        self.image_label.setFixedSize(222, 130)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet(
            "background-color: lightgray; border-top-left-radius: 5px; border-top-right-radius: 5px;")
        info_widget = QWidget();
        info_widget.setFixedHeight(50);
        info_widget.setStyleSheet(
            "background-color: #f0f0f0; border-bottom-left-radius: 5px; border-bottom-right-radius: 5px;")
        info_layout = QHBoxLayout(info_widget);
        info_layout.setContentsMargins(5, 0, 5, 0)
        self.checkbox = QCheckBox();
        self.checkbox.toggled.connect(self.on_toggled)
        self.name_label = QLabel("...");
        self.name_label.setWordWrap(True)
        info_layout.addWidget(self.checkbox);
        info_layout.addWidget(self.name_label, 1)
        main_layout.addWidget(self.image_label);
        main_layout.addWidget(info_widget)
        self.load_data()

    def on_toggled(self, checked):
        map_display_id = self.map_data['id'] + ("_rvs" if self.is_reverse else "")
        self.selection_changed.emit(map_display_id, checked)

    def set_checked(self, checked):
        self.checkbox.blockSignals(True);
        self.checkbox.setChecked(checked);
        self.checkbox.blockSignals(False)

    def load_data(self):
        # ... (代码不变) ...
        thumb_path = f"data/thumbnails/{self.map_data['id']}.png";
        pixmap = QPixmap()
        if os.path.exists(thumb_path): pixmap = load_pixmap_safely(thumb_path)
        final_pixmap = self.draw_overlays(pixmap);
        self.image_label.setPixmap(final_pixmap)
        display_name = i18n.get_map_name_with_fallback(self.map_data)
        if self.is_reverse: prefix = i18n.tr("map_prefixes.reverse"); display_name = f"{prefix} {display_name}"
        self.name_label.setText(display_name);
        self.setToolTip(f"{display_name}\nID: {self.map_data['id']}{'_rvs' if self.is_reverse else ''}")

    def draw_overlays(self, base_pixmap: QPixmap):
        # --- 核心修改: 调整难度渲染参数 ---
        canvas = QPixmap(222, 130)
        canvas.fill(Qt.GlobalColor.transparent)
        painter = QPainter(canvas)

        if not base_pixmap.isNull():
            painter.drawPixmap(0, 0, base_pixmap.scaled(222, 130, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                                        Qt.TransformationMode.SmoothTransformation))
        else:
            painter.fillRect(canvas.rect(), QColor("#e0e0e0"))

        difficulty = self.map_data.get('difficulty')
        if difficulty is not None:
            try:
                difficulty = int(difficulty)
                if 0 < difficulty <= 6:
                    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                    # 参数化，便于调整
                    bg_width = 55
                    bg_height = 28
                    skew = 15
                    bar_width = 4
                    bar_spacing = 6

                    bg_poly = QPolygon(
                        [QPoint(0, 0), QPoint(bg_width, 0), QPoint(bg_width - skew, bg_height), QPoint(0, bg_height)])
                    painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
                    painter.setPen(Qt.PenStyle.NoPen)
                    painter.drawPolygon(bg_poly)

                    for i in range(difficulty):
                        x_start = 7 + i * bar_spacing
                        bar_poly = QPolygon([
                            QPoint(x_start, 18), QPoint(x_start + bar_width, 18),
                            QPoint(x_start + bar_width - 2, 23), QPoint(x_start - 2, 23)
                        ])
                        painter.setBrush(QBrush(Qt.GlobalColor.red))
                        painter.drawPolygon(bar_poly)
            except (ValueError, TypeError):
                pass

        if self.is_reverse:
            reverse_icon = QPixmap("assets/icons/reverse_icon.png")
            if not reverse_icon.isNull():
                painter.drawPixmap(222 - 36 - 2, 130 - 36 - 2, 36, 36, reverse_icon)

        painter.end()
        return canvas