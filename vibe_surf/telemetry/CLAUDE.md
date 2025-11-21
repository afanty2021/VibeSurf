[根目录](../../CLAUDE.md) > **telemetry**

# 遥测服务模块 (Telemetry Service Module)

## 模块职责

提供匿名化的产品遥测数据收集和分析服务，支持用户行为跟踪、性能监控和错误诊断。

## 入口与启动

- **ProductTelemetry** (`service.py`): 单例遥测服务管理器
- **BaseTelemetryEvent** (`views.py`): 遥测事件基类和具体事件定义

## 核心功能

### 匿名化遥测收集
- **用户ID管理**: 自动生成和持久化匿名用户标识
- **事件捕获**: 支持多种预定义事件类型
- **配置控制**: 通过环境变量控制遥测开关
- **数据安全**: 仅收集匿名化数据，保护用户隐私

### 事件类型系统
```python
# 支持的遥测事件类型
- CLITelemetryEvent: CLI使用事件
- VibeSurfAgentTelemetryEvent: 代理执行事件
- MCPClientTelemetryEvent: MCP客户端使用
- ComposioTelemetryEvent: Composio集成使用
- ReportWriterTelemetryEvent: 报告生成事件
- BackendTelemetryEvent: 后端API事件
```

### PostHog集成
- **实时数据收集**: 通过PostHog平台进行数据分析
- **异常自动捕获**: 自动记录应用异常和错误
- **性能指标**: 跟踪执行时间、资源使用等性能数据
- **地理位置**: 可选的地理位置信息收集

## 关键特性

### 自动用户标识
```python
# 自动生成和管理用户ID
telemetry = ProductTelemetry()
user_id = telemetry.user_id  # 自动获取或生成匿名用户ID
```

### 环境配置控制
```bash
# 环境变量控制
VIBESURF_ANONYMIZED_TELEMETRY=true    # 启用遥测 (默认true)
VIBESURF_DEBUG=false                  # 调试模式
```

### 事件捕获
```python
from vibe_surf.telemetry.views import CLITelemetryEvent

# 创建事件
event = CLITelemetryEvent(
    version="1.0.0",
    action="task_completed",
    mode="interactive",
    model="gpt-4o",
    duration_seconds=120.5
)

# 发送事件
telemetry.capture(event)
```

### Docker环境检测
```python
# 自动检测运行环境
@dataclass
class BaseTelemetryEvent:
    @property
    def properties(self) -> dict:
        props = {k: v for k, v in asdict(self).items() if k != 'name'}
        props['is_docker'] = is_running_in_docker()  # 自动添加Docker标识
        return props
```

## 遥测事件详解

### 代理执行事件
```python
@dataclass
class VibeSurfAgentTelemetryEvent:
    version: str
    action: str  # 'start', 'task_completed', 'error'
    task_description: str | None
    model: str | None
    model_provider: str | None
    duration_seconds: float | None
    success: bool | None
    error_message: str | None
    session_id: str | None
```

### MCP客户端事件
```python
@dataclass
class MCPClientTelemetryEvent:
    server_name: str
    command: str
    tools_discovered: int
    version: str
    action: str  # 'connect', 'disconnect', 'tool_call'
    tool_name: str | None = None
    duration_seconds: float | None = None
    error_message: str | None = None
```

### CLI使用事件
```python
@dataclass
class CLITelemetryEvent:
    version: str
    action: str  # 'start', 'message_sent', 'task_completed', 'error'
    mode: str  # 'interactive', 'oneshot', 'mcp_server'
    model: str | None = None
    model_provider: str | None = None
    browser_path: str | None = None
    duration_seconds: float | None = None
    error_message: str | None = None
```

## 配置和部署

### PostHog配置
```python
PROJECT_API_KEY = 'phc_lCYnQqFlfNHAlh1TJGqaTvD8EFPCKR7ONsEHbbWuPVr'
HOST = 'https://us.i.posthog.com'

# 事件设置
POSTHOG_EVENT_SETTINGS = {
    'process_person_profile': True,
}
```

### 用户ID持久化
```python
# 用户ID存储路径
WORKSPACE_DIR = common.get_workspace_dir()
USER_ID_PATH = os.path.join(WORKSPACE_DIR, 'telemetry', 'userid')

# 自动生成UUID7作为用户标识
new_user_id = uuid7str()
```

## 对外接口

### 核心API
- `capture(event)`: 捕获遥测事件
- `flush()`: 强制发送待处理事件
- `user_id`: 获取/生成用户标识

### 事件创建
```python
# 创建自定义事件
class CustomTelemetryEvent(BaseTelemetryEvent):
    custom_field: str
    numeric_value: int

    name: str = 'custom_event'
```

## 关键依赖与配置

### 核心依赖
- **posthog**: PostHog Python SDK
- **python-dotenv**: 环境变量管理
- **uuid-extensions**: UUID7生成

### 环境变量
```bash
# 遥测控制
VIBESURF_ANONYMIZED_TELEMETRY=true|false
VIBESURF_DEBUG=true|false

# PostHog配置 (内部使用)
POSTHOG_API_KEY=phc_...
POSTHOG_HOST=https://us.i.posthog.com
```

## 数据模型

### 事件基类
```python
@dataclass
class BaseTelemetryEvent(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    def properties(self) -> dict[str, Any]:
        # 自动转换为字典并添加Docker标识
        pass
```

### 单例管理
```python
@singleton
class ProductTelemetry:
    # 确保全局只有一个实例
    # 自动处理初始化和配置
```

## 测试与质量

### 测试覆盖
- 事件创建和验证测试
- PostHog集成测试
- 用户ID生成和持久化测试
- 环境配置控制测试

### 测试示例
```python
def test_cli_telemetry_event():
    event = CLITelemetryEvent(
        version="1.0.0",
        action='start',
        mode='interactive'
    )

    telemetry = ProductTelemetry()
    telemetry.capture(event)
    telemetry.flush()
```

## 常见问题 (FAQ)

**Q: 遥测数据是否包含敏感信息？**
A: 所有遥测数据都是匿名的，不包含个人身份信息、用户内容或敏感数据。

**Q: 如何禁用遥测收集？**
A: 设置环境变量 `VIBESURF_ANONYMIZED_TELEMETRY=false`。

**Q: PostHog数据存储在哪里？**
A: 数据存储在PostHog云平台，符合GDPR和相关隐私法规。

**Q: 遥测对性能有什么影响？**
A: 遥测使用异步发送，对应用性能影响微乎其微。

## 相关文件清单

### 核心文件
- `service.py` - 遥测服务实现
- `views.py` - 事件定义和数据模型
- `__init__.py` - 模块初始化

### 测试文件
- `tests/test_telemetry.py` - 遥测功能测试

## 变更记录 (Changelog)

### 2025-11-21 深度扫描完成
- 新增遥测服务完整文档
- 补充PostHog集成说明
- 添加事件类型详细定义
- 完善配置和部署指南