# API参考

<cite>
**Referenced Files in This Document**   
- [main.py](file://vibe_surf/backend/main.py)
- [task.py](file://vibe_surf/backend/api/task.py)
- [browser.py](file://vibe_surf/backend/api/browser.py)
- [files.py](file://vibe_surf/backend/api/files.py)
- [config.py](file://vibe_surf/backend/api/config.py)
- [activity.py](file://vibe_surf/backend/api/activity.py)
- [agent.py](file://vibe_surf/backend/api/agent.py)
- [schedule.py](file://vibe_surf/backend/api/schedule.py)
- [composio.py](file://vibe_surf/backend/api/composio.py)
- [voices.py](file://vibe_surf/backend/api/voices.py)
- [models.py](file://vibe_surf/backend/api/models.py)
</cite>

## 目录
1. [API概览](#api概览)
2. [认证机制](#认证机制)
3. [API端点](#api端点)
   1. [任务管理](#任务管理)
   2. [浏览器管理](#浏览器管理)
   3. [文件管理](#文件管理)
   4. [配置管理](#配置管理)
   5. [活动日志](#活动日志)
   6. [代理管理](#代理管理)
   7. [计划管理](#计划管理)
   8. [Composio集成](#composio集成)
   9. [语音管理](#语音管理)
4. [错误响应](#错误响应)
5. [WebSocket API](#websocket-api)
6. [客户端实现指南](#客户端实现指南)
7. [API版本控制](#api版本控制)

## API概览

VibeSurf API是一个基于FastAPI的RESTful API，为自动化代理系统提供后端服务。API设计为单任务执行模型，集成了Langflow功能，支持任务提交、执行控制、浏览器操作、文件管理、配置管理等多种功能。

API基础URL为`http://localhost:9335/api`，所有端点都通过此基础路径访问。API使用JSON格式进行请求和响应，并遵循标准的HTTP状态码。

**Section sources**
- [main.py](file://vibe_surf/backend/main.py#L1-L794)

## 认证机制

VibeSurf API目前主要依赖于会话ID和任务ID进行操作上下文管理，而不是传统的API密钥或JWT令牌认证。系统通过生成唯一的会话ID来跟踪用户会话和相关操作。

会话ID可以通过`/generate-session-id`端点生成：

```http
GET /generate-session-id
```

响应示例：
```json
{
  "session_id": "0191f3e0-5a3d-7e6f-9c8d-4b2a1c0d9e8f",
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

在提交任务和其他操作时，需要提供会话ID以确保操作的上下文正确性。

**Section sources**
- [main.py](file://vibe_surf/backend/main.py#L660-L669)

## API端点

### 任务管理

任务管理API提供任务提交、控制和状态查询功能。

#### 提交任务
```http
POST /api/tasks/submit
```

**请求体**:
```json
{
  "session_id": "string",
  "task_description": "string",
  "llm_profile_name": "string",
  "upload_files_path": "string",
  "mcp_server_config": {},
  "agent_mode": "thinking"
}
```

**请求参数**:
- `session_id`: 会话ID
- `task_description`: 任务描述
- `llm_profile_name`: LLM配置文件名称
- `upload_files_path`: 上传文件路径
- `mcp_server_config`: MCP服务器配置
- `agent_mode`: 代理模式（thinking, no-thinking, flash）

**成功响应**:
```json
{
  "success": true,
  "task_id": "string",
  "session_id": "string",
  "status": "submitted",
  "message": "Task submitted for execution",
  "llm_profile": "string",
  "workspace_dir": "string"
}
```

**错误响应**:
```json
{
  "success": false,
  "message": "Cannot submit task: another task is currently running",
  "active_task": {
    "task_id": "string",
    "status": "string",
    "session_id": "string",
    "start_time": "string"
  }
}
```

#### 检查任务状态
```http
GET /api/tasks/status
```

**响应**:
```json
{
  "has_active_task": false,
  "active_task": null
}
```

#### 暂停任务
```http
POST /api/tasks/pause
```

**请求体**:
```json
{
  "reason": "string"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Task paused successfully",
  "operation": "pause"
}
```

#### 恢复任务
```http
POST /api/tasks/resume
```

**请求体**:
```json
{
  "reason": "string"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Task resumed successfully",
  "operation": "resume"
}
```

#### 停止任务
```http
POST /api/tasks/stop
```

**请求体**:
```json
{
  "reason": "string"
}
```

**响应**:
```json
{
  "success": true,
  "message": "Task stopped successfully",
  "operation": "stop"
}
```

#### 添加新任务
```http
POST /api/tasks/add-new-task
```

**请求体**:
```json
{
  "reason": "string"
}
```

**响应**:
```json
{
  "success": true,
  "message": "New task added successfully",
  "operation": "add_new_task",
  "new_task": "string"
}
```

#### 获取详细任务状态
```http
GET /api/tasks/detailed-status
```

**响应**:
```json
{
  "has_active_task": true,
  "task_id": "string",
  "status": "string",
  "session_id": "string",
  "task": "string",
  "start_time": "string",
  "end_time": "string",
  "result": "string",
  "error": "string",
  "pause_reason": "string",
  "stop_reason": "string",
  "vibesurf_status": {
    "overall_status": "string",
    "active_step": "string",
    "agent_statuses": {},
    "progress": 0,
    "last_update": "string"
  }
}
```

**Section sources**
- [task.py](file://vibe_surf/backend/api/task.py#L1-L379)
- [models.py](file://vibe_surf/backend/api/models.py#L101-L171)

### 浏览器管理

浏览器管理API提供浏览器标签信息的获取功能。

#### 获取活动标签
```http
GET /api/browser/active-tab
```

**响应**:
```json
{
  "tab_id": {
    "url": "string",
    "title": "string"
  }
}
```

#### 获取所有标签
```http
GET /api/browser/all-tabs
```

**响应**:
```json
{
  "tab_id": {
    "url": "string",
    "title": "string"
  }
}
```

**Section sources**
- [browser.py](file://vibe_surf/backend/api/browser.py#L1-L71)

### 文件管理

文件管理API提供文件上传、下载和列表功能。

#### 上传文件
```http
POST /api/files/upload
```

**请求参数**:
- `files`: 文件列表（multipart/form-data）
- `session_id`: 会话ID（可选）

**响应**:
```json
{
  "message": "Successfully uploaded 1 files",
  "files": [
    {
      "file_id": "string",
      "original_filename": "string",
      "stored_filename": "string",
      "session_id": "string",
      "file_size": 0,
      "mime_type": "string",
      "upload_time": "string",
      "file_path": "string"
    }
  ],
  "upload_directory": "string"
}
```

#### 下载文件
```http
GET /api/files/{file_id}
```

返回文件内容，响应头包含文件名和MIME类型。

#### 列出上传的文件
```http
GET /api/files
```

**查询参数**:
- `session_id`: 会话ID（可选）
- `limit`: 限制数量（-1表示所有）
- `offset`: 偏移量

**响应**:
```json
{
  "files": [
    {
      "file_id": "string",
      "original_filename": "string",
      "stored_filename": "string",
      "session_id": "string",
      "file_size": 0,
      "mime_type": "string",
      "upload_time": "string",
      "file_path": "string"
    }
  ],
  "total_count": 0,
  "limit": 0,
  "offset": 0,
  "has_more": false,
  "session_id": "string"
}
```

#### 删除文件
```http
DELETE /api/files/{file_id}
```

**响应**:
```json
{
  "message": "File filename.txt deleted successfully",
  "file_id": "string"
}
```

#### 列出会话文件
```http
GET /api/files/session/{session_id}
```

**查询参数**:
- `include_directories`: 是否包含目录

**响应**:
```json
{
  "session_id": "string",
  "files": [
    {
      "name": "string",
      "path": "string",
      "size": 0,
      "mime_type": "string",
      "modified_time": "string",
      "type": "file"
    }
  ],
  "directories": [
    {
      "name": "string",
      "path": "string",
      "type": "directory"
    }
  ],
  "total_files": 0,
  "total_directories": 0
}
```

**Section sources**
- [files.py](file://vibe_surf/backend/api/files.py#L1-L332)
- [models.py](file://vibe_surf/backend/api/models.py#L217-L240)

### 配置管理

配置管理API提供LLM配置文件和环境变量的管理功能。

#### 创建LLM配置文件
```http
POST /api/config/llm-profiles
```

**请求体**:
```json
{
  "profile_name": "string",
  "provider": "string",
  "model": "string",
  "api_key": "string",
  "base_url": "string",
  "temperature": 0.7,
  "max_tokens": 1000,
  "top_p": 1,
  "frequency_penalty": 0,
  "seed": 0,
  "provider_config": {},
  "description": "string",
  "is_default": false
}
```

**响应**:
```json
{
  "profile_id": "string",
  "profile_name": "string",
  "provider": "string",
  "model": "string",
  "base_url": "string",
  "temperature": 0.7,
  "max_tokens": 1000,
  "top_p": 1,
  "frequency_penalty": 0,
  "seed": 0,
  "provider_config": {},
  "description": "string",
  "is_active": true,
  "is_default": false,
  "created_at": "string",
  "updated_at": "string",
  "last_used_at": "string"
}
```

#### 列出LLM配置文件
```http
GET /api/config/llm-profiles
```

**查询参数**:
- `active_only`: 仅活动配置文件
- `limit`: 限制数量
- `offset`: 偏移量

**响应**:
```json
[
  {
    "profile_id": "string",
    "profile_name": "string",
    "provider": "string",
    "model": "string",
    "base_url": "string",
    "temperature": 0.7,
    "max_tokens": 1000,
    "top_p": 1,
    "frequency_penalty": 0,
    "seed": 0,
    "provider_config": {},
    "description": "string",
    "is_active": true,
    "is_default": false,
    "created_at": "string",
    "updated_at": "string",
    "last_used_at": "string"
  }
]
```

#### 获取LLM配置文件
```http
GET /api/config/llm-profiles/{profile_name}
```

**响应**:
```json
{
  "profile_id": "string",
  "profile_name": "string",
  "provider": "string",
  "model": "string",
  "base_url": "string",
  "temperature": 0.7,
  "max_tokens": 1000,
  "top_p": 1,
  "frequency_penalty": 0,
  "seed": 0,
  "provider_config": {},
  "description": "string",
  "is_active": true,
  "is_default": false,
  "created_at": "string",
  "updated_at": "string",
  "last_used_at": "string"
}
```

#### 更新LLM配置文件
```http
PUT /api/config/llm-profiles/{profile_name}
```

**请求体**:
```json
{
  "provider": "string",
  "model": "string",
  "api_key": "string",
  "base_url": "string",
  "temperature": 0.7,
  "max_tokens": 1000,
  "top_p": 1,
  "frequency_penalty": 0,
  "seed": 0,
  "provider_config": {},
  "description": "string",
  "is_active": true,
  "is_default": false
}
```

**响应**:
```json
{
  "profile_id": "string",
  "profile_name": "string",
  "provider": "string",
  "model": "string",
  "base_url": "string",
  "temperature": 0.7,
  "max_tokens": 1000,
  "top_p": 1,
  "frequency_penalty": 0,
  "seed": 0,
  "provider_config": {},
  "description": "string",
  "is_active": true,
  "is_default": false,
  "created_at": "string",
  "updated_at": "string",
  "last_used_at": "string"
}
```

#### 删除LLM配置文件
```http
DELETE /api/config/llm-profiles/{profile_name}
```

**响应**:
```json
{
  "message": "LLM profile 'profile_name' deleted successfully"
}
```

#### 设置默认LLM配置文件
```http
POST /api/config/llm-profiles/{profile_name}/set-default
```

**响应**:
```json
{
  "message": "LLM profile 'profile_name' set as default"
}
```

#### 获取默认LLM配置文件
```http
GET /api/config/llm-profiles/default/current
```

**响应**:
```json
{
  "profile_id": "string",
  "profile_name": "string",
  "provider": "string",
  "model": "string",
  "base_url": "string",
  "temperature": 0.7,
  "max_tokens": 1000,
  "top_p": 1,
  "frequency_penalty": 0,
  "seed": 0,
  "provider_config": {},
  "description": "string",
  "is_active": true,
  "is_default": false,
  "created_at": "string",
  "updated_at": "string",
  "last_used_at": "string"
}
```

#### 获取可用提供商
```http
GET /api/config/llm/providers
```

**响应**:
```json
{
  "providers": [
    {
      "name": "string",
      "display_name": "string",
      "models": ["string"],
      "model_count": 0,
      "requires_api_key": true,
      "supports_base_url": false,
      "requires_base_url": false,
      "supports_tools": false,
      "supports_vision": false,
      "default_model": "string"
    }
  ],
  "total_providers": 0
}
```

#### 获取提供商模型
```http
GET /api/config/llm/providers/{provider_name}/models
```

**响应**:
```json
{
  "provider": "string",
  "display_name": "string",
  "models": ["string"],
  "model_count": 0,
  "default_model": "string",
  "metadata": {}
}
```

#### 获取配置状态
```http
GET /api/config/status
```

**响应**:
```json
{
  "llm_profiles": {
    "total_profiles": 0,
    "active_profiles": 0,
    "default_profile": "string",
    "has_default": true
  },
  "tools": {
    "initialized": true
  },
  "browser_manager": {
    "initialized": true
  },
  "vibesurf_agent": {
    "initialized": true,
    "workspace_dir": "string"
  },
  "overall_status": "ready"
}
```

#### 获取环境变量
```http
GET /api/config/environments
```

**响应**:
```json
{
  "environments": {
    "key": "value"
  },
  "count": 0
}
```

#### 更新环境变量
```http
PUT /api/config/environments
```

**请求体**:
```json
{
  "key": "value"
}
```

**响应**:
```json
{
  "message": "Environment variables updated successfully",
  "updated_keys": ["string"],
  "environments": {
    "key": "value"
  }
}
```

**Section sources**
- [config.py](file://vibe_surf/backend/api/config.py#L1-L762)
- [models.py](file://vibe_surf/backend/api/models.py#L13-L69)

### 活动日志

活动日志API提供任务历史和活动日志的查询功能。

#### 获取最近任务
```http
GET /api/activity/tasks
```

**查询参数**:
- `limit`: 限制数量（-1表示所有）

**响应**:
```json
{
  "tasks": [
    {
      "task_id": "string",
      "session_id": "string",
      "task_description": "string",
      "status": "string",
      "task_result": "string",
      "error_message": "string",
      "report_path": "string",
      "created_at": "string",
      "started_at": "string",
      "completed_at": "string"
    }
  ],
  "total_count": 0,
  "limit": 0
}
```

#### 获取所有会话
```http
GET /api/activity/sessions
```

**查询参数**:
- `limit`: 限制数量（-1表示所有）
- `offset`: 偏移量

**响应**:
```json
{
  "sessions": [
    {
      "session_id": "string",
      "task_count": 0,
      "last_task_at": "string",
      "created_at": "string"
    }
  ],
  "total_count": 0,
  "limit": 0,
  "offset": 0
}
```

#### 获取会话任务
```http
GET /api/activity/sessions/{session_id}/tasks
```

**响应**:
```json
{
  "session_id": "string",
  "tasks": [
    {
      "task_id": "string",
      "task_description": "string",
      "status": "string",
      "task_result": "string",
      "llm_profile_name": "string",
      "workspace_dir": "string",
      "mcp_server_config": {},
      "error_message": "string",
      "report_path": "string",
      "created_at": "string",
      "started_at": "string",
      "completed_at": "string"
    }
  ],
  "total_count": 0
}
```

#### 获取任务信息
```http
GET /api/activity/{task_id}
```

**响应**:
```json
{
  "task_id": "string",
  "session_id": "string",
  "task_description": "string",
  "status": "string",
  "upload_files_path": "string",
  "mcp_server_config": {},
  "llm_profile_name": "string",
  "task_result": "string",
  "error_message": "string",
  "report_path": "string",
  "created_at": "string",
  "started_at": "string",
  "completed_at": "string",
  "metadata": {}
}
```

#### 获取会话活动日志
```http
GET /api/activity/sessions/{session_id}/activity
```

**查询参数**:
- `limit`: 限制数量（-1表示所有）
- `message_index`: 消息索引

**响应**:
```json
{
  "session_id": "string",
  "activity_logs": [
    {
      "timestamp": "string",
      "level": "string",
      "message": "string",
      "metadata": {}
    }
  ],
  "total_count": 0,
  "original_total": 0
}
```

#### 获取最新活动
```http
GET /api/activity/sessions/{session_id}/latest_activity
```

**响应**:
```json
{
  "session_id": "string",
  "latest_vibesurf_log": {
    "timestamp": "string",
    "level": "string",
    "message": "string",
    "metadata": {}
  },
  "latest_task": null
}
```

**Section sources**
- [activity.py](file://vibe_surf/backend/api/activity.py#L1-L246)
- [models.py](file://vibe_surf/backend/api/models.py#L172-L206)

### 代理管理

代理管理API提供代理技能的查询功能。

#### 获取所有技能
```http
GET /api/agent/get_all_skills
```

**响应**:
```json
[
  "string"
]
```

**Section sources**
- [agent.py](file://vibe_surf/backend/api/agent.py#L1-L38)

### 计划管理

计划管理API提供工作流计划的管理功能。

#### 获取所有计划
```http
GET /api/schedule
```

**响应**:
```json
[
  {
    "id": "string",
    "flow_id": "string",
    "cron_expression": "string",
    "is_enabled": true,
    "description": "string",
    "last_execution_at": "string",
    "next_execution_at": "string",
    "execution_count": 0,
    "created_at": "string",
    "updated_at": "string"
  }
]
```

#### 创建计划
```http
POST /api/schedule
```

**请求体**:
```json
{
  "flow_id": "string",
  "cron_expression": "string",
  "is_enabled": true,
  "description": "string"
}
```

**响应**:
```json
{
  "id": "string",
  "flow_id": "string",
  "cron_expression": "string",
  "is_enabled": true,
  "description": "string",
  "last_execution_at": "string",
  "next_execution_at": "string",
  "execution_count": 0,
  "created_at": "string",
  "updated_at": "string"
}
```

#### 获取计划
```http
GET /api/schedule/{flow_id}
```

**响应**:
```json
{
  "id": "string",
  "flow_id": "string",
  "cron_expression": "string",
  "is_enabled": true,
  "description": "string",
  "last_execution_at": "string",
  "next_execution_at": "string",
  "execution_count": 0,
  "created_at": "string",
  "updated_at": "string"
}
```

#### 更新计划
```http
PUT /api/schedule/{flow_id}
```

**请求体**:
```json
{
  "cron_expression": "string",
  "is_enabled": true,
  "description": "string"
}
```

**响应**:
```json
{
  "id": "string",
  "flow_id": "string",
  "cron_expression": "string",
  "is_enabled": true,
  "description": "string",
  "last_execution_at": "string",
  "next_execution_at": "string",
  "execution_count": 0,
  "created_at": "string",
  "updated_at": "string"
}
```

#### 删除计划
```http
DELETE /api/schedule/{flow_id}
```

**响应**:
```json
{
  "message": "Schedule deleted for flow flow_id"
}
```

**Section sources**
- [schedule.py](file://vibe_surf/backend/api/schedule.py#L1-L331)

### Composio集成

Composio集成API提供Composio工具包的管理功能。

#### 获取Composio状态
```http
GET /api/composio/status
```

**响应**:
```json
{
  "connected": true,
  "key_valid": true,
  "has_key": true,
  "message": "string",
  "instance_available": true
}
```

#### 验证Composio API密钥
```http
POST /api/composio/verify-key
```

**请求体**:
```json
{
  "api_key": "string"
}
```

**响应**:
```json
{
  "valid": true,
  "message": "string",
  "user_info": {}
}
```

#### 获取Composio工具包
```http
GET /api/composio/toolkits
```

**查询参数**:
- `sync_with_api`: 是否与API同步

**响应**:
```json
{
  "toolkits": [
    {
      "id": "string",
      "name": "string",
      "slug": "string",
      "description": "string",
      "logo": "string",
      "app_url": "string",
      "enabled": true,
      "tools": [],
      "connection_status": "string",
      "created_at": "string",
      "updated_at": "string"
    }
  ],
  "total_count": 0,
  "synced_count": 0
}
```

#### 切换Composio工具包
```http
POST /api/composio/toolkit/{slug}/toggle
```

**请求体**:
```json
{
  "enabled": true,
  "force_reauth": false
}
```

**响应**:
```json
{
  "success": true,
  "message": "string",
  "enabled": true,
  "requires_oauth": true,
  "oauth_url": "string",
  "connected": true,
  "connection_status": "string"
}
```

#### 获取工具包工具
```http
GET /api/composio/toolkit/{slug}/tools
```

**响应**:
```json
{
  "toolkit_slug": "string",
  "tools": [
    {
      "name": "string",
      "description": "string",
      "parameters": {},
      "enabled": true
    }
  ],
  "total_tools": 0
}
```

**Section sources**
- [composio.py](file://vibe_surf/backend/api/composio.py#L1-L800)

### 语音管理

语音管理API提供语音配置文件和语音识别功能。

#### 创建语音配置文件
```http
POST /api/voices/voice-profiles
```

**请求体**:
```json
{
  "voice_profile_name": "string",
  "voice_model_type": "asr",
  "voice_model_name": "string",
  "api_key": "string",
  "voice_meta_params": {},
  "description": "string"
}
```

**响应**:
```json
{
  "success": true,
  "message": "string",
  "profile": {}
}
```

#### 更新语音配置文件
```http
PUT /api/voices/voice-profiles/{voice_profile_name}
```

**请求体**:
```json
{
  "voice_model_type": "asr",
  "voice_model_name": "string",
  "api_key": "string",
  "voice_meta_params": {},
  "description": "string",
  "is_active": true
}
```

**响应**:
```json
{
  "success": true,
  "message": "string",
  "profile": {
    "profile_id": "string",
    "voice_profile_name": "string",
    "voice_model_type": "string",
    "voice_model_name": "string",
    "voice_meta_params": {},
    "description": "string",
    "is_active": true,
    "created_at": "string",
    "updated_at": "string",
    "last_used_at": "string"
  }
}
```

#### 删除语音配置文件
```http
DELETE /api/voices/voice-profiles/{voice_profile_name}
```

**响应**:
```json
{
  "success": true,
  "message": "string"
}
```

#### 语音识别
```http
POST /api/voices/asr
```

**请求参数**:
- `audio_file`: 音频文件
- `voice_profile_name`: 语音配置文件名称

**响应**:
```json
{
  "success": true,
  "voice_profile_name": "string",
  "voice_model_name": "string",
  "recognized_text": "string",
  "filename": "string",
  "saved_audio_path": "string"
}
```

#### 列出语音配置文件
```http
GET /api/voices/voice-profiles
```

**查询参数**:
- `voice_model_type`: 语音模型类型
- `active_only`: 仅活动配置文件
- `limit`: 限制数量
- `offset`: 偏移量

**响应**:
```json
{
  "profiles": [
    {
      "profile_id": "string",
      "voice_profile_name": "string",
      "voice_model_type": "string",
      "voice_model_name": "string",
      "voice_meta_params": {},
      "description": "string",
      "is_active": true,
      "created_at": "string",
      "updated_at": "string",
      "last_used_at": "string"
    }
  ],
  "total": 0,
  "voice_model_type": "string",
  "active_only": true
}
```

#### 获取可用语音模型
```http
GET /api/voices/models
```

**查询参数**:
- `model_type`: 模型类型

**响应**:
```json
{
  "models": [
    {
      "model_name": "string",
      "model_type": "string",
      "requires_api_key": true
    }
  ],
  "total_models": 0
}
```

#### 获取语音配置文件
```http
GET /api/voices/{voice_profile_name}
```

**响应**:
```json
{
  "profile_id": "string",
  "voice_profile_name": "string",
  "voice_model_type": "string",
  "voice_model_name": "string",
  "voice_meta_params": {},
  "description": "string",
  "is_active": true,
  "created_at": "string",
  "updated_at": "string",
  "last_used_at": "string"
}
```

**Section sources**
- [voices.py](file://vibe_surf/backend/api/voices.py#L1-L481)

## 错误响应

VibeSurf API使用标准的HTTP状态码来表示请求结果。以下是常见的错误响应格式：

```json
{
  "detail": "string"
}
```

或

```json
{
  "error": "string",
  "detail": "string",
  "timestamp": "string"
}
```

**常见HTTP状态码**:
- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源未找到
- `409 Conflict`: 资源冲突
- `500 Internal Server Error`: 服务器内部错误

**Section sources**
- [main.py](file://vibe_surf/backend/main.py#L696-L724)
- [models.py](file://vibe_surf/backend/api/models.py#L178-L182)

## WebSocket API

目前代码库中未发现WebSocket API的实现。VibeSurf API主要基于HTTP RESTful架构，使用同步请求-响应模式进行通信。

**Section sources**
- [main.py](file://vibe_surf/backend/main.py#L1-L794)

## 客户端实现指南

### Python客户端示例

```python
import requests
import json

class VibeSurfClient:
    def __init__(self, base_url="http://localhost:9335"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def generate_session_id(self):
        """生成会话ID"""
        response = self.session.get(f"{self.base_url}/generate-session-id")
        return response.json()["session_id"]
    
    def submit_task(self, session_id, task_description, llm_profile_name):
        """提交任务"""
        payload = {
            "session_id": session_id,
            "task_description": task_description,
            "llm_profile_name": llm_profile_name
        }
        response = self.session.post(f"{self.base_url}/api/tasks/submit", json=payload)
        return response.json()
    
    def get_task_status(self):
        """获取任务状态"""
        response = self.session.get(f"{self.base_url}/api/tasks/status")
        return response.json()

# 使用示例
client = VibeSurfClient()
session_id = client.generate_session_id()
result = client.submit_task(
    session_id=session_id,
    task_description="搜索最新的AI新闻",
    llm_profile_name="openai-gpt4"
)
print(result)
```

### JavaScript客户端示例

```javascript
class VibeSurfClient {
    constructor(baseUrl = 'http://localhost:9335') {
        this.baseUrl = baseUrl;
    }
    
    async generateSessionId() {
        const response = await fetch(`${this.baseUrl}/generate-session-id`);
        const data = await response.json();
        return data.session_id;
    }
    
    async submitTask(sessionId, taskDescription, llmProfileName) {
        const response = await fetch(`${this.baseUrl}/api/tasks/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                session_id: sessionId,
                task_description: taskDescription,
                llm_profile_name: llmProfileName
            })
        });
        return await response.json();
    }
    
    async getTaskStatus() {
        const response = await fetch(`${this.baseUrl}/api/tasks/status`);
        return await response.json();
    }
}

// 使用示例
const client = new VibeSurfClient();
const sessionId = await client.generateSessionId();
const result = await client.submitTask(
    sessionId,
    '搜索最新的AI新闻',
    'openai-gpt4'
);
console.log(result);
```

**Section sources**
- [main.py](file://vibe_surf/backend/main.py#L660-L669)
- [task.py](file://vibe_surf/backend/api/task.py#L43-L146)

## API版本控制

VibeSurf API当前版本为2.0.0，通过`/api/status`端点可以获取API版本信息。

```http
GET /api/status
```

响应中包含版本信息：
```json
{
  "system_status": "operational",
  "active_task": null,
  "langflow_status": "not_started",
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

API遵循语义化版本控制原则，向后兼容性通过以下方式保证：
1. 不删除已存在的端点
2. 不修改现有端点的请求/响应格式
3. 新功能通过新增端点或可选参数实现
4. 重大变更通过版本号升级（如从v1到v2）实现

**Section sources**
- [main.py](file://vibe_surf/backend/main.py#L559-L560)
- [main.py](file://vibe_surf/backend/main.py#L650-L658)