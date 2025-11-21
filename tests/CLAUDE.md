[根目录](../CLAUDE.md) > **tests**

# 测试模块 (Test Module)

## 模块职责

提供全面的项目测试覆盖，包括单元测试、集成测试、端到端测试和性能测试，确保系统各模块的功能正确性和稳定性。

## 测试架构

### 测试分类
- **单元测试**: 独立模块和函数测试
- **集成测试**: 模块间交互测试
- **API测试**: 后端接口功能测试
- **浏览器测试**: 浏览器自动化测试
- **工具测试**: MCP和Composio集成测试
- **遥测测试**: 数据收集和发送测试

## 测试文件清单

### 核心测试文件

#### `test_agents.py`
- **VibeSurfAgent测试**: 代理核心功能验证
- **代理工作流测试**: 任务执行和状态管理
- **多代理协调测试**: 并发代理交互

#### `test_backend_api.py`
- **API端点测试**: 所有后端接口功能验证
- **数据库测试**: 数据模型和持久化
- **认证和授权测试**: 安全机制验证
- **WebSocket连接测试**: 实时通信功能

#### `test_browser.py`
- **浏览器会话测试**: AgentBrowserSession功能
- **CDP协议测试**: Chrome DevTools Protocol集成
- **元素提取测试**: SemanticExtractor准确性
- **导航和交互测试**: 页面操作功能

#### `test_tools.py`
- **MCP集成测试**: Model Context Protocol功能
- **Composio测试**: 第三方服务集成
- **文件系统测试**: CustomFileSystem操作
- **金融工具测试**: Yahoo Finance数据获取
- **工具注册测试**: 动态工具发现和管理

#### `test_telemetry.py`
- **事件捕获测试**: 遥测数据收集
- **PostHog集成测试**: 数据发送和验证
- **用户ID生成测试**: 匿名用户标识管理
- **配置控制测试**: 环境变量控制

#### `test_api_tools.py`
- **API工具集成测试**: 后端工具接口
- **任务管理测试**: 工作流编排
- **LangFlow集成测试**: 工作流引擎

#### `test_voice_api.py`
- **语音识别测试**: ASR功能验证
- **语音合成测试**: TTS功能验证
- **音频处理测试**: 格式转换和质量

## 测试工具和框架

### 主要测试框架
- **pytest**: 测试运行器和断言库
- **pytest-asyncio**: 异步测试支持
- **aiohttp**: 异步HTTP客户端测试
- **Playwright**: 浏览器自动化测试

### 测试配置
```python
# pytest.ini (示例)
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = -v --tb=short
```

## 关键测试场景

### 浏览器自动化测试
```python
async def test_browser_session():
    """测试浏览器会话管理"""
    session = AgentBrowserSession()
    await session.connect()

    # 测试导航
    await session.navigate_to_url("https://example.com")

    # 测试元素提取
    extractor = SemanticExtractor()
    elements = await extractor.extract_interactive_elements(session)

    assert len(elements) > 0
```

### MCP集成测试
```python
async def test_mcp_integration():
    """测试MCP服务器集成"""
    mcp_config = {
        "mcpServers": {
            "filesystem": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            }
        }
    }

    tools = VibeSurfTools(mcp_server_config=mcp_config)
    await tools.register_mcp_clients()

    # 验证工具注册
    actions = tools.registry.registry.actions.keys()
    assert any("mcp.filesystem" in action for action in actions)
```

### 遥测功能测试
```python
def test_telemetry_event():
    """测试遥测事件捕获"""
    event = CLITelemetryEvent(
        version="1.0.0",
        action='start',
        mode='interactive',
        model='gpt-4o'
    )

    telemetry = ProductTelemetry()

    # 验证PostHog客户端初始化
    assert telemetry._posthog_client is not None

    # 测试事件捕获
    telemetry.capture(event)
    telemetry.flush()
```

### API端点测试
```python
async def test_task_api():
    """测试任务管理API"""
    async with aiohttp.ClientSession() as session:
        # 提交任务
        task_data = {
            "task": "测试任务",
            "llm_profile": "default"
        }

        async with session.post('/api/tasks/submit', json=task_data) as resp:
            assert resp.status == 200
            result = await resp.json()
            task_id = result["task_id"]

        # 查询任务状态
        async with session.get(f'/api/tasks/status/{task_id}') as resp:
            assert resp.status == 200
            status = await resp.json()
            assert "status" in status
```

## 测试数据和Mock

### Mock数据生成
```python
# 模拟浏览器元素
mock_elements = [
    {
        "tag": "button",
        "text_content": "Submit",
        "css_selector": "#submit-btn",
        "position": {"x": 100, "y": 200}
    }
]

# 模拟金融数据
mock_finance_data = {
    "symbol": "AAPL",
    "current_price": 150.25,
    "volume": 1000000
}
```

### 测试环境配置
```python
# conftest.py (示例)
@pytest.fixture
async def browser_session():
    """提供测试用的浏览器会话"""
    session = AgentBrowserSession()
    await session.connect()
    yield session
    await session.disconnect()

@pytest.fixture
def telemetry_service():
    """提供测试用的遥测服务"""
    return ProductTelemetry()
```

## 性能测试

### 负载测试
- **并发请求测试**: 模拟多用户并发访问
- **内存使用测试**: 长时间运行内存泄漏检测
- **响应时间测试**: API响应时间基准

### 浏览器性能
- **页面加载时间**: 不同页面类型的加载性能
- **元素提取效率**: 大型页面的DOM处理性能
- **并发会话测试**: 多代理同时操作的性能

## 测试报告和覆盖率

### 覆盖率目标
- **代码覆盖率**: 目标90%以上
- **分支覆盖率**: 目标85%以上
- **功能覆盖率**: 100%核心功能覆盖

### 报告生成
```bash
# 运行测试并生成覆盖率报告
pytest --cov=vibe_surf --cov-report=html --cov-report=term

# 生成详细报告
pytest --html=test_report.html --self-contained-html
```

## 持续集成

### GitHub Actions配置
```yaml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest --cov=vibe_surf
```

## 常见问题 (FAQ)

**Q: 如何运行特定模块的测试？**
A: 使用 `pytest tests/test_module.py` 或 `pytest tests/test_module.py::test_function`。

**Q: 测试需要特殊的环境配置吗？**
A: 某些测试需要真实浏览器或外部服务，可以跳过或使用Mock。

**Q: 如何调试失败的测试？**
A: 使用 `pytest --pdb` 进入调试模式，或在测试中添加断点。

**Q: 测试数据存储在哪里？**
A: 测试数据在 `tests/fixtures/` 目录下，临时文件在 `/tmp/` 中。

## 相关文件清单

### 测试文件
- `test_agents.py` - 代理功能测试
- `test_backend_api.py` - 后端API测试
- `test_browser.py` - 浏览器功能测试
- `test_tools.py` - 工具集成测试
- `test_telemetry.py` - 遥测服务测试
- `test_api_tools.py` - API工具测试
- `test_voice_api.py` - 语音API测试

### 配置文件
- `pytest.ini` - pytest配置
- `conftest.py` - 测试夹具和配置
- `requirements-test.txt` - 测试依赖

### 测试数据
- `fixtures/` - 测试数据和Mock文件
- `mock_responses/` - API响应模拟数据

## 变更记录 (Changelog)

### 2025-11-21 深度扫描完成
- 新增测试模块完整文档
- 补充各类测试场景说明
- 添加测试工具和框架介绍
- 完善性能测试和CI配置指南