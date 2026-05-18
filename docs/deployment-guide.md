# HTML PPT 部署上线指南

## 1. 环境要求

| 依赖 | 最低版本 | 用途 |
|------|----------|------|
| Python | 3.11+ | 后端运行时 |
| Node.js | 18+ | 前端构建 + Puppeteer 截图 |
| npm | 9+ | 包管理 |
| Chromium/Chrome | 稳定版 | Puppeteer 无头截图（导出 PPTX） |
| Nginx | 1.20+ | 反向代理（推荐） |

---

## 2. 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python + Node.js
sudo apt install -y python3 python3-venv python3-pip nodejs npm

# 安装 Chromium（Puppeteer 截图用）
sudo apt install -y chromium-browser
# 或
sudo apt install -y google-chrome-stable

# 安装 Nginx
sudo apt install -y nginx

# 安装 PM2（进程守护）
sudo npm install -g pm2
```

---

## 3. 获取代码

```bash
# 方式一：Git
cd /opt
git clone <你的仓库地址> html-ppt
cd html-ppt

# 方式二：直接上传
# 将项目上传到 /opt/html-ppt
```

---

## 4. 后端配置

### 4.1 创建虚拟环境并安装依赖

```bash
cd /opt/html-ppt/backend

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 4.2 配置环境变量

```bash
cp .env .env.production
vim .env.production
```

修改以下关键配置：

```ini
# 生产环境关闭 debug
DEBUG=false

# LLM 提供商（至少配置一个）
DEFAULT_PROVIDER=deepseek
DEEPSEEK_API_KEY=你的DeepSeek密钥
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-v4-flash

# 图片搜索（至少配一个，推荐 Pexels）
PEXELS_API_KEY=你的Pexels密钥

# Puppeteer 截图（确保路径正确）
SCREENSHOTS_DIR=/opt/html-ppt/backend/screenshots
SCREENSHOT_SCRIPT=/opt/html-ppt/scripts/screenshot.js
```

> **重要：** `.env.production` 中不要保留测试密钥。确保 `.gitignore` 包含 `.env`。

### 4.3 安全检查

```bash
# 确认 .env 不在 Git 跟踪中
grep -q ".env" .gitignore || echo ".env" >> .gitignore
```

---

## 5. 前端构建

```bash
cd /opt/html-ppt/frontend

# 安装依赖
npm install

# 生产构建（输出到 dist/）
npm run build
```

构建产物在 `frontend/dist/` 目录，包含 `index.html` 和所有静态资源。

---

## 6. Puppeteer 截图模块

```bash
cd /opt/html-ppt/scripts

# 安装 Puppeteer
npm install

# 设置 Puppeteer 使用系统 Chromium（避免下载 Chromium）
export PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
# 或写入 .bashrc 永久生效
echo 'export PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser' >> ~/.bashrc
```

---

## 7. Nginx 配置

创建站点配置：

```bash
sudo vim /etc/nginx/sites-available/html-ppt
```

写入以下内容（替换域名和路径）：

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或 IP

    # 前端静态文件
    location / {
        root /opt/html-ppt/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;  # SPA 路由回退
    }

    # 后端 API 反向代理
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # SSE 流式接口需要关闭缓冲
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;  # LLM 生成可能较慢

        # WebSocket 支持（如有需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # 静态资源缓存
    location /assets/ {
        root /opt/html-ppt/frontend/dist;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Gzip 压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
    gzip_min_length 1000;

    # 上传限制（如有大图代理需求）
    client_max_body_size 20m;
}
```

启用站点并重载 Nginx：

```bash
sudo ln -s /etc/nginx/sites-available/html-ppt /etc/nginx/sites-enabled/
sudo nginx -t          # 检查配置语法
sudo systemctl reload nginx
```

---

## 8. 启动后端服务

### 方式一：PM2 进程守护（推荐）

```bash
cd /opt/html-ppt/backend

# 创建启动脚本
cat > start.sh << 'EOF'
#!/bin/bash
source /opt/html-ppt/backend/venv/bin/activate
export PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
cd /opt/html-ppt/backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
EOF
chmod +x start.sh

# 用 PM2 启动
pm2 start start.sh --name html-ppt-api
pm2 save
pm2 startup   # 生成开机自启命令，按提示执行
```

### 方式二：Systemd 服务

```bash
sudo vim /etc/systemd/system/html-ppt.service
```

```ini
[Unit]
Description=HTML PPT Backend API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/html-ppt/backend
Environment=PATH=/opt/html-ppt/backend/venv/bin
Environment=PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium-browser
ExecStart=/opt/html-ppt/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable html-ppt
sudo systemctl start html-ppt
sudo systemctl status html-ppt
```

---

## 9. HTTPS 配置（推荐）

```bash
# 安装 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 申请证书（替换域名）
sudo certbot --nginx -d your-domain.com

# 自动续期已内置，验证：
sudo certbot renew --dry-run
```

Certbot 会自动修改 Nginx 配置，将 HTTP 重定向到 HTTPS。

---

## 10. 防火墙

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
sudo ufw status
```

---

## 11. 验证部署

```bash
# 检查后端健康
curl http://localhost:8000/api/health
# 期望返回: {"status":"ok"}

# 检查前端
curl -I http://localhost/
# 期望返回 200

# 检查 API 代理
curl http://localhost/api/health
# 期望返回: {"status":"ok"}

# 检查 LLM 状态
curl http://localhost/api/llm/status

# 检查图片搜索
curl "http://localhost/api/images/search?q=test"
```

---

## 12. 目录结构总览

```
/opt/html-ppt/
├── backend/
│   ├── app/              # FastAPI 应用
│   ├── venv/             # Python 虚拟环境
│   ├── screenshots/      # 截图临时目录
│   ├── requirements.txt
│   └── .env              # 生产环境变量（不纳入 Git）
├── frontend/
│   ├── dist/             # 构建产物（Nginx 托管）
│   ├── src/
│   └── package.json
├── scripts/
│   ├── screenshot.js     # Puppeteer 截图脚本
│   └── node_modules/
└── nginx 配置在 /etc/nginx/sites-available/html-ppt
```

---

## 13. 常用运维命令

```bash
# 查看后端日志
pm2 logs html-ppt-api          # PM2 方式
sudo journalctl -u html-ppt -f # Systemd 方式

# 重启后端
pm2 restart html-ppt-api
sudo systemctl restart html-ppt

# 重新构建前端（代码更新后）
cd /opt/html-ppt/frontend && npm run build

# 更新代码并重启
cd /opt/html-ppt && git pull
cd frontend && npm install && npm run build
cd ../backend && source venv/bin/activate && pip install -r requirements.txt
pm2 restart html-ppt-api

# 清理截图临时文件
rm -f /opt/html-ppt/backend/screenshots/*.png
```

---

## 14. 注意事项

| 事项 | 说明 |
|------|------|
| **密钥安全** | `.env` 文件权限设为 `600`，不要提交到 Git |
| **API 限额** | DeepSeek / Pexels 均有请求频率限制，高并发需关注 |
| **Puppeteer 内存** | Chromium 无头模式约占 200-500MB 内存，2 worker 建议服务器 ≥2GB RAM |
| **截图目录权限** | `screenshots/` 目录需对运行用户可写 |
| **LLM 超时** | `nginx proxy_read_timeout` 设为 300s+，因为 LLM 生成可能耗时较长 |
| **SSE 缓冲** | Nginx 必须关闭 `proxy_buffering`，否则流式输出会被缓冲 |
| **CORS** | 生产环境建议将 `allow_origins=["*"]` 改为具体域名 |
