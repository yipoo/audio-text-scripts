// 任务类型
export interface Job {
  job_id: string;
  status: string;
  file?: string;
  timestamp: string;
  message?: string;
}

// 转写文本类型
export interface Transcript {
  transcript: string;
}

// 文本片段类型
export interface Segment {
  id: number;
  text: string;
  tags?: string[];
}

// 文本片段集合类型
export interface Segments {
  segments: Segment[];
}

// 生成内容类型
export interface GeneratedContent {
  id: number;
  original_text: string;
  generated_text: string;
  tags?: string[];
}

// 生成内容集合类型
export interface GeneratedContents {
  generated: GeneratedContent[];
}

// 脚本集合类型
export interface Scripts {
  scripts: Script[];
  original_text?: string;
}

// 单个脚本类型
export interface Script {
  id?: string;
  content: string;
  tags?: string[];
  source_job_id?: string;
  created_at?: string;
  favorite?: boolean;
}

// 脚本组类型
export interface ScriptGroup {
  original_text: string;
  job_id: string;
  scripts: Script[];
  tags?: string[];
  created_at?: string;
}

// 录音文件类型
export interface RecordingFile {
  name: string;
  path: string;
  size: number;
  created: number;
}

// 直播录制相关类型
export interface LiveStreamRequest {
  url: string;
  duration_minutes?: number;
  segment_duration?: number;
}

export interface TaskResponse {
  task_id: string;
  message: string;
}

export interface RecordingStatus {
  status: string;
  start_time?: string;
  duration?: number;
  file_path?: string;
  error?: string;
}
