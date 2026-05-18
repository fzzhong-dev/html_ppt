# 简历项目描述（应届生版）

## 项目名称：AI PPT 生成平台

**技术栈：** Vue 3 + Pinia + FastAPI + python-pptx

**项目描述：**

用户输入主题，AI 自动生成 HTML 格式的 PPT，支持在线编辑和 AI 对话修改，可导出为 PPTX 文件。前后端分离，前端 Vue 3，后端 Python FastAPI。

**主要工作：**

- 使用 Vue 3 + Pinia 搭建前端，实现了幻灯片缩略图列表、可视化编辑、代码编辑和 AI 对话面板等功能
- 后端对接了多家 AI 模型（OpenAI、DeepSeek、智谱、通义千问、Claude），当某个模型不可用时会自动切换到下一个，保证服务稳定
- 实现了流式生成功能，用 SSE（Server-Sent Events）让幻灯片一页一页实时推送到前端，用户不用等全部生成完才能看
- 通过 Puppeteer 对每页 HTML 截图，再用 python-pptx 组装成标准的 PPTX 文件，实现了导出功能
- 实现了撤销重做、幻灯片增删复制、全屏放映等编辑器基础功能

**项目收获：** 熟悉了前后端分离开发流程，掌握了 Vue 3 组合式 API 和状态管理，学习了如何对接大语言模型 API 以及 SSE 流式通信
