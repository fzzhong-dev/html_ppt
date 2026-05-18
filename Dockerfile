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