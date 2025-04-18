# 音频文本处理平台

## 项目概述

音频文本处理平台是一个集成了音频转文字、文本标签提取和脚本生成功能的一站式解决方案。该平台旨在帮助内容创作者快速将音频内容转换为文本，并通过AI技术自动生成适合短视频平台的多种脚本变体，大幅提高内容创作效率。

## 产品功能

### 核心功能

1. **音频转文字**
   - 支持多种音频格式（WAV、MP3、M4A）
   - 使用阿里云语音识别服务，提供高准确度的中文语音识别
   - 自动处理长音频文件

2. **标签提取**
   - 从转写文本中自动提取关键词和主题标签
   - 支持自定义标签数量
   - 标签可用于内容分类和检索

3. **脚本生成**
   - 基于转写文本和提取的标签，生成多个不同风格的短视频脚本
   - 支持自定义脚本数量
   - 脚本保留原始内容的核心信息，同时增加吸引力和互动性

4. **任务管理**
   - 查看所有处理任务的状态和进度
   - 支持失败任务的重试
   - 任务结果持久化存储

### 辅助功能

1. **服务状态监控**
   - 显示总任务数、完成任务数和完成率
   - 实时监控系统运行状态

2. **批量处理**
   - 支持队列处理多个音频文件
   - 后台异步处理，不阻塞用户界面

3. **结果导出**
   - 转写结果、标签和脚本可以查看和复制
   - 支持未来扩展导出为多种格式

## 技术栈

### 前端

- **框架**: Next.js 14（React框架）
- **UI组件库**: Ant Design 5.x
- **状态管理**: React Hooks (useState, useEffect)
- **HTTP客户端**: Axios
- **开发语言**: TypeScript
- **构建工具**: npm/webpack

### 后端

- **框架**: FastAPI (Python)
- **异步处理**: Python asyncio
- **API文档**: Swagger UI (通过FastAPI自动生成)
- **文件处理**: Python标准库 (os, shutil)
- **日志系统**: Python logging模块

### AI服务

- **语音识别**: 阿里云NLS语音识别服务
- **内容生成**: 阿里云DashScope (通义千问模型)
- **文本分析**: 自定义标签提取算法

### 部署

- **开发环境**: 本地开发服务器
- **生产环境**: 可部署到任何支持Node.js和Python的服务器
- **容器化**: 可使用Docker进行容器化部署（未实现）

## 系统架构

### 整体架构

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│   前端应用   │ <--> │  后端API服务 │ <--> │  AI服务集成  │
└─────────────┘      └─────────────┘      └─────────────┘
       │                    │                    │
       │                    │                    │
       ▼                    ▼                    ▼
┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  用户界面    │      │  文件存储    │      │ 外部AI服务   │
└─────────────┘      └─────────────┘      └─────────────┘
```

### 数据流程

```
┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐
│ 音频上传 │ --> │ 音频转写 │ --> │ 标签提取 │ --> │ 脚本生成 │
└─────────┘     └─────────┘     └─────────┘     └─────────┘
                      │               │               │
                      ▼               ▼               ▼
                 ┌─────────────────────────────────────┐
                 │              结果存储               │
                 └─────────────────────────────────────┘
                                  │
                                  ▼
                 ┌─────────────────────────────────────┐
                 │              前端展示               │
                 └─────────────────────────────────────┘
```

## 目录结构

```
audio-text-web/
├── docs/                    # 项目文档
├── public/                  # 静态资源
├── src/                     # 前端源代码
│   ├── app/                 # Next.js应用页面
│   │   ├── jobs/            # 任务管理页面
│   │   ├── page.tsx         # 首页
│   │   └── ...
│   ├── components/          # React组件
│   │   ├── layout/          # 布局组件
│   │   └── ...
│   ├── services/            # API服务
│   └── ...
├── python-backend/          # 后端源代码
│   ├── api/                 # FastAPI应用
│   │   ├── main.py          # 主应用入口
│   │   └── ...
│   ├── audio-text/          # 核心处理模块
│   │   ├── audio_processing/ # 音频处理模块
│   │   ├── text_processing/  # 文本处理模块
│   │   ├── ai_generation/   # AI生成模块
│   │   └── ...
│   ├── output/              # 输出文件目录
│   ├── uploads/             # 上传文件目录
│   └── ...
├── package.json             # 前端依赖配置
├── tsconfig.json            # TypeScript配置
└── ...
```

## API接口

### 主要接口

| 接口路径 | 方法 | 描述 |
|---------|------|------|
| `/api/upload` | POST | 上传音频文件并开始处理 |
| `/api/jobs` | GET | 获取所有任务列表 |
| `/api/jobs/{job_id}` | GET | 获取特定任务的详细信息 |
| `/api/jobs/{job_id}/transcript` | GET | 获取特定任务的转写结果 |
| `/api/jobs/{job_id}/tags` | GET | 获取特定任务的标签 |
| `/api/jobs/{job_id}/scripts` | GET | 获取特定任务的脚本 |
| `/api/jobs/{job_id}/generate-tags` | POST | 手动触发标签生成 |
| `/api/jobs/{job_id}/generate-scripts` | POST | 手动触发脚本生成 |
| `/api/jobs/{job_id}/retry` | POST | 重试失败的任务 |

## 使用流程

1. **上传音频文件**
   - 在首页拖拽或选择音频文件上传
   - 系统自动开始处理

2. **查看任务状态**
   - 在任务管理页面查看所有任务
   - 通过状态图标了解任务进度

3. **查看处理结果**
   - 任务完成后，可以查看转写结果、标签和脚本
   - 使用下拉菜单访问不同的结果类型

4. **手动生成内容**
   - 如果需要，可以手动触发标签或脚本的生成
   - 可以自定义生成的脚本数量

5. **重试失败任务**
   - 对于失败的任务，可以点击重试按钮
   - 系统会从合适的步骤重新开始处理

## 部署指南

### 前端部署

1. 安装依赖
   ```bash
   npm install
   ```

2. 开发环境运行
   ```bash
   npm run dev
   ```

3. 构建生产版本
   ```bash
   npm run build
   ```

4. 启动生产服务器
   ```bash
   npm start
   ```

### 后端部署

1. 安装Python依赖
   ```bash
   cd python-backend
   pip install -r requirements.txt
   ```

2. 配置环境变量
   - 创建 `audio-text/.env` 文件，设置以下变量：
     ```
     ALIYUN_NLS_APP_KEY=你的阿里云语音识别AppKey
     ALIYUN_DASHSCOPE_API_KEY=你的阿里云DashScope API Key
     ```

3. 启动后端服务
   ```bash
   cd python-backend
   sh run_api.sh
   ```

## 扩展与未来计划

1. **用户认证系统**
   - 添加用户注册和登录功能
   - 实现任务的用户隔离

2. **更多AI模型支持**
   - 集成更多语音识别服务提供商
   - 支持多语言转写和处理

3. **高级分析功能**
   - 情感分析
   - 主题聚类
   - 内容推荐

4. **批量处理优化**
   - 并行处理多个任务
   - 任务优先级队列

5. **移动端适配**
   - 响应式设计优化
   - 移动应用开发

## 常见问题

1. **为什么音频转写需要较长时间？**
   - 音频转写依赖于外部API服务，处理时间与音频长度和服务器负载有关。

2. **支持哪些音频格式？**
   - 目前支持WAV、MP3和M4A格式。

3. **如何处理转写不准确的情况？**
   - 可以通过重试功能重新处理，或者考虑提高音频质量。

4. **生成的脚本有什么特点？**
   - 脚本保留原始内容的核心信息，同时增加了吸引力和互动性，适合短视频平台使用。

5. **如何获取API密钥？**
   - 阿里云NLS和DashScope API密钥需要在阿里云官网注册并申请。

## 联系与支持

如有任何问题或建议，请通过以下方式联系我们：

- **项目仓库**: [GitHub链接]
- **问题反馈**: [Issues链接]
- **电子邮件**: [联系邮箱]

---

© 2025 音频文本处理平台 版权所有
