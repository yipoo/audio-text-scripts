# 音频文本处理平台 API 文档

## API 概述

音频文本处理平台提供了一系列RESTful API，用于音频文件上传、任务管理、转写结果获取、标签生成和脚本生成等功能。所有API均返回JSON格式的响应，除非特别说明。

**基础URL**: `http://localhost:8000`

## 认证

当前版本API不需要认证。未来版本可能会添加认证机制。

## 错误处理

API使用标准HTTP状态码表示请求结果：

- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

错误响应格式：

```json
{
  "detail": "错误描述信息"
}
```

## API 端点

### 1. 文件上传

#### 上传音频文件

```
POST /api/upload
```

**描述**：上传音频文件并开始处理流程（转写、标签提取、脚本生成）

**请求**：
- Content-Type: `multipart/form-data`
- Body:
  - `file`: 音频文件 (支持格式: .wav, .mp3, .m4a)

**响应**：
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "文件已上传，开始处理",
  "filename": "example.mp3"
}
```

**状态码**：
- `200 OK`: 上传成功
- `400 Bad Request`: 文件格式不支持或参数错误
- `500 Internal Server Error`: 服务器处理错误

### 2. 任务管理

#### 获取所有任务

```
GET /api/jobs
```

**描述**：获取所有任务的列表及其状态

**响应**：
```json
[
  {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "filename": "example1.mp3",
    "created_at": "2025-03-21T10:00:00",
    "updated_at": "2025-03-21T10:05:00",
    "message": "处理完成",
    "has_transcript": true,
    "has_tags": true,
    "has_scripts": true
  },
  {
    "job_id": "550e8400-e29b-41d4-a716-446655440001",
    "status": "processing",
    "filename": "example2.mp3",
    "created_at": "2025-03-21T10:10:00",
    "updated_at": "2025-03-21T10:10:00",
    "message": "正在转写音频",
    "has_transcript": false,
    "has_tags": false,
    "has_scripts": false
  }
]
```

**状态码**：
- `200 OK`: 请求成功
- `500 Internal Server Error`: 服务器处理错误

#### 获取特定任务

```
GET /api/jobs/{job_id}
```

**描述**：获取特定任务的详细信息

**参数**：
- `job_id`: 任务ID

**响应**：
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "filename": "example.mp3",
  "created_at": "2025-03-21T10:00:00",
  "updated_at": "2025-03-21T10:05:00",
  "message": "处理完成",
  "has_transcript": true,
  "has_tags": true,
  "has_scripts": true
}
```

**状态码**：
- `200 OK`: 请求成功
- `404 Not Found`: 任务不存在
- `500 Internal Server Error`: 服务器处理错误

#### 重试任务

```
POST /api/jobs/{job_id}/retry
```

**描述**：重新处理失败的任务，或为已有转写结果的任务重新生成标签和脚本

**参数**：
- `job_id`: 任务ID

**响应**：
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "任务已重新开始处理"
}
```

**状态码**：
- `200 OK`: 请求成功
- `404 Not Found`: 任务不存在
- `500 Internal Server Error`: 服务器处理错误

### 3. 转写结果

#### 获取转写结果

```
GET /api/jobs/{job_id}/transcript
```

**描述**：获取特定任务的音频转写结果

**参数**：
- `job_id`: 任务ID

**响应**：
```
这是转写的文本内容...
```

**状态码**：
- `200 OK`: 请求成功
- `404 Not Found`: 任务不存在或转写结果不存在
- `500 Internal Server Error`: 服务器处理错误

### 4. 标签管理

#### 获取标签

```
GET /api/jobs/{job_id}/tags
```

**描述**：获取特定任务的标签

**参数**：
- `job_id`: 任务ID

**响应**：
```json
["标签1", "标签2", "标签3", "标签4", "标签5"]
```

**状态码**：
- `200 OK`: 请求成功
- `404 Not Found`: 任务不存在或标签不存在
- `500 Internal Server Error`: 服务器处理错误

#### 生成标签

```
POST /api/jobs/{job_id}/generate-tags
```

**描述**：为特定任务生成标签

**参数**：
- `job_id`: 任务ID

**请求体**：
```json
{
  "num_tags": 10
}
```
注：`num_tags`参数可选，默认为10

**响应**：
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "正在生成标签"
}
```

**状态码**：
- `200 OK`: 请求成功
- `404 Not Found`: 任务不存在或转写结果不存在
- `400 Bad Request`: 参数错误
- `500 Internal Server Error`: 服务器处理错误

### 5. 脚本管理

#### 获取脚本

```
GET /api/jobs/{job_id}/scripts
```

**描述**：获取特定任务的脚本

**参数**：
- `job_id`: 任务ID

**响应**：
```json
{
  "original_text": "原始转写文本...",
  "scripts": [
    "脚本1内容...",
    "脚本2内容...",
    "脚本3内容...",
    "脚本4内容...",
    "脚本5内容..."
  ]
}
```

**状态码**：
- `200 OK`: 请求成功
- `404 Not Found`: 任务不存在或脚本不存在
- `500 Internal Server Error`: 服务器处理错误

#### 生成脚本

```
POST /api/jobs/{job_id}/generate-scripts
```

**描述**：为特定任务生成脚本

**参数**：
- `job_id`: 任务ID
- `num_scripts`: 生成脚本数量（可选，默认为5）
- `custom_prompt`: 自定义提示词（可选）
- `overwrite`: 是否覆盖现有脚本（可选，默认为false）

**请求体**：
```json
{
  "num_scripts": 5,
  "custom_prompt": "自定义提示词",
  "overwrite": true
}
```

**响应**：
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "5f270fbf-4d7c-4dfd-8187-3c253719f687",
  "status": "processing",
  "message": "正在生成脚本"
}
```

**状态码**：
- `200 OK`: 请求成功
- `404 Not Found`: 任务不存在或转写结果不存在
- `400 Bad Request`: 参数错误
- `500 Internal Server Error`: 服务器处理错误

### 6. 系统状态

#### 获取API服务状态

```
GET /api/status
```

**描述**：获取API服务的状态信息，包括阿里云NLS和DashScope服务的连接状态

**响应**：
```json
{
  "nlsApi": {
    "status": "online",
    "message": "连接正常"
  },
  "dashscopeApi": {
    "status": "online",
    "message": "连接正常"
  },
  "lastCheck": "2025-03-21T19:36:16.158185",
  "logs": [
    "日志内容..."
  ]
}
```

**状态码**：
- `200 OK`: 请求成功
- `500 Internal Server Error`: 服务器处理错误

#### 获取系统资源状态

```
GET /api/system/status
```

**描述**：获取系统资源状态，包括后台任务线程池状态和最近的任务信息

**响应**：
```json
{
  "active_tasks": 1,
  "total_tasks": 10,
  "thread_pool": {
    "max_workers": 4,
    "active_threads": 1,
    "tasks_completed": 5
  },
  "recent_tasks": [
    {
      "id": "5f270fbf-4d7c-4dfd-8187-3c253719f687",
      "name": "generate_scripts_for_job_sync",
      "status": "running",
      "start_time": "2025-03-21T21:17:39.732357",
      "end_time": null,
      "args": "('job_id', 2, None, True)",
      "kwargs": "{}",
      "result": null,
      "error": null
    }
  ]
}
```

**状态码**：
- `200 OK`: 请求成功
- `500 Internal Server Error`: 服务器处理错误

#### 获取所有后台任务

```
GET /api/system/tasks
```

**描述**：获取所有后台任务的状态信息

**响应**：
```json
{
  "tasks": [
    {
      "id": "5f270fbf-4d7c-4dfd-8187-3c253719f687",
      "name": "generate_scripts_for_job_sync",
      "status": "running",
      "start_time": "2025-03-21T21:17:39.732357",
      "end_time": null,
      "args": "('job_id', 2, None, True)",
      "kwargs": "{}",
      "result": null,
      "error": null
    }
  ]
}
```

**状态码**：
- `200 OK`: 请求成功
- `500 Internal Server Error`: 服务器处理错误

#### 获取特定后台任务状态

```
GET /api/system/tasks/{task_id}
```

**描述**：获取特定后台任务的状态信息

**参数**：
- `task_id`: 任务ID

**响应**：
```json
{
  "id": "5f270fbf-4d7c-4dfd-8187-3c253719f687",
  "name": "generate_scripts_for_job_sync",
  "status": "running",
  "start_time": "2025-03-21T21:17:39.732357",
  "end_time": null,
  "args": "('job_id', 2, None, True)",
  "kwargs": "{}",
  "result": null,
  "error": null
}
```

**状态码**：
- `200 OK`: 请求成功
- `404 Not Found`: 任务不存在
- `500 Internal Server Error`: 服务器处理错误

## 数据模型

### 任务状态

任务状态可以是以下值之一：

- `pending`: 任务已创建但尚未开始处理
- `processing`: 任务正在处理中
- `completed`: 任务已成功完成
- `error`: 任务处理过程中出错

### 任务信息

任务信息包含以下字段：

- `job_id`: 任务ID，UUID格式
- `status`: 任务状态
- `filename`: 原始文件名
- `created_at`: 任务创建时间，ISO 8601格式
- `updated_at`: 任务最后更新时间，ISO 8601格式
- `message`: 任务状态描述信息
- `has_transcript`: 是否有转写结果
- `has_tags`: 是否有标签
- `has_scripts`: 是否有脚本

## 使用示例

### 上传音频文件

```javascript
// 使用fetch API上传文件
const fileInput = document.querySelector('input[type="file"]');
const formData = new FormData();
formData.append('file', fileInput.files[0]);

fetch('http://localhost:8000/api/upload', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('上传成功:', data);
  // 保存job_id用于后续操作
  const jobId = data.job_id;
})
.catch(error => {
  console.error('上传失败:', error);
});
```

### 获取任务列表

```javascript
fetch('http://localhost:8000/api/jobs')
.then(response => response.json())
.then(jobs => {
  console.log('任务列表:', jobs);
  // 处理任务列表
  jobs.forEach(job => {
    console.log(`任务ID: ${job.job_id}, 状态: ${job.status}`);
  });
})
.catch(error => {
  console.error('获取任务列表失败:', error);
});
```

### 获取转写结果

```javascript
const jobId = '550e8400-e29b-41d4-a716-446655440000';

fetch(`http://localhost:8000/api/jobs/${jobId}/transcript`)
.then(response => response.text())
.then(transcript => {
  console.log('转写结果:', transcript);
  // 显示转写结果
})
.catch(error => {
  console.error('获取转写结果失败:', error);
});
```

### 生成脚本

```javascript
const jobId = '550e8400-e29b-41d4-a716-446655440000';

fetch(`http://localhost:8000/api/jobs/${jobId}/generate-scripts`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    num_scripts: 5,
    custom_prompt: "自定义提示词",
    overwrite: true
  })
})
.then(response => response.json())
.then(data => {
  console.log('脚本生成请求已提交:', data);
  // 可以定期检查任务状态，等待脚本生成完成
})
.catch(error => {
  console.error('生成脚本请求失败:', error);
});
```

### 重试失败任务

```javascript
const jobId = '550e8400-e29b-41d4-a716-446655440000';

fetch(`http://localhost:8000/api/jobs/${jobId}/retry`, {
  method: 'POST'
})
.then(response => response.json())
.then(data => {
  console.log('任务重试请求已提交:', data);
  // 可以定期检查任务状态
})
.catch(error => {
  console.error('重试任务请求失败:', error);
});
```

## 注意事项

1. **长时间运行的任务**：
   - 音频转写、标签生成和脚本生成可能需要较长时间
   - 这些操作是异步执行的，API会立即返回，但实际处理可能仍在进行中
   - 客户端应定期检查任务状态

2. **文件大小限制**：
   - 默认最大文件大小为100MB
   - 超过此限制的文件将被拒绝

3. **支持的音频格式**：
   - 当前支持WAV、MP3和M4A格式
   - 其他格式将返回400错误

4. **错误处理**：
   - 客户端应妥善处理API返回的错误
   - 对于500错误，可以考虑重试请求

5. **并发限制**：
   - 当前版本没有实现并发限制
   - 未来版本可能会添加速率限制

## 更新日志

### v1.0.0 (2025-03-21)
- 初始API版本发布
- 支持基本的音频上传、转写、标签和脚本生成功能

---

© 2025 音频文本处理平台 版权所有
