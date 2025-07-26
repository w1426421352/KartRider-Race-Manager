// main.js - 根据当前页面路径执行不同逻辑

// 登录页面逻辑
if (document.getElementById('loginForm')) {
    const form = document.getElementById('loginForm');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const username = form.username.value;
        const password = form.password.value;
        const errorMessage = document.getElementById('error-message');

        const response = await fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body: `username=${username}&password=${password}`
        });

        const result = await response.json();

        if (result.status === 'success') {
            // 登录成功，将token存入浏览器本地存储
            localStorage.setItem('authToken', result.token);
            // 跳转到仪表盘
            window.location.href = '/dashboard';
        } else {
            errorMessage.textContent = result.message || '登录失败';
        }
    });
}

// 仪表盘页面逻辑
if (document.getElementById('dashboard')) {
    const statusDiv = document.getElementById('status');
    const scoreboardDiv = document.getElementById('scoreboard');
    const token = localStorage.getItem('authToken');

    if (!token) {
        // 如果没有token，跳转回登录页
        window.location.href = '/';
    } else {
        // 使用 ws:// 或 wss:// (for https)
        const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${wsProtocol}//${window.location.host}/ws/${token}`;
        const socket = new WebSocket(wsUrl);

        socket.onopen = () => {
            statusDiv.textContent = "已连接到比赛服务器。";
            console.log("WebSocket connection established.");
        };

        socket.onmessage = (event) => {
            console.log("Message from server: ", event.data);
            const message = JSON.parse(event.data);

            // 根据消息类型更新UI
            if (message.type === 'score_update') {
                statusDiv.textContent = `第 ${message.round} 局分数已更新！`;
                // 简单地将分数数据显示为JSON字符串
                scoreboardDiv.innerHTML = `<pre>${JSON.stringify(message.scores, null, 2)}</pre>`;
            } else if (message.type === 'broadcast') {
                statusDiv.textContent = `通知: ${message.text}`;
            }
            // ...未来可以扩展更多消息类型
        };

        socket.onclose = () => {
            statusDiv.textContent = "与服务器的连接已断开。";
            console.log("WebSocket connection closed.");
        };

        socket.onerror = (error) => {
            statusDiv.textContent = "连接发生错误。";
            console.error("WebSocket error: ", error);
        };
    }
}