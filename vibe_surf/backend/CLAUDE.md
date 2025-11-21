[根目录](../../../CLAUDE.md) > [vibe_surf](../) > **backend**

# 后端API服务模块 (backend)

## 模块职责

后端API服务模块是VibeSurf的服务端核心，基于FastAPI框架构建，提供RESTful API接口。负责任务管理、代理协调、数据库操作、文件处理和LangFlow集成。

## 入口与启动

### 主要入口文件
- **main.py** - FastAPI应用主入口，包含应用生命周期管理
- **cli.py** - 命令行启动入口（位于上级目录）

### 启动流程
1. 解析命令行参数和环境变量
2. 配置LangFlow环境变量
3. 初始化FastAPI应用和中间件
4. 启动后台服务（LangFlow初始化、浏览器监控、调度管理）
5. 挂载静态文件和API路由
6. 启动Uvicorn服务器

### 启动命令
```bash
# 开发模式
uvicorn vibe_surf.backend.main:app --reload --host 127.0.0.1 --port 9335

# 生产模式
vibesurf
```

## 对外接口

### API路由结构

#### 核心任务管理 (/api/tasks)
- **GET /api/tasks/status** - 检查任务状态
- **POST /api/tasks/submit** - 提交新任务
- **POST /api/tasks/control** - 任务控制（暂停/恢复/停止）

#### 文件管理 (/api/files)
- **POST /api/files/upload** - 文件上传
- **GET /api/files/list** - 文件列表
- **DELETE /api/files/{file_id}** - 文件删除

#### 浏览器控制 (/api/browser)
- **GET /api/browser/tabs** - 获取浏览器标签页
- **POST /api/browser/navigate** - 导航到URL
- **POST /api/browser/screenshot** - 截图

#### 代理管理 (/api/agent)
- **GET /api/agent/status** - 代理状态
- **POST /api/agent/config** - 配置代理

#### 语音服务 (/api/voices)
- **GET /api/voices/profiles** - 语音配置文件
- **POST /api/voices/asr** - 语音识别
- **POST /api/voices/tts** - 语音合成

#### 配置管理 (/api/config)
- **GET /api/config/llm-profiles** - LLM配置文件
- **POST /api/config/llm-profiles** - 创建LLM配置
- **PUT /api/config/llm-profiles/{profile_id}** - 更新LLM配置

#### 调度管理 (/api/schedule)
- **GET /api/schedule/jobs** - 定时任务列表
- **POST /api/schedule/jobs** - 创建定时任务

### 系统接口
- **GET /health** - 健康检查
- **GET /api/status** - 系统状态
- **GET /generate-session-id** - 生成会话ID

## 关键依赖与配置

### 核心依赖
- **fastapi** - Web框架
- **uvicorn** - ASGI服务器
- **sqlalchemy** - ORM框架
- **alembic** - 数据库迁移
- **pydantic** - 数据验证

### 数据库配置
```python
# 数据库连接
DATABASE_URL = "sqlite:///./workspace/langflow.db"

# 连接池配置
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

### 中间件配置
- **CORSMiddleware** - 跨域资源共享
- **JavaScriptMIMETypeMiddleware** - MIME类型处理
- **SentryAsgiMiddleware** - 错误监控（可选）

## 数据模型

### 核心数据表

#### 任务表 (Task)
```python
class Task(Base):
    __tablename__ = 'tasks'

    task_id = Column(String(36), primary_key=True)
    session_id = Column(String(36), nullable=False)
    task_content = Column(Text, nullable=False)
    task_type = Column(String(50), default="general")
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)
    llm_profile_name = Column(String(100), nullable=False)
    workspace_dir = Column(String(500), nullable=False)

    # 时间戳
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
```

#### LLM配置表 (LLMProfile)
```python
class LLMProfile(Base):
    __tablename__ = 'llm_profiles'

    profile_id = Column(String(36), primary_key=True)
    profile_name = Column(String(100), nullable=False, unique=True)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    base_url = Column(String(500), nullable=True)
    encrypted_api_key = Column(Text, nullable=True)

    # LLM参数
    temperature = Column(JSON, nullable=True)
    max_tokens = Column(JSON, nullable=True)
    top_p = Column(JSON, nullable=True)

    # 元数据
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)
```

#### 语音配置表 (VoiceProfile)
```python
class VoiceProfile(Base):
    __tablename__ = 'voice_profiles'

    profile_id = Column(String(36), primary_key=True)
    voice_profile_name = Column(String(100), nullable=False, unique=True)
    voice_model_type = Column(Enum(VoiceModelType), nullable=False)
    voice_model_name = Column(String(100), nullable=False)
    encrypted_api_key = Column(Text, nullable=True)
    voice_meta_params = Column(JSON, nullable=True)
```

## 共享状态管理

### shared_state.py
```python
class SharedState:
    # 全局实例
    browser_manager: Optional[BrowserManager] = None
    llm: Optional[BaseChatModel] = None
    active_task: Optional[Dict[str, Any]] = None
    workspace_dir: str = get_workspace_dir()

    # 初始化方法
    async def initialize_vibesurf_components()
    async def initialize_schedule_manager()
    async def shutdown_schedule_manager()
```

## 测试与质量

### 测试覆盖
- **test_backend_api.py** - API接口测试
- **test_api_tools.py** - API工具测试
- **test_telemetry.py** - 遥测服务测试

### 质量保证
- API请求验证和错误处理
- 数据库事务管理
- 异步操作超时控制
- 资源清理和内存管理

## LangFlow集成

### 集成特性
- **后台初始化** - 异步加载LangFlow服务
- **数据库共享** - 复用SQLite数据库
- **组件缓存** - 预加载和缓存组件
- **API路由合并** - 统一API端点

### 初始化流程
1. 配置LangFlow环境变量
2. 初始化设置服务和队列服务
3. 加载组件和预设项目
4. 启动MCP服务器
5. 开始遥测服务

## 安全特性

### API安全
- 请求大小限制中间件
- 多部分表单验证
- 跨域请求控制
- 敏感信息过滤

### 数据加密
- API密钥使用MAC地址加密存储
- 数据库连接加密
- 传输层HTTPS支持

## 常见问题 (FAQ)

### Q: 如何添加新的API路由？
A: 在api/目录下创建新路由文件，然后在main.py中注册。

### Q: 数据库迁移如何处理？
A: 使用Alembic进行迁移管理，通过alembic命令生成和应用迁移。

### Q: 如何配置LLM提供商？
A: 通过/api/config/llm-profiles接口创建配置文件，支持加密存储API密钥。

## 相关文件清单

### 应用入口
- `main.py` - FastAPI应用主入口
- `shared_state.py` - 全局状态管理

### API路由
- `api/task.py` - 任务管理API
- `api/files.py` - 文件管理API
- `api/browser.py` - 浏览器控制API
- `api/config.py` - 配置管理API
- `api/agent.py` - 代理管理API
- `api/voices.py` - 语音服务API
- `api/activity.py` - 活动日志API
- `api/schedule.py` - 调度管理API

### 数据层
- `database/models.py` - SQLAlchemy模型定义
- `database/manager.py` - 数据库管理器
- `database/queries.py` - 数据库查询操作
- `database/schemas.py` - Pydantic模式定义

### 工具和配置
- `llm_config.py` - LLM配置管理
- `voice_model_config.py` - 语音模型配置
- `utils/` - 工具函数集合

## 变更记录 (Changelog)

**2025-11-21**: 初始模块文档生成，基于代码扫描和架构分析