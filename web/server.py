# 文件名: web/server.py (V2 - 修正路径问题)

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles # <-- 导入 StaticFiles
from fastapi.templating import Jinja2Templates
from typing import List
import queue
import json
import os # <-- 新增导入

# --- 导入我们之前编写的核心服务 ---
from core.auth_manager import AuthManager

# --- 初始化 ---
app = FastAPI()

# --- 路径修正部分 ---
# 获取当前文件(server.py)所在的目录的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))
# 构建到 static 和 templates 文件夹的绝对路径
static_path = os.path.join(current_dir, "static")
templates_path = os.path.join(current_dir, "templates")

# 使用绝对路径来挂载静态文件目录和模板目录
app.mount("/static", StaticFiles(directory=static_path), name="static")
templates = Jinja2Templates(directory=templates_path)
# --- 路径修正结束 ---


# 这个队列是桌面程序与Web服务之间通信的桥梁
command_queue = queue.Queue()

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, username: str):
        await websocket.accept()
        self.active_connections[username] = websocket

    def disconnect(self, username: str):
        if username in self.active_connections:
            del self.active_connections[username]

    async def broadcast(self, message: dict):
        """向所有连接的客户端广播消息"""
        message_str = json.dumps(message)
        for connection in self.active_connections.values():
            await connection.send_text(message_str)

manager = ConnectionManager()
auth_manager = AuthManager()

# --- 后台任务：处理来自主程序的指令 ---
async def process_commands():
    """一个无限循环的后台任务，用于处理指令队列"""
    while True:
        try:
            command = command_queue.get_nowait()
            if command:
                await manager.broadcast(command)
        except queue.Empty:
            await asyncio.sleep(0.1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(process_commands())

# --- HTTP API 端点 ---

@app.get("/", response_class=HTMLResponse)
async def get_login_page(request: Request):
    """提供登录页面"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def handle_login(username: str = Form(...), password: str = Form(...)):
    """处理用户登录请求"""
    if auth_manager.verify_password(username, password):
        token = auth_manager.generate_session_token(username)
        return {"status": "success", "token": token}
    return {"status": "error", "message": "用户名或密码错误"}

@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """提供选手仪表盘页面"""
    return templates.TemplateResponse("dashboard.html", {"request": request})

# --- WebSocket 端点 ---

@app.websocket("/ws/{token}")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """处理选手的WebSocket连接"""
    username = auth_manager.verify_session_token(token)
    if not username:
        await websocket.close(code=1008)
        return

    await manager.connect(websocket, username)
    print(f"信息: 选手 '{username}' 已连接。")
    try:
        while True:
            data = await websocket.receive_text()
            print(f"收到来自 '{username}' 的消息: {data}")
    except WebSocketDisconnect:
        manager.disconnect(username)
        print(f"信息: 选手 '{username}' 已断开连接。")