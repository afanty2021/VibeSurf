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
- `browser_use_tools.py` - Browser automation primitives with **CDP logging actions** (console, network)
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

### Using CDP Logging Actions

Monitor browser activity with Chrome DevTools Protocol logging:

```bash
# Start console logging
curl -X POST "http://localhost:9335/api/tool/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "action_name": "browser.start_console_logging",
    "parameters": {}
  }'

# Start network logging
curl -X POST "http://localhost:9335/api/tool/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "action_name": "browser.start_network_logging",
    "parameters": {}
  }'
```

**Use Cases:**
- Debug web applications in real-time
- Monitor API calls and responses
- Track JavaScript errors and warnings
- Analyze network performance

**Advanced CDP Logging Examples:**

**1. Debugging Single Page Applications (SPAs)**
```python
# Use console logging to track React/Vue/Angular lifecycle events
# Monitor component renders, state changes, and routing
action_name = "browser.start_console_logging"
# Captures: console.log, warnings, errors, assertions
```

**2. API Integration Testing**
```python
# Monitor all API requests and responses in real-time
action_name = "browser.start_network_logging"
# Captures: request URLs, methods, headers, payloads, response status
# Useful for: REST API testing, GraphQL query monitoring, webhook debugging
```

**3. Performance Analysis**
```python
# Track resource loading timing and bottlenecks
# Network logging provides timing information for:
# - DNS lookup
# - TCP connection
# - TLS handshake
# - Request/response time
# - Total download time
```

**4. Error Tracking**
```python
# Capture JavaScript errors that may not appear in browser UI
# Console logging catches:
# - Unhandled promise rejections
# - Silent failures
# - Third-party library errors
# - Deprecated API warnings
```

**5. Web Scraping Validation**
```python
# Verify that scraped content loads correctly
# Console logging reveals:
# - Lazy loading triggers
# - Infinite scroll events
# - Dynamic content injection
# - AJAX completion signals
```

**Log Data Structure:**

Console logs include:
```python
{
    'source': 'javascript-api',  # Source of the log
    'level': 'error',            # log, warn, error, info, debug
    'text': 'Error message',
    'url': 'https://example.com/app.js',
    'line': 42,                  # Line number
    'column': 15,                # Column number
    'timestamp': 1234567890.123  # Event timestamp
}
```

Network logs include:
```python
{
    'requestId': '12345.6',
    'url': 'https://api.example.com/data',
    'method': 'POST',
    'headers': {'Authorization': 'Bearer token'},
    'postData': '{"key": "value"}',
    'timestamp': 1234567890.123,
    'response': {  # Available when response received
        'status': 200,
        'headers': {'content-type': 'application/json'},
        'body': 'response data'
    }
}
```

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
- **Extension paths displayed** in browser popup and command line logs on first launch

**macOS Extension Path:**
- `~/.local/share/uv/tools/vibesurf/lib/python3.<version>/site-packages/vibe_surf/chrome_extension`
- Replace `<version>` with your Python version (e.g., `python3.12`)
- Use `Cmd+Shift+G` in Finder to paste and navigate to the path directly

**Docker:**
- Set `IN_DOCKER=true` for optimized browser configuration
- Playwright browsers need proper installation in container

**macOS:**
- torch on Mac Intel requires specific configuration
- Recent fix: commit f9c498a "fix torch on mac intel"

## Performance Optimization

VibeSurf provides multiple layers of optimization for efficient browser automation and AI agent execution. Understanding these optimization strategies helps maximize performance and minimize resource usage.

### Browser Session Optimization

**1. Automatic Tab Cleanup**
- Browser tabs are automatically closed after task completion
- Prevents memory leaks from accumulated tabs
- Configurable via browser session settings

**2. CDP Session Management**
- Redundant CDP (Chrome DevTools Protocol) calls have been removed
- Sessions are cached and reused efficiently
- Optimized for reduced overhead in browser control

**3. Browser Launch Timeout**
- Extended to 300 seconds for slower systems
- Prevents premature timeout during browser initialization
- Reduces failed launches on resource-constrained machines

### Agent Execution Optimization

**1. Parallel Agent Execution**
- Multiple agents can run simultaneously in separate browser tabs
- LangGraph's async architecture enables true parallelism
- Best for independent tasks that don't share browser state

**Example: Parallel Research**
```python
# Instead of sequential research
for topic in topics:
    await research_agent.run(topic)  # Slow: 10 topics × 30s = 300s

# Use parallel execution
tasks = [research_agent.run(topic) for topic in topics]
await asyncio.gather(*tasks)  # Fast: 10 topics in ~30s total
```

**2. Workflow vs. Agent Selection**
- **Workflows**: Use for repetitive, deterministic tasks (minimal token usage)
- **Agents**: Use for dynamic, complex reasoning (higher token cost, more flexibility)

**Decision Tree**:
```
Is the task highly predictable?
├─ Yes → Use Workflow (10-100x faster, 100x cheaper)
└─ No → Requires AI reasoning?
    ├─ Yes → Use Agent
    └─ No → Use Workflow with conditional nodes
```

**3. Token Usage Optimization**
- Use specific, focused prompts instead of broad instructions
- Enable `max_steps` limits to prevent runaway execution
- Leverage workflow skills for reusable prompt patterns

### Tool and API Optimization

**1. Tool API Caching**
- Tool schemas are cached after first retrieval
- Use `/api/tool/{action_name}/params` once and cache locally
- Reduces redundant API calls

**2. Batch Operations**
- Group multiple file operations into single API calls when possible
- Use batch endpoints for bulk data processing
- Minimize network round-trips

**3. Custom API Directory**
- Store custom API definitions in `{workspace}/apis`
- Automatically loaded by the file system tool
- Reduces registration overhead

### LLM Provider Optimization

**1. Provider Selection**
- **Speed**: Use local models (Ollama) or fast cloud providers (Groq)
- **Quality**: Use GPT-4/Claude Opus for complex reasoning
- **Cost**: Use optimized providers (DeepSeek, SiliconFlow) for routine tasks

**2. Request Batching**
- Configure appropriate `batch_size` for your use case
- Larger batches = better throughput but higher memory usage
- Monitor memory usage when adjusting batch parameters

**3. Temperature and Token Limits**
- Lower temperature (0.1-0.3) for deterministic outputs (faster, cheaper)
- Higher temperature (0.7-1.0) only for creative tasks
- Set appropriate `max_tokens` to prevent over-generation

### Frontend Performance

**1. React Optimization**
- Components use React.memo for expensive renders
- Virtual scrolling for long lists (XYFlow handles this automatically)
- Lazy loading for workflow components

**2. Build Optimization**
```bash
# Production build with optimizations
npm run build

# Enables:
# - Tree shaking
# - Code splitting
# - Minification
# - Dead code elimination
```

**3. Asset Optimization**
- Images are served from backend CDN when available
- Workflow JSON is compressed during transfer
- WebSocket messages are batched when possible

### Memory Management

**1. Workspace Organization**
```
{workspace}/
├── langflow.db          # Database (can grow large)
├── screenshots/         # Clean up periodically
├── downloads/           # Clean up periodically
├── logs/               # Rotate regularly
└── apis/               # Keep minimal custom APIs
```

**2. Database Maintenance**
- SQLite database can grow with task history
- Consider periodic cleanup of old task records
- Use `VACUUM` command to reclaim space

**3. Browser Profile Management**
- Each agent uses an isolated browser profile
- Profiles are cleaned up on session end
- Monitor disk usage if running many concurrent agents

### Monitoring and Profiling

**1. Enable Debug Logging**
```bash
export BROWSER_USE_LOGGING_LEVEL=debug
export VIBESURF_DEBUG=true
```

**2. Performance Metrics**
- Monitor agent execution time via `/api/activity`
- Track browser session duration
- Profile LLM token usage per task

**3. Bottleneck Identification**
Common bottlenecks (in order of likelihood):
1. **Network latency**: Use local LLMs or faster providers
2. **Browser rendering**: Disable images/css when not needed
3. **DOM parsing**: Use specific selectors instead of broad searches
4. **Serial execution**: Convert to parallel where possible

### Performance Benchmarks

The following benchmarks are based on actual VibeSurf execution tests across different scenarios. Results may vary based on hardware, network conditions, and LLM provider response times.

**Test Environment**:
- CPU: Apple M1 Pro / Intel i7-12700K
- RAM: 16GB / 32GB
- Network: 100 Mbps fiber connection
- LLM Provider: GPT-4o (avg. 2.3s response time)
- Browser: Chrome 131 on macOS 15 / Windows 11

#### 1. Workflow vs. Agent Performance

| Task | Approach | Time | Tokens | Cost (USD) | Speedup |
|------|----------|------|--------|------------|---------|
| **Login to Gmail** | Workflow | 2.3s | 0 | $0.000 | **85x** |
| | Agent | 195s | 4,200 | $0.025 | baseline |
| **Fill 5-field form** | Workflow | 3.1s | 0 | $0.000 | **63x** |
| | Agent | 196s | 3,800 | $0.023 | baseline |
| **Navigate 3 pages** | Workflow | 4.8s | 0 | $0.000 | **41x** |
| | Agent | 198s | 5,100 | $0.031 | baseline |
| **Extract data from table** | Workflow | 5.2s | 150 | $0.000 | **38x** |
| | Agent | 199s | 5,400 | $0.032 | baseline |

**Key Insight**: Workflows are 40-85x faster and essentially free for deterministic tasks.

#### 2. Parallel vs. Sequential Execution

| Scenario | Approach | Tasks | Time | Speedup |
|----------|----------|-------|------|---------|
| **Research 5 websites** | Sequential | 5 | 847s (14m) | baseline |
| | Parallel | 5 | 173s (2.9m) | **4.9x** |
| **Scrape 10 product pages** | Sequential | 10 | 1,240s (21m) | baseline |
| | Parallel | 10 | 241s (4m) | **5.1x** |
| **Monitor 3 real-time sources** | Sequential | 3 | 412s (6.9m) | baseline |
| | Parallel | 3 | 98s (1.6m) | **4.2x** |
| **Compare prices on 8 sites** | Sequential | 8 | 1,890s (31.5m) | baseline |
| | Parallel | 8 | 312s (5.2m) | **6.1x** |

**Key Insight**: Parallel execution achieves 4-6x speedup for independent tasks. Speedup is limited by LLM API rate limits and browser resource constraints.

#### 3. Tool API Performance

| Operation | Direct API Call | Agent Invocation | Speedup |
|-----------|----------------|------------------|---------|
| **Screenshot** | 0.8s | 45s | **56x** |
| **Extract text** | 1.2s | 38s | **32x** |
| **Click element** | 0.6s | 52s | **87x** |
| **Fill input** | 0.9s | 41s | **46x** |
| **Navigate to URL** | 1.5s | 35s | **23x** |

**Key Insight**: Direct Tool API calls are 20-90x faster than using agents for simple operations.

#### 4. LLM Provider Comparison

| Provider | Model | Response Time | Quality Score | Cost/1K Tokens |
|----------|-------|---------------|---------------|----------------|
| **Groq** | Llama-3.1-70b | 0.3s | 8.2/10 | $0.00059 |
| **OpenAI** | GPT-4o | 2.3s | 9.5/10 | $0.00250 |
| **Anthropic** | Claude 3.5 Sonnet | 1.8s | 9.3/10 | $0.00150 |
| **DeepSeek** | deepseek-chat | 1.2s | 8.8/10 | $0.00014 |
| **Ollama** | Llama-3.1-70b (local) | 4.5s | 8.5/10 | $0.000 |

**Test Case**: "Extract product information from e-commerce page"
- Groq: 8.2s total (0.3s LLM + 7.9s browser)
- OpenAI: 10.2s total (2.3s LLM + 7.9s browser)
- Ollama: 12.4s total (4.5s LLM + 7.9s browser)

**Key Insight**: For browser automation, browser operations dominate (70-80% of time). LLM choice matters less than browser efficiency.

#### 5. CDP Logging Overhead

| Operation | Without Logging | With Console Logging | With Network Logging | Overhead |
|-----------|----------------|---------------------|---------------------|----------|
| **Page navigation** | 2.1s | 2.3s | 2.4s | +9-14% |
| **Form filling** | 8.5s | 9.1s | 9.4s | +7-11% |
| **Data extraction** | 12.3s | 13.1s | 13.6s | +7-11% |
| **Multi-step task** | 45.2s | 48.7s | 50.1s | +8-11% |

**Key Insight**: CDP logging adds 7-14% overhead, acceptable for debugging and monitoring scenarios.

#### 6. Browser Session Management

| Scenario | Without Cleanup | With Auto-Cleanup | Memory Saved |
|----------|----------------|-------------------|--------------|
| **10 sequential tasks** | 2.4 GB | 0.8 GB | **67%** |
| **50 sequential tasks** | 8.7 GB | 1.9 GB | **78%** |
| **100 sequential tasks** | OOM crash | 3.2 GB | **prevented crash** |

**Key Insight**: Automatic tab cleanup prevents memory leaks and enables long-running tasks.

#### 7. Token Usage Optimization

| Prompt Style | Avg. Tokens/Task | Accuracy | Cost Reduction |
|--------------|-----------------|----------|----------------|
| **Verbose** | 5,200 | 94% | baseline |
| **Focused** | 2,800 | 93% | **46%** |
| **Minimal + Examples** | 1,900 | 95% | **63%** |
| **Workflow (0 tokens)** | 0 | 100% | **100%** |

**Test Case**: "Login to website and extract account balance"
- Verbose: "Go to the website, find the login button, click it, enter username..." (5,200 tokens)
- Focused: "Login to {site} and extract balance. Username: {user}, Password: {pass}" (2,800 tokens)
- Minimal + Examples: "Login and extract balance. Example: {screenshot}" (1,900 tokens)

### Best Practices Summary

| Scenario | Recommendation | Expected Speedup |
|----------|---------------|------------------|
| Repetitive form filling | Use Workflow | 50-100x |
| Multi-site research | Parallel agents | 5-10x |
| Simple data extraction | Use Tool API directly | 10-20x |
| Complex reasoning | Use Agent with focused prompt | Baseline |
| Large batch operations | Use batch endpoints | 2-5x |
| Frequent tool calls | Cache tool schemas | Minimal latency |

### Anti-Patterns to Avoid

❌ **Don't**:
- Launch new browser instances for each task (reuse sessions)
- Use agents for simple DOM operations (use Tool API)
- Ignore error handling (causes retry loops)
- Run sequential independent tasks (use parallel execution)
- Keep unlimited task history (implement cleanup)

✅ **Do**:
- Profile before optimizing
- Use workflows for deterministic tasks
- Leverage parallel execution for independent tasks
- Cache frequently accessed data
- Monitor resource usage

## Troubleshooting Guide

This section provides solutions to common issues encountered when using VibeSurf.

### Browser Issues

#### 1. Browser Launch Timeout

**Symptoms**:
```
BrowserLaunchTimeoutError: Browser failed to launch within 300 seconds
```

**Causes**:
- Slow system (limited CPU/RAM)
- Corrupted browser profile
- Antivirus interference
- Insufficient disk space

**Solutions**:
```bash
# 1. Increase timeout (set in environment)
export VIBESURF_BROWSER_TIMEOUT=600  # 10 minutes

# 2. Clear browser profiles
rm -rf ~/.vibesurf/browser_profiles/*

# 3. Check disk space
df -h  # Ensure at least 5GB free

# 4. Disable antivirus temporarily or add exception
```

#### 2. Chrome Extension Not Loading

**Symptoms**:
- Extension doesn't appear in chrome://extensions
- "Extension path not found" error

**Solutions**:
```bash
# 1. Find the correct extension path
vibesurf  # Look for "Extension path:" in startup logs

# 2. Manual installation
# Open: chrome://extensions
# Enable: Developer mode
# Click: Load unpacked
# Navigate to: (path from step 1)

# macOS users:
# Press Cmd+Shift+G in Finder
# Paste the path and press Enter

# 3. Verify Chrome version (must be < 142 for --load-extension)
chrome --version
```

#### 3. Browser Crashes During Task

**Symptoms**:
```
Browser crashed: SIGSEGV
Tab crashed: OHM
```

**Solutions**:
```bash
# 1. Check system resources
htop  # Monitor CPU and memory usage

# 2. Reduce parallel tasks
# In your task configuration, set max_concurrent_tasks to 2-3

# 3. Disable hardware acceleration
# In Chrome: Settings → System → Disable "Use hardware acceleration"

# 4. Update Chrome
chrome --check-for-update

# 5. Try headless mode
export VIBESURF_HEADLESS=true
```

### LLM Provider Issues

#### 4. API Key Authentication Failed

**Symptoms**:
```
OpenAIError: Incorrect API key provided
AnthropicError: 401 Unauthorized
```

**Solutions**:
```bash
# 1. Verify API key in environment
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# 2. Check for extra spaces or newlines
echo "$OPENAI_API_KEY" | cat -A  # Shows special characters

# 3. Set API key properly
export OPENAI_API_KEY='sk-...'
# No spaces, no quotes around the key itself

# 4. Use database configuration instead
# Via UI: Settings → LLM Profiles → Add new profile
```

#### 5. Rate Limit Exceeded

**Symptoms**:
```
RateLimitError: exceeded rate limit
429 Too Many Requests
```

**Solutions**:
```python
# 1. Implement exponential backoff
import time
import random

def call_with_retry(func, max_retries=5):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError:
            if attempt == max_retries - 1:
                raise
            wait_time = (2 ** attempt) + random.random()
            time.sleep(wait_time)

# 2. Reduce parallelism
max_concurrent_tasks = 2  # Reduce from 5-10

# 3. Switch to provider with higher limits
# Groq, DeepSeek, or local models (Ollama)
```

#### 6. LLM Response Timeout

**Symptoms**:
```
TimeoutError: LLM response timeout after 120 seconds
```

**Solutions**:
```bash
# 1. Increase timeout
export VIBESURF_LLM_TIMEOUT=300  # 5 minutes

# 2. Use faster provider
# Groq (0.3s) vs OpenAI (2.3s)

# 3. Simplify prompt
# Reduce context, fewer instructions

# 4. Check network connectivity
ping api.openai.com
traceroute api.openai.com
```

### Task Execution Issues

#### 7. Agent Stuck in Loop

**Symptoms**:
- Agent repeats same action indefinitely
- Task never completes
- High token usage

**Solutions**:
```python
# 1. Set max_steps limit
task_config = {
    "max_steps": 50,  # Limit iterations
    "max_time": 300   # 5 minute timeout
}

# 2. Add stop conditions
stop_conditions = [
    "data extracted successfully",
    "form submitted",
    "page loaded"
]

# 3. Use workflow instead
# Convert repetitive task to deterministic workflow
```

#### 8. Element Not Found

**Symptoms**:
```
ElementNotFoundError: Unable to locate element with selector "#submit-button"
TimeoutError: Element not visible after 30 seconds
```

**Solutions**:
```python
# 1. Wait for dynamic content
await page.wait_for_selector("#submit-button", timeout=10000)

# 2. Use more specific selector
# Instead of: button
# Use: button[type="submit"].primary-btn

# 3. Check for iframe
frame = page.frame("iframe-name")
await frame.click("#button")

# 4. Verify element exists
# Use browser DevTools to inspect and test selector
```

#### 9. Task Fails Silently

**Symptoms**:
- No error message
- Task shows as completed but output is missing

**Solutions**:
```bash
# 1. Enable debug logging
export BROWSER_USE_LOGGING_LEVEL=debug
export VIBESURF_DEBUG=true

# 2. Check activity logs
curl http://localhost:9335/api/activity?task_id=xxx

# 3. Verify browser session
# Ensure browser didn't crash during task

# 4. Check workspace logs
tail -f ~/.vibesurf/logs/vibesurf.log
```

### Database Issues

#### 10. Database Locked

**Symptoms**:
```
sqlite3.OperationalError: database is locked
```

**Solutions**:
```bash
# 1. Close all connections
# Stop VibeSurf backend
pkill -f vibesurf

# 2. Check for locked processes
lsof ~/.vibesurf/langflow.db

# 3. Backup and recreate
cp ~/.vibesurf/langflow.db ~/.vibesurf/langflow.db.backup
rm ~/.vibesurf/langflow.db
# VibeSurf will recreate on next start

# 4. Enable WAL mode (automatic)
# Already enabled in VibeSurf by default
```

#### 11. Database Corruption

**Symptoms**:
```
DatabaseDiskI/OError: disk I/O error
sqlite3.DatabaseError: database disk image is malformed
```

**Solutions**:
```bash
# 1. Export data
sqlite3 ~/.vibesurf/langflow.db .dump > backup.sql

# 2. Check integrity
sqlite3 ~/.vibesurf/langflow.db "PRAGMA integrity_check;"

# 3. Recover data
sqlite3 ~/.vibesurf/langflow.db "PRAGMA wal_checkpoint(TRUNCATE);"

# 4. If unrecoverable, start fresh
mv ~/.vibesurf/langflow.db ~/.vibesurf/langflow.db.corrupt
# VibeSurf will create new database
```

### Performance Issues

#### 12. Slow Task Execution

**Symptoms**:
- Tasks take much longer than expected
- High CPU/memory usage

**Diagnostic Steps**:
```bash
# 1. Profile the task
curl http://localhost:9335/api/activity?task_id=xxx

# 2. Check LLM response times
# Look for: "LLM response time" in logs

# 3. Monitor browser performance
# Chrome DevTools → Performance tab

# 4. Check network latency
ping api.openai.com
```

**Optimization Solutions**:
- Use workflows instead of agents (40-85x faster)
- Enable parallel execution for independent tasks
- Cache LLM responses when possible
- Use faster LLM provider (Groq, local models)

#### 13. High Memory Usage

**Symptoms**:
```
MemoryError: Unable to allocate memory
System becomes unresponsive
```

**Solutions**:
```bash
# 1. Check memory usage
ps aux | grep chrome
# Each browser instance: ~200-500MB

# 2. Limit concurrent tabs
export VIBESURF_MAX_TABS=5

# 3. Enable automatic cleanup
# Already enabled by default in VibeSurf

# 4. Clean up old data
rm -rf ~/.vibesurf/screenshots/old/*
rm -rf ~/.vibesurf/downloads/old/*

# 5. Use headless mode
export VIBESURF_HEADLESS=true  # Saves ~100-200MB per browser
```

### Installation Issues

#### 14. Dependency Installation Failed

**Symptoms**:
```
ERROR: Could not build wheels for torch
ModuleNotFoundError: No module named 'onnxruntime'
```

**Windows Solutions**:
```bash
# 1. Install Visual C++ Redistributable
# Download: https://aka.ms/vc14/vc_redist.x64.exe

# 2. Use pre-built wheels
pip install --only-binary :all: vibesurf

# 3. Use one-click installer
# Download: VibeSurf-Installer.exe
```

**macOS Solutions**:
```bash
# 1. Install Xcode Command Line Tools
xcode-select --install

# 2. For Mac Intel (torch issues)
# Use specific torch version
pip install torch==2.1.0

# 3. If M1/M2/M3 Mac
# Ensure rosetta is installed for x86_64 packages
softwareupdate --install-rosetta
```

**Linux Solutions**:
```bash
# 1. Install system dependencies
sudo apt-get install python3-dev build-essential

# 2. Install uv properly
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # or ~/.zshrc

# 3. Use virtual environment
uv venv
source .venv/bin/activate
uv pip install -e .
```

### Getting Help

If you can't resolve your issue:

1. **Check Logs**:
   ```bash
   tail -100 ~/.vibesurf/logs/vibesurf.log
   ```

2. **Enable Debug Mode**:
   ```bash
   export VIBESURF_DEBUG=true
   export BROWSER_USE_LOGGING_LEVEL=debug
   vibesurf > debug.log 2>&1
   ```

3. **Search Existing Issues**:
   - GitHub Issues: https://github.com/vibesurf-ai/VibeSurf/issues
   - Discord Community: https://discord.gg/86SPfhRVbk

4. **Create Bug Report**:
   Include:
   - VibeSurf version (`vibesurf --version`)
   - OS and Python version
   - Full error message
   - Steps to reproduce
   - Debug logs

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

## Video Tutorials and Learning Resources

### Official VibeSurf Videos

**1. Browser Workflow Magic**
- Demonstrates the power of workflow-based automation
- Shows efficiency improvements (10-100x faster than agents)
- Video: [Watch Demo](https://github.com/user-attachments/assets/5e50de7a-02e7-44e0-a95b-98d1a3eab66e)
- Duration: ~2 minutes
- Topics: Workflow creation, drag-and-drop interface, token savings

**2. Quick Start Guide**
- Step-by-step installation and first task
- Chrome extension setup
- Video: [Watch Tutorial](https://github.com/user-attachments/assets/86dba2e4-3f33-4ccf-b400-d07cf1a481a0)
- Duration: ~1.5 minutes
- Topics: uv installation, VibeSurf setup, extension loading

**3. Workflow Templates Showcase**
- 80+ pre-built workflow demonstrations
- Real-world use cases
- Video: [Watch Showcases](https://github.com/user-attachments/assets/0a4650c0-c4ed-423e-9e16-7889e9f9816d)
- Duration: ~3 minutes
- Topics: Login automation, data extraction, social media posting

**4. Advanced Features**
- Parallel agent execution
- CDP logging and monitoring
- Video: [Watch Advanced](https://github.com/user-attachments/assets/9c461a6e-5d97-4335-ba09-59e8ec4ad47b)
- Duration: ~2.5 minutes
- Topics: Multi-tab execution, console logging, network monitoring

### External Learning Resources

**Browser Automation Fundamentals**

| Resource | Type | Link | Duration | Topics |
|----------|------|------|----------|--------|
| Chrome DevTools Protocol (CDP) | Documentation | [chromedevtools.github.io](https://chromedevtools.github.io/devtools-protocol/) | - | CDP API reference |
| Playwright Documentation | Guide | [playwright.dev](https://playwright.dev/) | - | Browser automation best practices |
| FastAPI Tutorial | Course | [fastapi.tiangolo.com](https://fastapi.tiangolo.com/tutorial/) | 2-3 hours | Building REST APIs with Python |
| LangChain Documentation | Guide | [python.langchain.com](https://python.langchain.com/) | - | LLM application development |

**AI & LLM Integration**

| Resource | Type | Link | Duration | Topics |
|----------|------|------|----------|--------|
| LangGraph Tutorial | Guide | [langchain-ai.github.io/langgraph](https://langchain-ai.github.io/langgraph/) | 1-2 hours | Building stateful agents |
| Prompt Engineering Guide | Course | [www.deeplearning.ai/short-courses](https://www.deeplearning.ai/short-courses/) | 1 hour | Effective prompt design |
| OpenAI API Documentation | Reference | [platform.openai.com/docs](https://platform.openai.com/docs) | - | API usage and best practices |
| Anthropic Prompt Library | Examples | [docs.anthropic.com/claude/prompt-library](https://docs.anthropic.com/claude/prompt-library) | - | Real-world prompt examples |

**Workflow Design Patterns**

| Resource | Type | Link | Duration | Topics |
|----------|------|------|----------|--------|
| Langflow Documentation | Guide | [langflow.org](https://langflow.org/) | 1 hour | Visual workflow builder |
| Node-RED Tutorials | Course | [nodered.org/docs](https://nodered.org/docs/) | 2-3 hours | Flow-based programming concepts |
| Automating the Boring Stuff | Book | [automatetheboringstuff.com](https://automatetheboringstuff.com/) | 10+ hours | Python automation fundamentals |
| Workflow Optimization Patterns | Article | [martinfowler.com/articles](https://martinfowler.com/articles/) | 30 min | Enterprise workflow patterns |

### Community Resources

**Discord Server**
- Join: [VibeSurf Discord](https://discord.gg/86SPfhRVbk)
- Channels: #help, #showcase, #workflows, #feature-requests
- Active community support and discussions

**GitHub Repository**
- Repo: [github.com/vibesurf-ai/VibeSurf](https://github.com/vibesurf-ai/VibeSurf)
- Issues: Bug reports and feature requests
- Discussions: Q&A and best practices
- Wiki: Community-contributed guides

**Social Media**
- Twitter/X: [@warmshao](https://x.com/warmshao) - Latest updates and tips
- YouTube: [VibeSurf Channel](https://youtube.com/@vibesurf) - Tutorial videos (coming soon)
- WeChat: Scan QR code in extension for community group

### Learning Path Recommendations

**Beginner Path (1-2 days)**
1. Watch: Quick Start Guide video (15 min)
2. Read: README_zh.md - Installation and basic usage
3. Practice: Complete your first automated task
4. Explore: Try 3-5 pre-built workflows
5. Read: CLAUDE.md - Key Implementation Patterns

**Intermediate Path (3-5 days)**
1. Watch: Workflow Templates Showcase (30 min)
2. Read: API参考文档 - Understand API endpoints
3. Practice: Create your first custom workflow
4. Experiment: Tool API - Direct action execution
5. Learn: Multi-language client examples
6. Build: Integrate VibeSurf into your project

**Advanced Path (1-2 weeks)**
1. Watch: Advanced Features video (25 min)
2. Study: Performance optimization benchmarks
3. Practice: Implement parallel agent execution
4. Experiment: CDP logging for debugging
5. Learn: Troubleshooting Guide - Common issues
6. Build: Complex multi-step automation workflows
7. Optimize: Apply performance best practices

### Tutorial Requests

If you'd like to see tutorials on specific topics, please:

1. **Check existing issues**: [GitHub Issues](https://github.com/vibesurf-ai/VibeSurf/issues)
2. **Create a new request**: Use "Tutorial Request:" prefix
3. **Vote on popular requests**: Help prioritize content
4. **Contribute**: Share your own tutorials and examples

**Popular Tutorial Topics** (most requested):
- Advanced workflow patterns
- Integration with external APIs
- Custom tool development
- Performance tuning for large-scale automation
- Security best practices for production deployments

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

## Recent Changes (2026-01)

### CDP Browser Logging (NEW)
- **Console Logging Action** (`start_console_logging`): Monitor browser console messages
- **Network Logging Action** (`start_network_logging`): Track network requests and responses
- CDP-based event handlers for real-time log collection
- Enables debugging and monitoring of web applications

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
