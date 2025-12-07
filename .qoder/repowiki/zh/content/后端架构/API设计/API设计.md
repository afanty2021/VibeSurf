# API设计

<cite>
**Referenced Files in This Document**   
- [main.py](file://vibe_surf/backend/main.py)
- [activity.py](file://vibe_surf/backend/api/activity.py)
- [agent.py](file://vibe_surf/backend/api/agent.py)
- [browser.py](file://vibe_surf/backend/api/browser.py)
- [composio.py](file://vibe_surf/backend/api/composio.py)
- [config.py](file://vibe_surf/backend/api/config.py)
- [files.py](file://vibe_surf/backend/api/files.py)
- [models.py](file://vibe_surf/backend/api/models.py)
- [schedule.py](file://vibe_surf/backend/api/schedule.py)
- [task.py](file://vibe_surf/backend/api/task.py)
- [vibesurf.py](file://vibe_surf/backend/api/vibesurf.py)
- [voices.py](file://vibe_surf/backend/api/voices.py)
</cite>

## 目录
1. [API端点组](#api端点组)
2. [API版本控制与向后兼容性](#api版本控制与向后兼容性)
3. [错误处理机制](#错误处理机制)
4. [API速率限制、输入验证与安全措施](#api速率限制输入验证与安全措施)
5. [自动生成的API文档访问指南](#自动生成的api文档访问指南)
6. [API调用示例](#api调用示例)

## API端点组

VibeSurf后端API提供了一组RESTful端点，用于管理各种功能，包括活动日志、代理、浏览器、Composio集成、配置、文件、模型、计划、任务、VibeSurf和语音。所有API端点均通过FastAPI框架实现，并遵循标准的HTTP方法和状态码。

### 活动 (Activity)
活动API端点用于检索VibeSurf代理的活动日志和数据库中的任务历史记录。

- **HTTP方法**: `GET`
- **URL模式**: 
  - `/api/activity/tasks` - 获取最近的任务
  - `/api/activity/sessions` - 获取所有会话
  - `/api/activity/sessions/{session_id}/tasks` - 获取特定会话的任务
  - `/api/activity/{task_id}` - 获取任务信息
  - `/api/activity/sessions/{session_id}/activity` - 获取特定会话的活动日志
  - `/api/activity/sessions/{session_id}/latest_activity` - 获取会话的最新活动
- **请求/响应模式**: 请求参数包括`limit`、`offset`、`session_id`等，响应包含任务或活动日志的详细信息。
- **认证方法**: 无特定认证，依赖于系统内部状态。

**Section sources**
- [activity.py](file://vibe_surf/backend/api/activity.py)

### 代理 (Agent)
代理API端点用于管理VibeSurf工具注册表中的技能。

- **HTTP方法**: `GET`
- **URL模式**: `/api/agent/get_all_skills` - 获取所有可用技能
- **请求/响应模式**: 响应为技能名称列表。
- **认证方法**: 无特定认证，依赖于系统内部状态。

**Section sources**
- [agent.py](file://vibe_surf/backend/api/agent.py)

### 浏览器 (Browser)
浏览器API端点用于获取浏览器标签页信息。

- **HTTP方法**: `GET`
- **URL模式**: 
  - `/api/browser/active-tab` - 获取当前活动标签页
  - `/api/browser/all-tabs` - 获取所有标签页
- **请求/响应模式**: 响应包含标签页的URL和标题。
- **认证方法**: 无特定认证，依赖于系统内部状态。

**Section sources**
- [browser.py](file://vibe_surf/backend/api/browser.py)

### Composio集成 (Composio Integration)
Composio API端点用于管理Composio集成，包括工具包配置、OAuth流程处理和API密钥验证。

- **HTTP方法**: `GET`, `POST`, `PUT`
- **URL模式**: 
  - `/api/composio/status` - 获取Composio连接状态
  - `/api/composio/verify-key` - 验证Composio API密钥
  - `/api/composio/toolkits` - 获取所有OAuth2工具包
  - `/api/composio/toolkit/{slug}/toggle` - 启用/禁用工具包
  - `/api/composio/toolkit/{slug}/tools` - 获取工具包工具
- **请求/响应模式**: 请求包含API密钥、工具包slug等，响应包含验证结果、工具包列表等。
- **认证方法**: 通过API密钥进行认证。

**Section sources**
- [composio.py](file://vibe_surf/backend/api/composio.py)

### 配置 (Config)
配置API端点用于管理LLM配置文件和工具配置。

- **HTTP方法**: `GET`, `POST`, `PUT`, `DELETE`
- **URL模式**: 
  - `/api/config/llm-profiles` - 创建、列出、更新、删除LLM配置文件
  - `/api/config/mcp-profiles` - 创建、列出、更新、删除MCP配置文件
  - `/api/config/llm/providers` - 获取可用LLM提供者
  - `/api/config/llm/providers/{provider_name}/models` - 获取特定提供者的模型
  - `/api/config/status` - 获取配置状态
  - `/api/config/environments` - 获取和更新环境变量
- **请求/响应模式**: 请求包含配置文件的详细信息，响应包含配置文件数据。
- **认证方法**: 无特定认证，依赖于系统内部状态。

**Section sources**
- [config.py](file://vibe_surf/backend/api/config.py)

### 文件 (Files)
文件API端点用于处理文件上传、下载和管理。

- **HTTP方法**: `POST`, `GET`, `DELETE`
- **URL模式**: 
  - `/api/files/upload` - 上传文件
  - `/api/files/{file_id}` - 下载文件
  - `/api/files` - 列出上传的文件
  - `/api/files/{file_id}` - 删除文件
  - `/api/files/session/{session_id}` - 列出会话文件
- **请求/响应模式**: 请求包含文件和会话ID，响应包含文件信息和上传目录。
- **认证方法**: 无特定认证，依赖于系统内部状态。

**Section sources**
- [files.py](file://vibe_surf/backend/api/files.py)

### 模型 (Models)
模型API端点定义了请求和响应的数据结构。

- **HTTP方法**: N/A (数据模型)
- **URL模式**: N/A
- **请求/响应模式**: 定义了LLM配置文件、任务、活动日志等的Pydantic模型。
- **认证方法**: N/A

**Section sources**
- [models.py](file://vibe_surf/backend/api/models.py)

### 计划 (Schedule)
计划API端点用于管理工作流计划。

- **HTTP方法**: `GET`, `POST`, `PUT`, `DELETE`
- **URL模式**: 
  - `/api/schedule` - 获取、创建、更新、删除计划
  - `/api/schedule/{flow_id}` - 获取、更新、删除特定计划
- **请求/响应模式**: 请求包含cron表达式和计划描述，响应包含计划详细信息。
- **认证方法**: 无特定认证，依赖于系统内部状态。

**Section sources**
- [schedule.py](file://vibe_surf/backend/api/schedule.py)

### 任务 (Task)
任务API端点用于提交、控制和监控任务执行。

- **HTTP方法**: `GET`, `POST`
- **URL模式**: 
  - `/api/tasks/status` - 检查任务状态
  - `/api/tasks/submit` - 提交新任务
  - `/api/tasks/pause` - 暂停任务
  - `/api/tasks/resume` - 恢复任务
  - `/api/tasks/stop` - 停止任务
  - `/api/tasks/add-new-task` - 添加新任务
  - `/api/tasks/detailed-status` - 获取详细任务状态
- **请求/响应模式**: 请求包含任务描述和LLM配置文件，响应包含任务ID和状态。
- **认证方法**: 无特定认证，依赖于系统内部状态。

**Section sources**
- [task.py](file://vibe_surf/backend/api/task.py)

### VibeSurf
VibeSurf API端点用于管理VibeSurf API密钥和工作流。

- **HTTP方法**: `GET`, `POST`, `DELETE`
- **URL模式**: 
  - `/api/vibesurf/verify-key` - 验证VibeSurf API密钥
  - `/api/vibesurf/status` - 获取VibeSurf连接状态
  - `/api/vibesurf/key` - 删除VibeSurf API密钥
  - `/api/vibesurf/validate` - 验证当前API密钥
  - `/api/vibesurf/generate-uuid` - 生成UUID
  - `/api/vibesurf/import-workflow` - 导入工作流
  - `/api/vibesurf/export-workflow/{flow_id}` - 导出工作流
  - `/api/vibesurf/version` - 获取VibeSurf版本
  - `/api/vibesurf/extension-path` - 获取扩展路径
  - `/api/vibesurf/serve` - 提供文件服务
  - `/api/vibesurf/news/sources` - 获取新闻源
  - `/api/vibesurf/news` - 获取新闻
- **请求/响应模式**: 请求包含API密钥和工作流JSON，响应包含验证结果和工作流ID。
- **认证方法**: 通过API密钥进行认证。

**Section sources**
- [vibesurf.py](file://vibe_surf/backend/api/vibesurf.py)

### 语音 (Voices)
语音API端点用于管理语音配置文件和语音识别。

- **HTTP方法**: `GET`, `POST`, `PUT`, `DELETE`
- **URL模式**: 
  - `/api/voices/voice-profiles` - 创建、列出、更新、删除语音配置文件
  - `/api/voices/asr` - 语音识别
  - `/api/voices/models` - 获取可用语音模型
  - `/api/voices/{voice_profile_name}` - 获取特定语音配置文件
- **请求/响应模式**: 请求包含音频文件和语音配置文件名称，响应包含识别的文本。
- **认证方法**: 无特定认证，依赖于系统内部状态。

**Section sources**
- [voices.py](file://vibe_surf/backend/api/voices.py)

## API版本控制与向后兼容性

VibeSurf后端API目前使用版本2.0.0，通过FastAPI的version参数在`main.py`中定义。API设计遵循向后兼容性原则，确保现有客户端在API更新时无需修改即可继续工作。未来的API版本将通过URL前缀（如`/api/v2/`）进行区分，以支持新功能和改进。

## 错误处理机制

VibeSurf API采用标准化的错误响应格式和HTTP状态码来处理错误情况。

### 标准化错误响应格式
错误响应通常包含以下字段：
- `error`: 错误类型或代码
- `detail`: 错误的详细描述
- `timestamp`: 错误发生的时间戳

例如：
```json
{
  "error": "llm_connection_failed",
  "detail": "Cannot connect to LLM API: Invalid API key",
  "timestamp": "2023-10-01T12:00:00Z"
}
```

### HTTP状态码使用
- `200 OK`: 请求成功
- `201 Created`: 资源创建成功
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源未找到
- `500 Internal Server Error`: 服务器内部错误

**Section sources**
- [main.py](file://vibe_surf/backend/main.py)
- [task.py](file://vibe_surf/backend/api/task.py)

## API速率限制、输入验证与安全措施

### 速率限制
目前API未实施显式的速率限制，但通过系统资源和任务队列进行隐式控制。

### 输入验证
所有API端点使用Pydantic模型进行输入验证，确保请求数据的完整性和正确性。例如，`TaskCreateRequest`模型验证任务描述和LLM配置文件名称。

### 安全措施
- **API密钥加密**: Composio和VibeSurf API密钥在数据库中加密存储。
- **CORS配置**: 允许所有来源的跨域请求，适用于开发环境。
- **边界检查**: 文件上传时检查multipart/form-data的边界参数，防止无效格式。

**Section sources**
- [main.py](file://vibe_surf/backend/main.py)
- [composio.py](file://vibe_surf/backend/api/composio.py)
- [vibesurf.py](file://vibe_surf/backend/api/vibesurf.py)

## 自动生成的API文档访问指南

VibeSurf后端API使用FastAPI自动生成Swagger/OpenAPI文档。要访问这些文档，请启动后端服务并导航到以下URL：
- Swagger UI: `http://localhost:9335/docs`
- ReDoc: `http://localhost:9335/redoc`

这些文档提供了所有API端点的交互式界面，包括请求示例、参数说明和响应模式。

**Section sources**
- [main.py](file://vibe_surf/backend/main.py)

## API调用示例

### 提交任务
```bash
curl -X POST "http://localhost:9335/api/tasks/submit" \
-H "Content-Type: application/json" \
-d '{
  "session_id": "session123",
  "task_description": "Summarize the article",
  "llm_profile_name": "openai-gpt4",
  "upload_files_path": "/path/to/file"
}'
```

### 验证Composio API密钥
```bash
curl -X POST "http://localhost:9335/api/composio/verify-key" \
-H "Content-Type: application/json" \
-d '{
  "api_key": "your-composio-api-key"
}'
```

### 上传文件
```bash
curl -X POST "http://localhost:9335/api/files/upload" \
-H "Content-Type: multipart/form-data" \
-F "files=@/path/to/file.txt" \
-F "session_id=session123"
```

**Section sources**
- [task.py](file://vibe_surf/backend/api/task.py)
- [composio.py](file://vibe_surf/backend/api/composio.py)
- [files.py](file://vibe_surf/backend/api/files.py)