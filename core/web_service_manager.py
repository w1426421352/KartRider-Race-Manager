# 文件名: core/web_service_manager.py

import uvicorn
from PyQt6.QtCore import QThread, pyqtSignal
import queue

# 导入web服务器的app实例和指令队列
from web.server import app, command_queue


class WebServerThread(QThread):
    """运行Uvicorn服务器的后台线程"""

    def run(self):
        # Uvicorn需要以这种方式在非主线程中运行
        config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        server = uvicorn.Server(config)
        server.run()


class WebServiceManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(WebServiceManager, cls).__new__(cls)
            cls._instance.thread = None
            cls._instance.command_queue = command_queue
        return cls._instance

    def start_server(self):
        """启动Web服务"""
        if self.thread is None or not self.thread.isRunning():
            self.thread = WebServerThread()
            self.thread.start()
            print("Web服务已在后台启动，地址 http://0.0.0.0:8000")
            return True
        print("Web服务已在运行中。")
        return False

    def stop_server(self):
        """停止Web服务 (注意: uvicorn的程序化停止比较复杂，这里简化为终止线程)"""
        if self.thread and self.thread.isRunning():
            self.thread.terminate()  # 简单粗暴的停止方式
            self.thread.wait()
            self.thread = None
            print("Web服务已停止。")

    def send_command(self, command: dict):
        """
        向Web服务发送指令的统一接口。
        :param command: 一个包含指令类型和数据的字典
        """
        self.command_queue.put(command)
        print(f"已发送指令到Web服务: {command}")