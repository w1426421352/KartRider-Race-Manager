# 文件名: main.py (V1.3 - 修正导入路径问题)

import sys
import os
import ctypes

# --- 核心修正：在所有其他导入之前，将项目根目录添加到Python的搜索路径中 ---
# 这确保了无论从哪里运行脚本，程序都能找到'core'和'ui'这两个顶级包
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
# --- 修正结束 ---

from PyQt6.QtWidgets import QApplication, QMainWindow, QTabWidget, QStatusBar, QMessageBox
from PyQt6.QtGui import QAction

from ui.views.account_manager_widget import AccountManagerWidget
# 现在这个导入应该能正常工作了
from ui.views.map_manager.widget import MapManagerWidget

from core.db_manager import DBManager
from core.auth_manager import AuthManager
from core.map_manager import MapManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("跑跑卡丁车竞赛助手")
        self.setGeometry(100, 100, 1600, 900)
        self._setup_ui()
        self._create_menus()

    def _setup_ui(self):
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.account_manager = AccountManagerWidget()
        self.tabs.addTab(self.account_manager, "选手账号管理")

        self.map_manager = MapManagerWidget()
        self.tabs.addTab(self.map_manager, "地图库管理")

        self.map_manager.status_updated.connect(self.handle_status_update)

        self.setStatusBar(QStatusBar(self))

    def _create_menus(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件")
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def handle_status_update(self, message, level):
        print(f"[{level}] {message}")
        if level.upper() == 'ERROR':
            self.statusBar().showMessage(f"错误: {message}", 0)
            QMessageBox.critical(self, "发生错误", message)
        else:
            self.statusBar().showMessage(message, 5000)


def main():
    # 初始化核心服务 (确保数据库等已准备好)
    DBManager()
    AuthManager()
    MapManager()

    app = QApplication(sys.argv)
    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()