# 音频文本处理平台

音频文本处理平台是一个集成了音频转文字、文本标签提取和脚本生成功能的一站式解决方案。该平台旨在帮助内容创作者快速将音频内容转换为文本，并通过AI技术自动生成适合短视频平台的多种脚本变体，大幅提高内容创作效率。

## 核心功能

- **音频转文字**：支持多种音频格式，提供高准确度的中文语音识别
- **标签提取**：从转写文本中自动提取关键词和主题标签
- **脚本生成**：基于转写文本和标签，生成多个不同风格的短视频脚本
- **任务管理**：查看所有处理任务的状态和进度，支持失败任务的重试

## 技术栈

- **前端**：Next.js 14、Ant Design 5.x、TypeScript
- **后端**：FastAPI (Python)、异步处理
- **AI服务**：阿里云NLS语音识别、阿里云DashScope内容生成

## 详细文档

请参阅 [docs](./docs) 目录下的详细文档：

- [项目概述](./docs/README.md)：完整的项目功能、技术栈和架构说明
- [系统设计文档](./docs/系统设计文档.md)：详细的系统设计、数据流、模块设计等
- [API文档](./docs/API文档.md)：完整的API接口说明和使用示例
- [用户手册](./docs/用户手册.md)：面向最终用户的使用指南

## 快速开始

### 前端开发

```bash
# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

访问 [http://localhost:3000](http://localhost:3000) 查看前端应用。

### 后端开发

```bash
# 进入后端目录
cd python-backend

# 安装依赖
pip install -r requirements.txt

# 启动API服务
sh run_api.sh
```

后端API服务将在 [http://localhost:8000](http://localhost:8000) 上运行。

## 部署

详细的部署说明请参阅 [项目概述文档](./docs/README.md#部署指南)。
