[根目录](../../../CLAUDE.md) > [vibe_surf](../) > **agents**

# AI代理模块 (agents)

## 模块职责

AI代理模块是VibeSurf的核心智能引擎，负责基于LangGraph框架的多代理协调和任务执行。该模块提供智能浏览器操作、任务规划、并行执行和报告生成能力。

## 入口与启动

### 主要入口文件
- **vibe_surf_agent.py** - 主代理协调器，管理多代理工作流
- **browser_use_agent.py** - 浏览器自动化代理，基于browser-use框架
- **report_writer_agent.py** - 报告生成代理，创建结构化输出

### 启动流程
1. 通过VibeSurfState初始化工作流状态
2. 创建BrowserManager和VibeSurfTools实例
3. 注册多个专业代理（浏览器代理、报告代理等）
4. 构建LangGraph状态图，定义节点和边
5. 启动异步任务执行循环

## 对外接口

### 核心类和方法

#### VibeSurfAgent
```python
class VibeSurfAgent:
    def __init__(self, llm: BaseChatModel, browser_session: BrowserSession)
    async def execute_task(self, task: str, **kwargs) -> Dict[str, Any]
    async def pause_execution(self) -> ControlResult
    async def resume_execution(self) -> ControlResult
    async def stop_execution(self) -> ControlResult
```

#### 状态管理
- **VibeSurfState** - LangGraph工作流状态管理
- **AgentStatus** - 单个代理状态跟踪
- **VibeSurfStatus** - 整体系统状态

### 主要功能接口

#### 任务执行控制
- `submit_task()` - 提交新任务
- `pause_task()` - 暂停执行
- `resume_task()` - 恢复执行
- `stop_task()` - 停止任务

#### 代理管理
- `register_agent()` - 注册新代理
- `get_agent_status()` - 获取代理状态
- `assign_browser_session()` - 分配浏览器会话

## 关键依赖与配置

### 核心依赖
- **langgraph** - 工作流编排框架
- **browser-use** - 浏览器自动化库
- **pydantic** - 数据验证和序列化
- **asyncio** - 异步任务管理

### 配置组件
- **VibeSurfAgentSettings** - 代理配置参数
- **CustomAgentOutput** - 自定义输出格式
- **BrowserTaskResult** - 浏览器任务结果

## 数据模型

### 工作流状态
```python
@dataclass
class VibeSurfState:
    # 核心任务信息
    original_task: str
    upload_files: List[str]

    # 执行状态
    current_step: str
    completed_steps: List[str]

    # 代理状态
    agent_results: Dict[str, Any]

    # 浏览器会话
    available_tabs: List[TabInfo]
    active_tab_id: str
```

### 任务结果模型
```python
class BrowserTaskResult(BaseModel):
    agent_id: str
    agent_workdir: str
    success: bool
    task: Optional[str]
    result: Optional[str]
    error: Optional[str]
    important_files: Optional[List[str]]
```

## 测试与质量

### 测试覆盖
- **test_agents.py** - 代理核心功能测试
- **test_browser.py** - 浏览器操作测试
- **test_api_tools.py** - API工具集成测试

### 质量保证
- 异步错误处理和恢复机制
- 代理状态监控和日志记录
- 资源清理和内存管理
- 超时和重试机制

## 提示词系统

### 系统提示词
- **VIBESURF_SYSTEM_PROMPT** - 主代理系统提示词
- **EXTEND_BU_SYSTEM_PROMPT** - 浏览器代理扩展提示词
- **report_writer_prompt.py** - 报告生成专用提示词

### 提示词特性
- 专业AI浏览器助手角色定义
- 多代理协作指导原则
- 任务分解和并行执行策略
- 文件系统和路径管理规范

## 常见问题 (FAQ)

### Q: 如何添加新的代理类型？
A: 继承BaseAgent基类，实现execute方法，并在VibeSurfAgent中注册。

### Q: 代理之间如何通信？
A: 通过VibeSurfState共享状态，使用LangGraph的消息传递机制。

### Q: 如何处理代理执行失败？
A: 实现重试机制，记录错误日志，支持从断点恢复。

## 相关文件清单

### 核心代理文件
- `vibe_surf_agent.py` - 主代理协调器
- `browser_use_agent.py` - 浏览器自动化代理
- `report_writer_agent.py` - 报告生成代理

### 提示词文件
- `prompts/vibe_surf_prompt.py` - 主系统提示词
- `prompts/report_writer_prompt.py` - 报告生成提示词

### 工具和视图
- `views.py` - 数据模型定义
- `../tools/` - 集成工具集合

### 测试文件
- `../../tests/test_agents.py` - 代理功能测试
- `../../tests/test_browser.py` - 浏览器操作测试

## 变更记录 (Changelog)

**2025-11-21**: 初始模块文档生成，基于代码扫描和架构分析