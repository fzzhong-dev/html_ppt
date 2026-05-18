# HTML PPT — Hugging Face Spaces 免费部署指南

## 方案概述

将项目部署为 Hugging Face **Docker Space**（免费），架构为：

```
Hugging Face Docker Space（端口 7860）
├── Nginx            → 前端静态文件 + 反向代理 /api
├── FastAPI (uvicorn) → 后端 API（LLM 调用、PPT 生成）
└── Puppeteer        → Chromium 截图（导出 PPTX）
```

所有服务运行在一个 Docker 容器中，无需自己管理服务器。

---

## 1. 前置准备

| 需要的东西 | 说明 |
|-----------|------|
| Hugging Face 账号 | 免费注册 https://huggingface.co/join |
| Git | 本地安装 |
| API 密钥 | 至少需要一个 LLM 密钥（DeepSeek / 智谱）+ 可选 Pexels 图片搜索密钥 |

### HF Spaces 免费额度

| 资源 | 免费限制 |
|------|---------|
| CPU | 共享 2 vCPU |
| 内存 | ~16 GB |
| 磁盘 | 临时存储（重启清空），可挂载持久化存储 |
| 带宽 | 无硬性限制 |
| 端口 | 仅暴露 7860 |
| 休眠 | 无访问时自动休眠，访问时唤醒（约 30-60 秒冷启动） |

---

## 2. 创建 HF Space

1. 登录 https://huggingface.co
2. 点击右上角头像 → **New Space**
3. 填写：
   - **Space name**: `html-ppt`（或你喜欢的名字）
   - **License**: MIT
   - **SDK**: 选择 **Docker**
   - **Hardware**: **Free CPU**
4. 点击 **Create Space**
5. 记下你的 Space 地址：`https://huggingface.co/spaces/你的用户名/html-ppt`

---

## 3. 项目改造

### 3.1 在项目根目录创建 Dockerfile

```dockerfile
# ---- 多阶段构建 ----

# 阶段1：构建前端
FROM node:20-slim AS frontend-builder
WORKDIR /build/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# 阶段2：构建后端 + 运行时
FROM python:3.11-slim

# 安装 Nginx + Chromium（Puppeteer 用）
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    chromium \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 设置 Puppeteer 使用系统 Chromium
ENV PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium
ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true

# 创建非 root 用户（HF 要求 UID 1000）
RUN useradd -m -u 1000 appuser

WORKDIR /home/appuser/app

# 安装后端 Python 依赖
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# 安装 Puppeteer 截图脚本依赖
COPY scripts/package.json ./scripts/package.json
RUN cd scripts && npm install

# 复制后端代码
COPY --chown=appuser backend/ ./backend/

# 复制前端构建产物
COPY --from=frontend-builder /build/frontend/dist ./frontend/dist/

# 复制截图脚本
COPY --chown=appuser scripts/screenshot.js ./scripts/

# 复制模板（如果有）
COPY --chown=appuser templates/ ./templates/ 2>/dev/null || true

# 复制 Nginx 配置
COPY deploy/nginx.conf /etc/nginx/nginx.conf

# 复制启动脚本
COPY deploy/start.sh ./start.sh
RUN chmod +x ./start.sh

# 创建临时目录
RUN mkdir -p /home/appuser/app/backend/screenshots && \
    chown -R appuser:appuser /home/appuser/app

USER appuser
ENV HOME=/home/appuser

EXPOSE 7860

CMD ["./start.sh"]
```

### 3.2 创建启动脚本

创建文件 `deploy/start.sh`：

```bash
#!/bin/bash
set -e

# 启动 Nginx（后台）
nginx

# 启动 FastAPI（前台，容器主进程）
cd /home/appuser/app/backend
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1
```

### 3.3 创建 Nginx 配置

创建文件 `deploy/nginx.conf`：

```nginx
worker_processes 1;
error_log /dev/stderr warn;
pid /tmp/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    access_log /dev/stdout;

    server {
        listen 7860;
        server_name _;

        # 前端静态文件
        location / {
            root /home/appuser/app/frontend/dist;
            index index.html;
            try_files $uri $uri/ /index.html;
        }

        # 后端 API 反向代理
        location /api/ {
            proxy_pass http://127.0.0.1:8000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;

            # SSE 流式输出必须关闭缓冲
            proxy_buffering off;
            proxy_cache off;
            proxy_read_timeout 300s;

            proxy_http_version 1.1;
        }
    }
}
```

### 3.4 创建 README.md（HF Space 元数据）

在项目根目录创建/修改 `README.md`：

```markdown
---
title: HTML PPT Generator
emoji: 📊
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# HTML PPT Generator

输入主题，AI 自动生成专业演示文稿，支持实时编辑和导出 PPTX。
```

### 3.5 调整后端代码

确保 `backend/app/config.py` 中所有敏感配置项都有空字符串默认值（已有），HF 通过环境变量注入密钥，不再依赖 `.env` 文件。

添加 `.env` 文件忽略逻辑：如果 `settings` 读不到 `.env` 就用环境变量（pydantic-settings 默认行为，无需改动）。

### 3.6 创建 .dockerignore

```
.git
node_modules
__pycache__
*.pyc
.env
backend/venv
frontend/node_modules
backend/screenshots/*.png
```

### 3.7 创建 .gitignore（补充）

确保以下内容在 `.gitignore` 中：

```
.env
backend/venv/
backend/screenshots/*.png
frontend/node_modules/
frontend/dist/
__pycache__/
*.pyc
```

---

## 4. 配置密钥（Secrets）

1. 进入你的 Space 页面
2. 点击 **Settings** 标签
3. 找到 **Variables and secrets** 部分
4. 添加以下 **Secrets**（加密存储，不会泄露）：

| 名称 | 值 | 必填 |
|------|---|------|
| `DEFAULT_PROVIDER` | `deepseek` | 是 |
| `DEEPSEEK_API_KEY` | `sk-你的密钥` | 是（至少配一个 LLM） |
| `DEEPSEEK_BASE_URL` | `https://api.deepseek.com/v1` | 否（有默认值） |
| `DEEPSEEK_MODEL` | `deepseek-v4-flash` | 否 |
| `ZHIPU_API_KEY` | `你的智谱密钥` | 否（备选 LLM） |
| `PEXELS_API_KEY` | `你的Pexels密钥` | 否（图片搜索） |

> **注意**：不要把密钥写在代码或 `.env` 里提交到 Space，用 HF 的 Secrets 功能。

---

## 5. 推送部署

### 方式一：Git 推送（推荐）

```bash
# 克隆你的 HF Space 仓库
git clone https://huggingface.co/spaces/你的用户名/html-ppt
cd html-ppt

# 将你的项目文件复制进去
# （确保包含 Dockerfile、README.md、deploy/、backend/、frontend/、scripts/、templates/）

# 提交并推送
git add .
git commit -m "deploy: initial release"
git push
```

推送后 HF 会自动构建 Docker 镜像并启动服务，首次构建约 3-5 分钟。

### 方式二：直接从现有项目推送

```bash
cd /你的项目目录

# 添加 HF Space 为远程仓库
git remote add hf https://huggingface.co/spaces/你的用户名/html-ppt

# 推送
git push hf main
```

---

## 6. 验证部署

### 构建日志

在 Space 页面点击 **Logs** 标签查看构建和运行日志。

### 访问地址

```
https://你的用户名-html-ppt.hf.space
```

### 检查清单

- [ ] 页面能正常加载首页
- [ ] 输入主题能生成 PPT
- [ ] LLM 调用正常（不报 401/403）
- [ ] 图片搜索能用（如果配了 Pexels）
- [ ] 导出 PPTX 能下载（Puppeteer 截图正常）
- [ ] AI 助手修改功能正常

---

## 7. 更新部署

每次 `git push` 到 HF Space 仓库，HF 会自动重新构建并部署。

```bash
# 修改代码后
git add .
git commit -m "fix: update something"
git push hf main
```

---

## 8. 常见问题

### Q: 构建失败，提示磁盘空间不足

HF Docker Space 构建空间有限。优化方法：
- 确保 `.dockerignore` 排除了 `node_modules`、`venv`、`.git`
- 使用多阶段构建（Dockerfile 已使用），最终镜像不包含构建工具

### Q: Puppeteer 截图报错

- 确认 Dockerfile 安装了 `chromium` 和 `fonts-noto-cjk`（中文字体）
- 确认设置了 `PUPPETEER_EXECUTABLE_PATH=/usr/bin/chromium`
- 如果内存不足，限制 Chromium 启动参数：在 `screenshot.js` 的 `puppeteer.launch()` 中添加 `--disable-dev-shm-usage --no-sandbox`

### Q: 冷启动太慢

HF Space 休眠后首次访问需要 30-60 秒唤醒。缓解方法：
- 在 Space Settings 中勾选 **Pin this Space**（仅 Pro 用户可用）
- 免费方案只能接受冷启动延迟

### Q: LLM 响应超时

在 HF Space 中 Nginx 的 `proxy_read_timeout` 已设为 300s。如果仍然超时，可能是 LLM API 本身响应慢，考虑：
- 换用响应更快的模型（如 `deepseek-v4-flash`）
- 减少生成页数

### Q: Space 自动休眠

免费 Space 在无流量时会自动休眠。再次访问时会自动唤醒。如需保持在线：
- 升级 HF Pro（$9/月）可固定 Space
- 或用外部定时 ping（如 UptimeRobot）每 5 分钟访问一次

### Q: 密钥如何安全配置

**不要**把密钥写在代码里或 `.env` 文件中。使用 HF Space 的 **Secrets** 功能（Settings → Variables and secrets → New secret）。Secrets 会作为环境变量注入运行时，代码中的 `os.environ.get()` 或 pydantic-settings 会自动读取。

---

## 9. 目录结构（部署用）

```
html-ppt/
├── Dockerfile                  # Docker 构建文件
├── README.md                   # HF Space 元数据
├── .dockerignore               # Docker 构建排除
├── .gitignore                  # Git 排除
├── deploy/
│   ├── nginx.conf              # Nginx 配置
│   └── start.sh                # 容器启动脚本
├── backend/
│   ├── app/                    # FastAPI 应用
│   └── requirements.txt        # Python 依赖
├── frontend/
│   ├── src/                    # Vue 源码
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   ├── screenshot.js           # Puppeteer 截图
│   └── package.json
└── templates/                  # 模板文件（如有）
```

---

## 10. 完整操作步骤清单

```
1.  注册 Hugging Face 账号
2.  创建 Docker Space（SDK 选 Docker，硬件选 Free CPU）
3.  在项目根目录创建 Dockerfile
4.  创建 deploy/nginx.conf
5.  创建 deploy/start.sh
6.  修改项目根目录 README.md（添加 HF 元数据头）
7.  创建 .dockerignore
8.  确认 .gitignore 包含 .env
9.  在 Space Settings 中添加 Secrets（LLM 密钥、Pexels 密钥）
10. git clone 你的 HF Space 仓库到本地
11. 将项目文件复制/推送到 HF Space 仓库
12. git push → 等待自动构建
13. 查看 Logs 确认构建成功
14. 访问 https://你的用户名-html-ppt.hf.space 验证
```
