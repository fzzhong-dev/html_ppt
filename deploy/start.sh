#!/bin/bash
set -e

mkdir -p /tmp/nginx/client_body /tmp/nginx/proxy /tmp/nginx/fastcgi /tmp/nginx/uwsgi /tmp/nginx/scgi

# 启动 Nginx（后台）
nginx -c /etc/nginx/nginx.conf

# 启动 FastAPI（前台，容器主进程）
cd /home/appuser/app/backend
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1