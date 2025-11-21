[根目录](../../CLAUDE.md) > **browser**

# 浏览器控制模块 (Browser Control Module)

## 模块职责

负责浏览器会话管理、页面操作、元素提取和多代理隔离，提供完整的浏览器自动化控制能力。

## 入口与启动

- **BrowserManager** (`browser_manager.py`): 主要的浏览器管理器
- **AgentBrowserSession** (`agent_browser_session.py`): 代理专用浏览器会话
- **AgentBrowserProfile** (`agen_browser_profile.py`): 代理浏览器配置文件

## 核心功能

### 会话管理
- **多代理隔离**: 每个代理拥有独立的浏览器会话和标签页
- **CDP协议集成**: 直接使用Chrome DevTools Protocol进行高效控制
- **连接管理**: 支持本地和远程浏览器连接
- **资源优化**: 浏览器实例复用和资源清理

### 页面操作
- **导航控制**: URL导航、历史记录管理、新标签页创建
- **元素交互**: 点击、输入、悬停、拖拽等操作
- **屏幕截图**: 支持全页面和区域截图，带高亮标注
- **滚动控制**: 智能滚动到指定元素或文本

### 智能元素提取
- **SemanticExtractor** (`find_page_element.py`): 语义化元素提取器
  - 支持复杂UI组件识别（日历、下拉菜单、表单等）
  - 层次化上下文理解和重复元素处理
  - 智能文本匹配和模糊查找
- **页面元素映射**: 可见文本到确定选择器的映射
- **元素定位**: 多种定位策略（索引、XPath、CSS选择器）

### 监控看门狗系统
- **ActionWatchdog** (`watchdogs/action_watchdog.py`): 自定义动作监控
- **DOMWatchdog** (`watchdogs/dom_watchdog.py`): DOM变化监控
- **页面状态跟踪**: 实时监控页面加载和交互状态

## 关键特性

### 高级浏览器功能
```python
# 代理会话管理
session = AgentBrowserSession()
await session.connect(cdp_url)
await session.attach_all_watchdogs()

# 并发导航
target_id = await session.navigate_to_url(url, new_tab=True)

# 高效截图
screenshot_bytes = await session.take_screenshot(full_page=True)
highlighted = await create_highlighted_screenshot_async(screenshot, selector_map)
```

### 语义元素提取
```python
# 智能元素识别
extractor = SemanticExtractor()
elements = await extractor.extract_interactive_elements(session)
mapping = await extractor.extract_semantic_mapping(session)

# 层次化查找
element = extractor.find_element_by_hierarchy(mapping, "Submit", ["form", "contact"])
```

### 自定义浏览器配置
```python
# 扩展和配置
profile = AgentBrowserProfile(
    custom_extensions=["/path/to/extension"],
    headless=False,
    disable_security=True
)
```

## 对外接口

### 主要API端点
- `POST /api/browser/tabs`: 获取浏览器标签页列表
- `POST /api/browser/navigate`: 导航到指定URL
- `POST /api/browser/screenshot`: 截取当前页面
- `POST /api/browser/elements`: 提取页面交互元素

### 核心类和方法
- `AgentBrowserSession`: 代理会话管理
  - `connect()`: 连接到浏览器
  - `navigate_to_url()`: 页面导航
  - `take_screenshot()`: 截图
  - `get_or_create_cdp_session()`: CDP会话管理
- `SemanticExtractor`: 语义元素提取
  - `extract_interactive_elements()`: 提取交互元素
  - `find_element_by_text()`: 文本查找元素
  - `find_element_by_hierarchy()`: 层次化查找

## 关键依赖与配置

### 核心依赖
- **browser_use**: 浏览器自动化基础框架
- **cdp_use**: Chrome DevTools Protocol客户端
- **playwright**: 浏览器引擎支持
- **selenium**: 备用浏览器控制

### 配置文件
- 扩展配置在`AgentBrowserProfile`中管理
- 支持默认扩展下载和缓存
- 可配置浏览器启动参数和安全设置

## 数据模型

### 会话状态
```python
@dataclass
class BrowserSession:
    id: str
    cdp_url: str
    agent_focus: CDPSession | None
    _cdp_session_pool: Dict[str, CDPSession]
```

### 元素信息
```python
@dataclass
class ElementInfo:
    tag: str
    text_content: str
    css_selector: str
    hierarchical_selector: str
    position: Dict[str, float]
    container_context: Dict
```

## 测试与质量

### 测试覆盖
- 单元测试：浏览器会话管理、元素提取
- 集成测试：多代理隔离、CDP协议
- 端到端测试：完整工作流测试

### 性能优化
- CDP直接调用，绕过序列化瓶颈
- 并发操作支持
- 资源池管理和连接复用

## 常见问题 (FAQ)

**Q: 如何处理多代理间的浏览器隔离？**
A: 每个代理使用独立的`AgentBrowserSession`，通过不同的CDP会话池实现隔离。

**Q: 元素查找失败时如何处理？**
A: 使用`SemanticExtractor`的多策略查找：精确匹配 -> 模糊匹配 -> 层次化上下文查找。

**Q: 如何优化截图性能？**
A: 使用`AgentBrowserSession`的并发截图方法，避免事件系统开销。

## 相关文件清单

### 核心文件
- `browser_manager.py` - 浏览器管理器
- `agent_browser_session.py` - 代理会话实现
- `agen_browser_profile.py` - 浏览器配置
- `find_page_element.py` - 元素提取器
- `page_operations.py` - 页面操作
- `utils.py` - 工具函数

### 监控模块
- `watchdogs/__init__.py` - 看门狗模块初始化
- `watchdogs/action_watchdog.py` - 动作监控
- `watchdogs/dom_watchdog.py` - DOM监控

## 变更记录 (Changelog)

### 2025-11-21 深度扫描完成
- 新增语义元素提取器详细文档
- 补充CDP协议集成说明
- 添加监控看门狗系统介绍
- 完善API接口和使用示例