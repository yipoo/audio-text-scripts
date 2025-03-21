# 短视频升级营销项目

## 项目简介
该项目用于录制抖音直播语音，使用阿里云API进行语音转文字，按文字意思进行分段处理，为分段后的文字打标签，并交给阿里云大模型DeepSeek进行创作，要求创作的内容意义接近但文字不同。最新版本支持生成多份含义相似但表达不同的话术，大大提高了内容创作效率。

## 功能模块
1. 音频录制与处理
2. 语音转文字（阿里云API）
3. 文本分段处理
4. 文本标签生成
5. AI内容创作（阿里云DeepSeek）
6. 多份话术生成

## 快速开始

### 环境设置

本项目使用Python虚拟环境来避免依赖冲突。您可以使用以下两种方式设置环境：

#### 方式一：使用一键安装脚本（推荐）

```bash
# 给脚本添加执行权限
chmod +x setup_env.sh

# 运行安装脚本
./setup_env.sh
```

此脚本将自动创建虚拟环境、安装依赖、设置必要的目录结构。

#### 方式二：手动设置

1. 创建虚拟环境：
```bash
python3 -m venv venv
```

2. 激活虚拟环境：
```bash
# 在macOS/Linux上
source venv/bin/activate
# 或使用提供的脚本
./activate_env.sh

# 在Windows上
venv\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 使用完毕后，可以退出虚拟环境：
```bash
deactivate
```

## 环境配置
1. 配置阿里云API密钥：在`.env`文件中设置相关密钥

## 使用方法
1. 配置`.env`文件
2. 运行主程序：`python main.py`
3. 处理音频文件：`python main.py process-file --input recordings/your_audio.wav`
4. 生成多份话术：`python generate_multiple_scripts.py --input output/your_transcript/transcript.txt`

详细使用说明请参考 `docs/使用说明.md`

## 快速使用

### 单个文件处理

```bash
# 处理单个音频文件
python main.py process-file --input recordings/your_audio.wav --output-dir output/result

# 生成多份话术
python generate_multiple_scripts.py --input output/result/transcript.txt --num 5
```

### 批量处理

```bash
# 批量处理recordings目录下的所有音频文件（mp4和wav）
python process_all.py

# 批量处理并为每个文件生成5份话术
python process_all.py --num-scripts 5

# 批量处理并保留原始MP4文件
python process_all.py --keep-mp4

# 递归搜索子目录中的所有音频文件
python process_all.py --recursive
```

## 批量处理功能

`process_all.py` 脚本可以批量处理 recordings 目录中的音频文件，并生成多份话术。

### 主要功能

- 自动转换 MP4 文件为 WAV 格式
- 递归搜索子目录中的音频文件
- 保持输出目录结构与 recordings 目录结构一致
- 支持后台异步生成多份话术

### 使用方法

```bash
# 基本用法
python process_all.py

# 生成5份话术
python process_all.py --num-scripts 5

# 保留原始MP4文件
python process_all.py --keep-mp4

# 指定输出目录
python process_all.py --output-dir my_output

# 递归搜索子目录
python process_all.py --recursive

# 后台异步生成话术
python process_all.py --async-generation
```

### 命令行参数

```
--num-scripts, -n NUM   为每个文件生成的话术数量（默认：10）
--keep-mp4, -k          保留原始MP4文件（默认会删除）
--output-dir, -o DIR    指定输出目录（默认：output）
--recursive, -r         递归搜索子目录（默认只搜索根目录）
--async-generation, -a  异步生成多份话术（后台执行）
```

## 新增功能

### 1. 语音识别优化
使用阿里云的`NlsSpeechTranscriber`替代原来的`NlsSpeechRecognizer`，提高了识别的准确性和实时性。主要改进包括句子级别的回调函数、中间结果输出、优化的音频数据发送策略等。

### 2. 多份话术生成
新增了多份话术生成功能，可以基于同一段文本生成多个不同表达方式的话术版本，适用于营销文案的多版本测试、社交媒体内容的差异化发布、销售话术的多样化训练等场景。

### 3. 音频格式处理优化
改进了音频格式处理功能，现在支持更多格式的音频文件，并自动进行必要的转换，包括采样率、声道数和编码格式的调整。

## 目录结构
- `audio_processing/`: 音频录制与处理模块
- `text_processing/`: 文本处理与分段模块
- `ai_generation/`: AI内容创作模块
- `utils/`: 工具函数
- `main.py`: 主程序入口
- `.env`: 环境变量配置（API密钥等）

## 常用命令示例

```bash
# 录制音频
python main.py record --duration 300

# 处理已有音频文件
python main.py process-file --input recordings/test.wav

# 生成多份话术
python generate_multiple_scripts.py --input output/test_20250321_123017/transcript.txt --num 10

# 转换音频格式（使用ffmpeg）
ffmpeg -i input.mp3 -acodec pcm_s16le -ac 1 -ar 16000 recordings/output.wav
```

## 已知问题与解决方案

### 依赖问题

1. **pydub模块依赖问题**
   - 症状：导入pydub时出现`No module named 'pyaudioop'`错误
   - 解决方案：程序已做兼容处理，即使没有pydub也能正常运行基本功能，但音频处理功能会受限

2. **alibabacloud_nls20180628和alibabacloud_dashscope包不可用**
   - 症状：pip安装时找不到这些包
   - 解决方案：程序已做兼容处理，会使用HTTP请求或模拟响应替代SDK功能

3. **PyAudio安装问题**
   - 症状：在某些系统上安装PyAudio可能失败
   - 解决方案：程序支持使用sounddevice作为替代方案录制音频

### 环境变量配置

如果您没有阿里云API密钥，程序仍然可以在模拟模式下运行，但某些功能会受限：
- 语音识别将返回模拟结果
- AI内容创作将返回简单处理后的文本

要测试环境是否正确设置，可以运行：
```bash
python test_env.py
```

## 贡献指南

欢迎提交问题报告和功能请求。如果您想贡献代码，请遵循以下步骤：
1. Fork本仓库
2. 创建您的特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交您的更改 (`git commit -m 'Add some amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开一个Pull Request

## 许可证

本项目采用MIT许可证 - 详情请参见LICENSE文件
