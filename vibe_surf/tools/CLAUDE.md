[根目录](../../CLAUDE.md) > **tools**

# 工具集成模块 (Tools Integration Module)

## 模块职责

提供统一的工具集成框架，支持MCP客户端、Composio集成、文件系统操作、金融数据获取和浏览器工具扩展。

## 入口与启动

- **VibeSurfTools** (`vibesurf_tools.py`): 主要工具集成管理器
- **BrowserUseTools** (`browser_use_tools.py`): 浏览器工具扩展
- **CustomFileSystem** (`file_system.py`): 自定义文件系统

## 核心功能

### MCP集成 (Model Context Protocol)
- **CustomMCPClient** (`mcp_client.py`): 自定义MCP客户端实现
- 支持动态MCP服务器连接和管理
- 工具发现和自动注册机制
- 支持文件系统、桌面命令等MCP服务器

### Composio集成
- **ComposioClient** (`composio_client.py`): Composio平台集成客户端
- 支持Gmail、Slack、Google Workspace等第三方服务
- OAuth认证和连接管理
- 动态工具注册和配置

### 文件系统操作
```python
# 自定义文件系统支持多种格式
filesystem = CustomFileSystem("/workspace/path")

# 文件操作
await filesystem.write_file("report.md", content)
await filesystem.read_file("data.json")
await filesystem.create_directory("exports")

# 支持的文件类型
- MarkdownFile, TxtFile, JsonFile
- CsvFile, PdfFile, PythonFile, HtmlFile, JSFile
```

### 金融数据工具
```python
# Yahoo Finance集成
from vibe_surf.tools.finance_tools import FinanceDataRetriever

retriever = FinanceDataRetriever('AAPL')
data = retriever.get_finance_data([
    'get_info', 'get_history',
    'get_dividends', 'get_news'
])

# 支持的数据类型
- 基本公司信息和历史价格
- 财务报表和收益数据
- 分析师建议和新闻
- 股东信息和持仓数据
```

### 浏览器工具扩展
```python
# 扩展的浏览器操作
tools = BrowserUseTools()

# 高级导航
await tools.navigate_to_url("https://example.com", new_tab=True)

# 智能元素交互
await tools.hover(index=5)  # 或使用xpath/selector

# 媒体下载
await tools.download_media(
    url="https://example.com/image.jpg",
    filename="downloaded_image"
)
```

## 工具生态系统

### 支持的工具类别

#### 1. MCP服务器工具
- **文件系统**: 目录浏览、文件读写
- **桌面命令**: 进程管理、系统操作
- **MarkItDown**: 文档格式转换

#### 2. Composio集成工具
- **Gmail**: 邮件读取、发送、搜索
- **Slack**: 消息发送、频道管理
- **Google Workspace**: 文档、表格操作
- **GitHub**: 仓库管理、Issue处理

#### 3. 专用工具
- **搜索引擎**: Google、DuckDuckGo、Bing
- **金融数据**: Yahoo Finance API集成
- **媒体处理**: 文件下载、格式检测
- **报告生成**: 自动化报告编写

## 关键特性

### 动态工具注册
```python
# 配置MCP服务器
mcp_config = {
    "mcpServers": {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"]
        }
    }
}

# 初始化工具管理器
tools = VibeSurfTools(mcp_server_config=mcp_config)
await tools.register_mcp_clients()
```

### 工具发现和管理
```python
# 获取所有可用工具
available_actions = tools.registry.registry.actions.keys()

# 动态工具调用
action_model = tools.registry.create_action_model()
result = await tools.act(action_model(**params))
```

### 认证和连接管理
```python
# Composio OAuth集成
composio_client = ComposioClient(composio_instance=composio)

# 注册已连接的工具
await composio_client.register_to_tools(
    tools,
    toolkit_tools_dict
)
```

## 对外接口

### 工具注册API
- `register_mcp_clients()`: 注册MCP客户端
- `register_composio_tools()`: 注册Composio工具
- `unregister_mcp_clients()`: 注销MCP客户端

### 工具执行API
- `act()`: 执行工具动作
- `create_action_model()`: 创建动作模型
- `get_available_tools()`: 获取可用工具列表

### 文件系统API
- `write_file()`: 写入文件
- `read_file()`: 读取文件
- `list_directory()`: 列出目录
- `create_directory()`: 创建目录

## 关键依赖与配置

### 核心依赖
- **mcp**: Model Context Protocol客户端
- **composio**: 第三方服务集成
- **yfinance**: Yahoo Finance API
- **aiohttp**: 异步HTTP客户端

### 配置要求
- MCP服务器配置文件
- Composio API密钥
- 文件系统访问权限
- 网络访问权限

## 数据模型

### 工具配置
```python
@dataclass
class MCPConfig:
    mcpServers: Dict[str, ServerConfig]

@dataclass
class ServerConfig:
    command: str
    args: List[str]
    env: Dict[str, str] = None
```

### 金融数据格式
```python
@dataclass
class FinanceResult:
    symbol: str
    data: Dict[str, Any]
    timestamp: datetime
    method: str
```

## 测试与质量

### 测试覆盖
- MCP客户端连接测试
- Composio集成测试
- 文件系统操作测试
- 金融数据获取测试
- 工具注册和执行测试

### 测试工具
- `test_tools.py`: 综合工具测试
- MCP服务器模拟测试
- OAuth认证流程测试

## 常见问题 (FAQ)

**Q: 如何添加新的MCP服务器？**
A: 在配置文件中添加服务器定义，然后调用`register_mcp_clients()`。

**Q: Composio工具需要什么认证？**
A: 使用OAuth流程，通过Composio平台管理第三方服务连接。

**Q: 如何处理大文件操作？**
A: 使用流式处理和分块读取，支持大文件的异步操作。

## 相关文件清单

### 核心文件
- `vibesurf_tools.py` - 主工具管理器
- `browser_use_tools.py` - 浏览器工具扩展
- `mcp_client.py` - MCP客户端实现
- `composio_client.py` - Composio集成
- `file_system.py` - 文件系统实现
- `finance_tools.py` - 金融数据工具

### 支持文件
- `views.py` - 数据视图定义
- `utils.py` - 工具函数
- `vibesurf_registry.py` - 工具注册表
- `report_writer_tools.py` - 报告生成工具

### 网站API集成
- `website_api/douyin/` - 抖音API集成
- `website_api/weibo/` - 微博API集成
- `website_api/xhs/` - 小红书API集成
- `website_api/youtube/` - YouTube API集成

## 变更记录 (Changelog)

### 2025-11-21 深度扫描完成
- 新增MCP集成详细文档
- 补充Composio集成说明
- 添加金融工具使用指南
- 完善文件系统操作文档
- 添加网站API集成介绍