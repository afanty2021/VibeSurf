# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

VibeSurf is an AI agentic browser built with Python (backend) and React/TypeScript (frontend). It combines browser automation with AI intelligence through a multi-agent system, visual workflow builder, and Chrome extension integration.

**Core Stack:**
- Backend: FastAPI, LangGraph/LangChain, browser-use, SQLAlchemy, Uvicorn
- Frontend: React 18, TypeScript, Vite, Tailwind CSS, XYFlow (ReactFlow)
- Browser: Chrome DevTools Protocol (CDP), Playwright
- Python: 3.11+ (recommended 3.12)
- Package Manager: uv (0.7.20+)

**Version Info:**
- Chrome Extension: 0.1.44.127
- Frontend (Langflow): 1.6.4

## Development Commands

### Backend Development

```bash
# Install dependencies (development mode)
uv venv --python 3.12
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows
uv pip install -e .

# Start backend server (option 1 - direct)
uvicorn vibe_surf.backend.main:app --host 127.0.0.1 --port 9335

# Start backend server (option 2 - CLI)
uv run vibesurf

# For production users (no install)
uvx vibesurf
```

### Frontend Development

```bash
cd vibe_surf/frontend

# Install dependencies
npm ci

# Development server (proxies to backend at port 7860)
npm start

# Build for production
npm run build

# Copy build to backend directory
mkdir -p ../backend/frontend
cp -r build/* ../backend/frontend/

# Run tests
npm test
npm run test:coverage
npm run test:watch

# Linting and formatting
npm run format              # Auto-fix with Biome
npm run check-format        # Check only
npm run type-check          # TypeScript type checking
```

### Database Migrations

VibeSurf uses Alembic for database migrations (Langflow integration):

```bash
# Location: vibe_surf/langflow/alembic/
# Migrations run automatically on backend startup
# Database: SQLite at {workspace}/langflow.db
```

## Architecture

### Multi-Agent System

VibeSurf orchestrates multiple AI agents using LangGraph state machines:

1. **VibeSurfAgent** (`vibe_surf/agents/vibe_surf_agent.py`)
   - Main orchestrator that coordinates multiple browser agents
   - Manages parallel execution across browser tabs
   - Built on LangGraph for state management

2. **BrowserUseAgent** (`vibe_surf/agents/browser_use_agent.py`)
   - Extends browser-use's Agent class
   - Handles individual browser automation tasks
   - Integrates custom tools and file system access

3. **ReportWriterAgent** (`vibe_surf/agents/report_writer_agent.py`)
   - Specialized for content summarization and report generation

### Backend API Structure

The FastAPI backend (`vibe_surf/backend/main.py`) is organized into routers:

- `/api/task` - Task execution and management
- `/api/agent` - Agent operations and lifecycle
- `/api/browser` - Browser control and session management
- `/api/config` - LLM and voice profile configuration
- `/api/composio` - Third-party app integrations (100+ tools)
- `/api/skill` - AI skills registry (search, crawl, code execution) + Workflow skill configuration
- `/api/tool` - Tool API for action search, parameter inspection, and execution
- `/api/vibesurf` - Core VibeSurf operations
- `/api/schedule` - Scheduled task management
- `/api/files` - File operations
- `/api/activity` - Activity logging
- `/api/voices` - Voice model (ASR/TTS) management

### Browser Architecture

**AgentBrowserSession** manages browser instances with:
- Chrome DevTools Protocol (CDP) for low-level control
- Profile isolation per agent
- Watchdog monitoring for health checks
- Extension loading (when Chrome version < 142)
- **Automatic tab cleanup** on task completion
- **Optimized CDP session management** (redundant calls removed)
- **Improved tab session handling** with better state tracking
- **Extended launch timeout**: 300 seconds for slower systems

**Extension Integration:**
- Location: `vibe_surf/chrome_extension/`
- Manifest V3 with side panel UI
- WebSocket communication with backend
- Background service worker + content scripts
- **i18n Support**: Multi-language support (English, Simplified Chinese)

### Internationalization (i18n)

**Chrome Extension Localization:**
- Location: `vibe_surf/chrome_extension/_locales/`
- Supported languages: `en` (English), `zh_CN` (Simplified Chinese)
- Auto-detection: IP-based language detection on first load
- Translation keys: Defined in `messages.json` for each locale
- Helper script: `vibe_surf/chrome_extension/scripts/i18n-helper.js`

**Adding New Translations:**
1. Create new locale directory: `_locales/{locale_code}/`
2. Add `messages.json` with translation keys
3. Update `manifest.json` `default_locale` if needed
4. Use `chrome.i18n.getMessage()` in JavaScript

**Example usage:**
```javascript
// In extension scripts
const title = chrome.i18n.getMessage("extensionName");
const description = chrome.i18n.getMessage("extensionDescription");
```

### Langflow Integration

VibeSurf embeds a fork of Langflow for visual workflow creation:

- Location: `vibe_surf/langflow/`
- 100+ pre-built components in `components/` directory
- Frontend at `vibe_surf/frontend/` (shared with VibeSurf UI)
- Database migrations in `alembic/`
- Component types: LLMs, agents, tools, data sources, embeddings

### Workflow System

Pre-built workflow templates in `vibe_surf/workflows/`:
- Categories: AIGC, Browser, FileSystem, Integrations, Recruitment, VibeSurf
- 80+ pre-built workflows available
- Combine deterministic automation with AI intelligence
- Minimize token consumption for repetitive tasks

**Workflow Skills**:
- Expose workflow inputs as configurable skills via API
- Filter exposable inputs (not connected, not internal types)
- Full UUID support for workflow identification
- Search and filtering capabilities for skill discovery

### Tools and Skills

**Core Tools** (`vibe_surf/tools/`):
- `browser_use_tools.py` - Browser automation primitives
- `vibesurf_tools.py` - Search, crawl, JS code execution
- `file_system.py` - File operations with custom API directory support
- `composio_client.py` - Integration with external apps
- `website_api/` - Native APIs for social platforms (Xiaohongshu, Douyin, Weibo, YouTube, Zhihu, NewsNow)
- `aigc/` - AI generation tools
- `finance_tools.py` - Financial analysis tools
- `voice_asr.py` - Voice recognition (ASR)

**Tool API** (`/api/tool`):
- `GET /search` - Search and filter actions by keyword from both vibesurf_tools and browser_use_tools
- `GET /{action_name}/params` - Get parameter schema for a specific action
- `POST /execute` - Execute an action with validated parameters
- Actions from browser_use_tools are prefixed with "browser." for disambiguation
- Automatic filtering of duplicate, internal, and unsafe actions

**Skills** are higher-level capabilities registered via `/api/skill`:
- `/search` - Quick information retrieval
- `/crawl` - Website data extraction
- `/code` - Execute JavaScript in browser context
- **Workflow Skills**: Expose workflow inputs as configurable skills with search and filtering

### Database Models

SQLAlchemy models (`vibe_surf/backend/database/models.py`):

- **Task**: Execution records with status (pending, running, paused, completed, failed, stopped)
- **LLMProfile**: LLM configurations with encrypted API keys
- **VoiceProfile**: ASR/TTS model configurations

Database location: `{workspace}/langflow.db` (SQLite)

### LLM Provider Support

Multi-provider architecture with unified interface:
- OpenAI, Anthropic, Google (Gemini), Azure OpenAI
- DeepSeek, Mistral, Ollama (local)
- Dashscope (Alibaba), Moonshot, SiliconFlow
- IBM WatsonX, Groq, Cohere, HuggingFace

Configuration via environment variables or LLMProfile database records.

**LLM Factory** (`vibe_surf/backend/utils/llm_factory.py`):
- Centralized LLM client creation
- Provider-specific configuration handling
- Support for custom API endpoints

## Environment Configuration

Create `.env` file based on `.env.example`:

**Critical Variables:**
- LLM API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.)
- `VIBESURF_BACKEND_PORT` - Backend server port (default: 9335)
- `VIBESURF_EXTENSION` - Path to Chrome extension
- `VIBESURF_WORKSPACE` - Data directory location
- `BROWSER_EXECUTION_PATH` - Browser executable path
- `ANONYMIZED_TELEMETRY` - Enable/disable telemetry (default: false)
- `BROWSER_USE_LOGGING_LEVEL` - Logging verbosity (result | info | debug)

**Configuration Priority:**
1. `{workspace}/envs.json` (runtime configuration)
2. Environment variables
3. Defaults in code

Workspace directory determined by `vibe_surf/common.py:get_workspace_dir()`.

## Key Implementation Patterns

### Agent State Management

Agents use LangGraph's StateGraph for execution flow:
- Nodes represent agent actions
- Edges define state transitions
- Checkpointers enable pause/resume
- Streaming for real-time updates

### Browser Session Lifecycle

```python
# 1. BrowserManager creates isolated profiles
# 2. AgentBrowserSession wraps CDP connection
# 3. Watchdog monitors health
# 4. Session cleanup on completion/failure
```

### Tool Integration

Tools follow LangChain's structured tool pattern:
- Type-hinted parameters with Pydantic models
- Async execution for I/O operations
- Error handling with context preservation

### Frontend-Backend Communication

- REST API for CRUD operations
- WebSocket for streaming agent outputs
- Server-Sent Events (SSE) for workflow execution updates

### Welcome Flow

**New User Onboarding:**
- Welcome modal with feature introduction
- GitHub star prompt modal
- IP-based language auto-detection
- Settings guidance for first-time setup

**Location**: `vibe_surf/browser/welcome_modal_content.py`

## Common Workflows

### Using the Tool API

The Tool API provides programmatic access to browser and VibeSurf actions:

```bash
# Search for available actions
curl "http://localhost:9335/api/tool/search?keyword=screenshot"

# Get parameter schema for a specific action
curl "http://localhost:9335/api/tool/browser.screenshot/params"

# Execute an action with parameters
curl -X POST "http://localhost:9335/api/tool/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "action_name": "browser.screenshot",
    "parameters": {}
  }'
```

**Action Naming Convention:**
- VibeSurf actions: `action_name` (e.g., `take_and_save_screenshot`)
- Browser actions: `browser.action_name` (e.g., `browser.screenshot`)

### Configuring Workflow Skills

Expose workflow inputs as configurable skills:

1. **Create a workflow** with input nodes
2. **Configure skill exposure**:
   ```bash
   curl -X POST "http://localhost:9335/api/skill/expose" \
     -H "Content-Type: application/json" \
     -d '{
       "flow_id": "workflow-uuid",
       "add_to_skill": true,
       "workflow_expose_config": {
         "input_field_1": true,
         "input_field_2": false
       }
     }'
   ```
3. **Use the skill** through agent or direct API calls

### Adding a New LLM Provider

1. Create provider client in `vibe_surf/llm/`
2. Add to LLMProfile enum in `vibe_surf/backend/database/models.py`
3. Update provider factory in `vibe_surf/backend/utils/llm_factory.py`
4. Add API key to `.env.example`

### Creating a Custom Tool

1. Define tool in `vibe_surf/tools/`
2. Implement async function with Pydantic model for parameters
3. Register with `@tool` decorator (LangChain)
4. Add to agent's tool list in `vibe_surf/agents/`

### Building a New Workflow Template

1. Create workflow JSON in `vibe_surf/workflows/{category}/`
2. Use Langflow components from `vibe_surf/langflow/components/`
3. Test in workflow builder UI
4. Export and commit workflow file
5. Optionally expose as a skill via `/api/skill/expose`

### Adding Extension i18n Support

1. Add translation key to `_locales/en/messages.json`
2. Add translation to `_locales/zh_CN/messages.json`
3. Use `chrome.i18n.getMessage("keyName")` in scripts
4. Test extension in different languages

## Testing

**Frontend Tests:**
```bash
cd vibe_surf/frontend
npm test                    # Run Jest tests
npm run test:coverage       # With coverage report
npm run test:watch          # Watch mode
```

**Backend Tests:**
```bash
# Run specific test files
pytest tests/test_agents.py
pytest tests/test_aigc_tools.py
```

## Platform-Specific Notes

**Windows:**
- DLL dependencies for torch/onnxruntime: Install [Visual C++ Redistributable](https://aka.ms/vc14/vc_redist.x64.exe)
- One-click installer available: `VibeSurf-Installer.exe`
- Use backslash paths or raw strings for file operations

**Chrome Extension Loading:**
- Chrome 142+ removed `--load-extension` flag
- Manual loading required: chrome://extensions → Developer mode → Load unpacked
- Extension location: `vibe_surf/chrome_extension/`

**Docker:**
- Set `IN_DOCKER=true` for optimized browser configuration
- Playwright browsers need proper installation in container

**macOS:**
- torch on Mac Intel requires specific configuration
- Recent fix: commit f9c498a "fix torch on mac intel"

## Debugging

**Backend Debug Mode:**
```bash
# Enable verbose logging
export VIBESURF_DEBUG=true
export BROWSER_USE_LOGGING_LEVEL=debug

# Start with debugger support
python -m pdb -m vibe_surf.cli
```

**Frontend Debug:**
- React DevTools for component inspection
- Network tab for API calls (proxied to backend)
- Console for workflow execution logs

**Browser Automation:**
- Set `BROWSER_USE_LOGGING_LEVEL=debug` for detailed browser actions
- CDP messages logged when debug enabled
- Browser stays open on error for inspection

## Package Structure

```
vibe_surf/
├── agents/              # AI agent implementations
├── backend/             # FastAPI server
│   ├── api/            # API routers (task, agent, browser, tool, skill, etc.)
│   ├── database/       # SQLAlchemy models and queries
│   ├── utils/         # Utility functions (encryption, llm_factory)
│   └── frontend/       # Built React app (copied from vibe_surf/frontend/build)
├── browser/            # Browser management
│   └── welcome_modal_content.py  # Welcome flow content
├── chrome_extension/   # Chrome extension (Manifest V3)
│   ├── _locales/      # i18n translations (en, zh_CN)
│   ├── scripts/       # Extension scripts
│   │   ├── i18n-helper.js     # i18n utilities
│   │   └── ...
│   └── styles/        # Extension styles
├── frontend/           # React TypeScript app (source)
├── langflow/          # Workflow builder (Langflow fork)
│   ├── alembic/       # Database migrations
│   ├── components/    # 100+ workflow components
│   └── services/      # Langflow backend services
├── llm/               # LLM provider integrations
├── tools/             # Agent tools
│   ├── aigc/         # AI generation tools
│   ├── website_api/   # Platform-specific APIs
│   ├── browser_use_tools.py  # Browser automation primitives
│   ├── vibesurf_tools.py     # VibeSurf search/crawl/code tools
│   ├── file_system.py        # File operations with API directory
│   ├── finance_tools.py      # Financial analysis tools
│   ├── voice_asr.py          # Voice recognition
│   └── views.py              # Action models and views
├── workflows/         # Pre-built workflow templates (80+)
│   ├── AIGC/
│   ├── Browser/
│   ├── FileSystem/
│   ├── Integrations/
│   ├── Recruitment/    # NEW: Recruitment workflows
│   └── VibeSurf/
├── cli.py            # CLI entry point
└── common.py         # Shared utilities
```

## Documentation

- **English Guide**: See `README.md`
- **Chinese Guide**: See `PROJECT_GUIDE_CN.md` and `README_zh.md`
- **API Documentation**: Auto-generated by FastAPI at `/docs` endpoint

## Telemetry

VibeSurf collects anonymous usage data by default for product improvement:
- CLI startup events
- Agent execution metrics
- Error reporting via Sentry (if configured)

**Disable:**
```bash
export ANONYMIZED_TELEMETRY=false
# or in .env
ANONYMIZED_TELEMETRY=false
```

## Version Management

- Version determined by git tags via `setuptools-scm`
- Written to `vibe_surf/_version.py` on build
- CLI displays version from `vibe_surf.__version__`

## Recent Changes (2025-12 → 2026-01)

### Tool API Enhancements
- **New Tool API endpoints** (`/api/tool`):
  - Action search with keyword filtering
  - Parameter schema inspection for any action
  - Direct action execution with validation
- Browser actions prefixed with "browser." for clarity
- Smart filtering of duplicate and unsafe actions
- Custom API directory support at `{workspace}/apis`

### Workflow Skills System
- Expose workflow inputs as configurable skills
- Input filtering based on connection status and type
- Full UUID support instead of short IDs
- Search and filtering for skill discovery
- Validation of exposable inputs (no underscore prefixes, excludes HandleInput)

### Browser Session Management
- **Automatic tab cleanup** on task completion
- **Refactored CDP session calls** - removed redundant operations
- **Improved tab session handling** with better state tracking
- **Extended browser launch timeout** to 300 seconds
- Enhanced screenshot and input tools
- Browser paste text workflow component added

### Internationalization (i18n)
- Added Chrome extension i18n support for English and Simplified Chinese
- IP-based language auto-detection for new users
- Translation files in `_locales/` directory
- i18n helper utilities for extension scripts
- Improved modal and dialog translations

### UI Improvements
- GitHub star prompt modal in welcome flow
- **WeChat social link** with QR code popup in extension
- Improved settings panels with better organization
- Enhanced permission request UI
- Better modal management and news carousel
- Responsive form input fixes

### Backend Enhancements
- Improved VibeSurf API with better task management
- Enhanced LLM factory with provider-specific configuration
- Improved encryption utilities for API keys
- Streamlined browser session management
- Better proxy configuration support

### Error Handling
- **Improved YouTube transcript error handling**
- Enhanced API result processing
- Better error messages and logging

### Testing
- Added AIGC tools tests
- Improved agent tests coverage

### Documentation
- Added comprehensive Chinese project guide (`PROJECT_GUIDE_CN.md`)
- Updated README files with latest features
- Improved i18n translation coverage
- Updated AI context documentation (this file)

### New Workflow Category
- **Recruitment** workflows added
- Expanded workflow template library

## Contributing

When contributing to VibeSurf:
1. Follow existing code patterns and architecture
2. Add i18n strings for any new UI text
3. Update tests for new features
4. Ensure cross-platform compatibility (Windows, macOS, Linux)
5. Document new tools and workflows

## License

Apache-2.0 License - See LICENSE file for details
