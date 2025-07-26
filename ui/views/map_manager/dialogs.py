# 文件名: ui/views/map_manager/dialogs.py

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QDialogButtonBox
from PyQt6.QtCore import Qt


class AdvancedFilterDialog(QDialog):
    """
    用于高级筛选的对话框，允许用户选择多个“信息不完整”的条件。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("高级筛选")
        self.layout = QVBoxLayout(self)

        self.filters = {}
        self.filters['no_cn_name'] = QCheckBox("缺少简体中文译名")
        self.filters['no_tw_name'] = QCheckBox("缺少繁体中文译名")
        self.filters['no_kr_name'] = QCheckBox("缺少韩文译名")
        self.filters['no_difficulty'] = QCheckBox("缺少难度评级")

        for checkbox in self.filters.values():
            self.layout.addWidget(checkbox)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_selected_filters(self):
        """返回一个字典，表示哪些筛选条件被选中"""
        return {key: checkbox.isChecked() for key, checkbox in self.filters.items()}