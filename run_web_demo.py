# 文件名: run_web_demo.py (V2 - 优化版)

import sys
import time
from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout
from core.web_service_manager import WebServiceManager
from core.auth_manager import AuthManager


class WebDemoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Web服务控制器")
        self.web_manager = WebServiceManager()
        self.auth_manager = AuthManager()

        # --- 优化部分：只在用户不存在时创建 ---
        if not self.auth_manager.db.get_account_by_username("player1"):
            print("信息: 测试账号 'player1' 不存在，正在创建...")
            self.auth_manager.create_account("player1", "12345", display_name="测试选手1")
        else:
            print("信息: 测试账号 'player1' 已存在。")
        # --- 优化结束 ---

        layout = QVBoxLayout(self)
        self.start_btn = QPushButton("启动Web服务")
        self.stop_btn = QPushButton("停止Web服务")
        self.test_broadcast_btn = QPushButton("发送测试广播")

        layout.addWidget(self.start_btn)
        layout.addWidget(self.stop_btn)
        layout.addWidget(self.test_broadcast_btn)

        self.start_btn.clicked.connect(self.web_manager.start_server)
        self.stop_btn.clicked.connect(self.web_manager.stop_server)
        self.test_broadcast_btn.clicked.connect(self.send_test_message)

    def send_test_message(self):
        test_command = {
            "type": "broadcast",
            "text": f"这是一条来自桌面的测试消息! (时间: {time.time()})"
        }
        self.web_manager.send_command(test_command)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = WebDemoApp()
    demo.show()
    sys.exit(app.exec())