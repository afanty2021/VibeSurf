# VibeSurf - AI 智能浏览器助手

> 更新时间：2025-12-15 11:00:00
> 项目地址：https://github.com/vibesurf-ai/VibeSurf

## 项目简介

VibeSurf 是一个开源的 AI 驱动的智能浏览器助手，专注于浏览器自动化和智能研究。它结合了先进的 AI 技术、多代理并行处理和直观的工作流系统，为用户提供强大而高效的浏览器操作体验。

## 核心特性

### 🧠 高级 AI 自动化
- 超越传统浏览器自动化，支持深度研究、智能爬虫、内容摘要等功能
- 集成多个 AI 模型提供商（OpenAI、Google Gemini、Anthropic Claude 等）
- 支持本地 LLM（如 Ollama）确保隐私安全

### 🚀 多代理并行处理
- 在不同的浏览器标签页中同时运行多个 AI 代理
- 实现深度研究和广度研究的巨大效率提升
- 支持分布式任务执行

### 🔄 智能浏览器工作流
- 拖拽式和对话式自定义工作流创建
- 结合确定性自动化与 AI 智能决策
- 适用于自动登录、数据收集、社交媒体发布等重复性任务

### 🎨 原生 Chrome 扩展 UI
- 无缝的浏览器集成，无需切换应用
- 直观的用户界面，如同浏览器原生功能
- 支持实时交互和状态显示

### 🔒 隐私优先的 LLM 支持
- 支持本地 LLM 部署（Ollama 等）
- 支持自定义 LLM API
- 确保浏览数据的隐私和安全

### 🛠️ 工作流技能系统
- 将工作流输入暴露为可复用的技能
- 支持技能配置和管理
- 工作流技能的动态加载和执行

### 📁 文件系统操作
- 完整的文件系统工作流支持（读取、写入、复制、移动等）
- 文件内容搜索和替换
- 目录创建和管理

## 技术架构

### 编程语言
- **Python 3.11+**: 主要后端开发语言
- **TypeScript**: 前端和 Chrome 扩展开发
- **JavaScript**: 部分前端交互功能

### 核心框架与库
- **LangGraph**: AI 工作流编排
- **LangChain**: AI 应用开发框架
- **FastAPI**: 后端 API 服务
- **Browser-use**: 浏览器自动化核心
- **UVicorn**: ASGI 服务器
- **React**: 前端 UI 框架

### AI/ML 集成
- **OpenAI API**: GPT 系列模型
- **Google Gemini**: Google 的 AI 模型
- **Anthropic Claude**: Claude AI 模型
- **本地 LLM 支持**: Ollama 等本地部署方案
- **多提供商支持**: 通过 LiteLLM 统一接口

### 数据存储与处理
- **SQLite**: 本地数据存储
- **DuckDB**: 高性能分析数据库
- **Pandas**: 数据处理和分析
- **Redis**: 缓存和会话管理

### 第三方集成
- **Composio**: 与数百个流行工具集成（Gmail、Notion、GitHub 等）
- **原生 API**: 小红书、抖音、微博、YouTube、知乎等平台
- **Firecrawl**: 网页数据提取
- **AssemblyAI**: 语音识别和转录

## 项目结构

```
vibesurf/
├── vibe_surf/                 # 主要源代码目录
│   ├── agents/               # AI 代理实现
│   ├── backend/              # FastAPI 后端服务
│   ├── browser/              # 浏览器控制和自动化
│   ├── chrome_extension/     # Chrome 扩展源码
│   ├── frontend/             # React 前端应用
│   ├── langflow/             # LangFlow 集成
│   ├── llm/                  # LLM 模型管理
│   ├── tools/                # 工具和实用程序
│   │   ├── website_api/      # 各网站 API 集成
│   │   │   ├── xhs/         # 小红书 API
│   │   │   ├── douyin/      # 抖音 API
│   │   │   ├── weibo/       # 微博 API
│   │   │   ├── youtube/     # YouTube API
│   │   │   └── zhihu/       # 知乎 API
│   │   ├── website_api_skills.py # 网站 API 技能封装
│   │   └── ...              # 其他工具
│   ├── workflows/            # 预定义工作流
│   │   ├── FileSystem/      # 文件系统操作工作流
│   │   ├── Integrations/    # 平台集成工作流
│   │   └── VibeSurf/        # VibeSurf 核心工作流
│   └── telemetry/            # 遥测和监控
├── tests/                    # 测试文件
├── docs/                     # 项目文档
├── scripts/                  # 构建和部署脚本
└── assets/                   # 静态资源
```

## 快速开始

### 环境要求
- Python 3.11 或更高版本
- Node.js 16+（用于前端构建）
- Chrome 浏览器（用于浏览器自动化）

### 安装步骤

1. **安装 uv 包管理器**
   ```bash
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Windows
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. **安装 VibeSurf**
   ```bash
   uv pip install vibesurf -U
   ```

3. **启动 VibeSurf**
   ```bash
   uv run vibesurf
   ```

### 开发环境设置

1. **克隆仓库**
   ```bash
   git clone https://github.com/vibesurf-ai/VibeSurf.git
   cd VibeSurf
   ```

2. **设置虚拟环境**
   ```bash
   uv venv --python 3.12
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   uv pip install -e .
   ```

3. **构建前端（可选）**
   ```bash
   cd vibe_surf/frontend
   npm ci
   npm run build
   mkdir -p ../backend/frontend
   cp -r build/* ../backend/frontend/
   ```

4. **启动开发服务器**
   ```bash
   # 直接启动服务器
   uvicorn vibe_surf.backend.main:app --host 127.0.0.1 --port 9335

   # 或使用 CLI 命令
   uv run vibesurf
   ```

## 核心功能模块

### 1. 智能代理系统
- **多代理并行**: 支持同时在多个标签页运行不同代理
- **任务分发**: 智能分配任务给最适合的代理
- **协作机制**: 代理间可以共享信息和协作完成任务

### 2. 工作流引擎
- **可视化编辑**: 拖拽式工作流设计器
- **条件分支**: 支持基于条件的逻辑分支
- **循环控制**: 可配置的循环和迭代操作
- **错误处理**: 完善的错误捕获和恢复机制

### 3. 浏览器自动化
- **元素定位**: 智能元素识别和定位
- **交互模拟**: 点击、输入、滚动等用户操作模拟
- **页面导航**: 复杂的页面跳转和导航逻辑
- **数据提取**: 结构化数据提取和导出

### 4. 平台集成
- **社交媒体**: 小红书、抖音、微博、YouTube 等平台
- **生产力工具**: Gmail、Notion、Google Calendar、Slack 等
- **开发工具**: GitHub、Trello 等开发平台
- **自定义集成**: 支持添加自定义 API 集成

## 使用场景

### 1. 市场研究
- 自动化收集竞品信息
- 监控行业动态和趋势
- 生成分析报告和摘要

### 2. 内容管理
- 批量发布内容到多个平台
- 自动化内容审核和分类
- 定时发布和互动管理

### 3. 数据采集
- 网站数据批量抓取
- 结构化数据提取和存储
- 实时数据监控和更新

### 4. 工作自动化
- 自动登录和会话管理
- 表单填写和提交
- 报告生成和邮件发送

## API 设计

### REST API 端点
- `POST /api/agents/create`: 创建新的 AI 代理
- `POST /api/workflows/run`: 执行工作流
- `GET /api/browser/status`: 获取浏览器状态
- `POST /api/browser/navigate`: 导航到指定 URL
- `POST /api/tools/execute`: 执行工具操作
- `POST /api/skill/expose`: 配置工作流技能暴露
- `GET /api/skill/{flow_id}`: 获取工作流技能配置

### WebSocket 事件
- `agent:update`: 代理状态更新
- `workflow:progress`: 工作流执行进度
- `browser:screenshot`: 浏览器截图更新
- `system:notification`: 系统通知

## 配置管理

### 环境变量
```bash
# API 密钥
OPENAI_API_KEY=your_openai_key
GOOGLE_API_KEY=your_google_key
ANTHROPIC_API_KEY=your_anthropic_key

# 浏览器配置
BROWSER_HEADLESS=false
BROWSER_USER_DATA_DIR=/path/to/profile

# 服务器配置
HOST=127.0.0.1
PORT=9335
DEBUG=false
```

### 配置文件
主配置文件位于 `~/.vibesurf/config.yaml`，包含：
- 代理偏好设置
- 工作流模板
- 集成平台配置
- 性能优化参数

## 性能优化

### 1. 并发处理
- 使用异步 I/O 提高并发性能
- 智能资源调度和负载均衡
- 连接池和缓存机制

### 2. 内存管理
- 自动垃圾回收
- 内存使用监控
- 资源泄漏检测

### 3. 缓存策略
- 多级缓存架构
- 智能缓存失效
- 分布式缓存支持

## 监控与日志

### 1. 性能监控
- CPU、内存、网络使用率
- API 响应时间统计
- 错误率和成功率跟踪

### 2. 日志系统
- 结构化日志记录
- 日志级别过滤
- 日志轮转和归档

### 3. 遥测数据
- OpenTelemetry 集成
- Prometheus 指标导出
- 分布式链路追踪

## 安全考虑

### 1. 数据隐私
- 本地数据加密存储
- API 密钥安全管理
- 敏感信息脱敏

### 2. 访问控制
- 用户认证和授权
- API 访问限制
- 操作审计日志

### 3. 浏览器安全
- 沙箱隔离执行
- 恶意网站检测
- 内容安全策略

## 测试策略

### 1. 单元测试
- 核心功能模块测试
- Mock 外部依赖
- 边界条件测试

### 2. 集成测试
- API 端到端测试
- 浏览器自动化测试
- 第三方集成测试

### 3. 性能测试
- 负载测试和压力测试
- 内存泄漏检测
- 并发性能基准

## 部署方案

### 1. 本地部署
- 单机安装和运行
- Docker 容器化部署
- 系统服务配置

### 2. 云端部署
- AWS/GCP/Azure 部署
- Kubernetes 集群部署
- 自动扩缩容配置

### 3. 混合部署
- 本地+云端混合架构
- 数据同步和备份
- 灾难恢复方案

## 路线图

### 已完成 ✅
- [x] 智能技能系统（搜索、爬虫、代码执行）
- [x] 第三方平台集成（Composio）
- [x] 智能浏览器工作流
- [x] 工作流技能系统（技能暴露和管理）
- [x] 文件系统操作工作流
- [x] 知乎平台集成

### 进行中 🚧
- [ ] 强大的编程代理
- [ ] 智能记忆和个性化功能

### 计划中 📋
- [ ] 多语言支持
- [ ] 移动端支持
- [ ] 企业级功能
- [ ] 插件生态系统

## 贡献指南

### 1. 开发流程
1. Fork 项目仓库
2. 创建功能分支
3. 编写代码和测试
4. 提交 Pull Request
5. 代码审查和合并

### 2. 代码规范
- 遵循 PEP 8 Python 代码规范
- 使用 TypeScript 严格模式
- 编写完整的文档字符串
- 保持测试覆盖率 > 80%

### 3. 社区参与
- GitHub Issues: 报告 Bug 和功能请求
- Discord 社区: 技术讨论和交流
- 微信群: 中文用户交流

## 许可证

本项目采用 VibeSurf 开源许可证，基于 Apache 2.0 并附加额外条款。详见 [LICENSE](../LICENSE) 文件。

## 致谢

VibeSurf 基于以下优秀的开源项目：
- [Browser Use](https://github.com/browser-use/browser-use)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [Langflow](https://github.com/langflow-ai/langflow)

感谢所有贡献者和社区成员的支持！

---

## AI 使用建议

### 开发模式
1. **模块化开发**: 充分利用项目的模块化架构，专注于特定功能模块
2. **API 设计**: 遵循 RESTful 设计原则，保持 API 的一致性和可扩展性
3. **异步编程**: 大量使用 async/await 模式，提高并发性能
4. **测试驱动**: 编写全面的测试用例，确保代码质量

### 技术决策
1. **性能优先**: 在设计和实现中优先考虑性能影响
2. **可扩展性**: 预留扩展接口，支持未来功能增强
3. **用户体验**: 关注用户界面和交互体验的优化
4. **安全性**: 始终将数据安全和用户隐私放在首位

### 最佳实践
1. **代码复用**: 利用现有组件和工具，避免重复开发
2. **文档同步**: 保持代码和文档的同步更新
3. **版本管理**: 合理使用版本控制，便于协作和维护
4. **持续集成**: 建立 CI/CD 流水线，自动化测试和部署