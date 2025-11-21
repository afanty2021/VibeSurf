# -*- coding: utf-8 -*-
"""
VibeSurf浏览器自动化代理模块

这个模块基于browser-use框架实现了一个强大的浏览器自动化代理，
专门用于执行Web页面操作任务。该代理集成了视觉识别、自然语言理解
和复杂的浏览器交互能力。

主要功能：
- 基于LLM的智能网页操作
- 视觉元素识别和交互
- 多标签页管理
- 文件下载和上传
- 表单自动填写
- 动态内容处理

核心特性：
- 支持多种LLM模型（OpenAI、Claude、本地模型等）
- 异步执行和并发控制
- 完整的错误处理和恢复机制
- 可扩展的工具系统
- 详细的遥测数据收集
"""

import asyncio
import gc
import inspect
import json
import logging
import os.path
import pdb
import re
import sys
import tempfile
import time
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path
from typing import Any, Generic, Literal, TypeVar, Optional
from urllib.parse import urlparse

from dotenv import load_dotenv

from browser_use.agent.cloud_events import (
    CreateAgentOutputFileEvent,
    CreateAgentSessionEvent,
    CreateAgentStepEvent,
    CreateAgentTaskEvent,
    UpdateAgentTaskEvent,
)
from browser_use.agent.message_manager.utils import save_conversation
from browser_use.llm.base import BaseChatModel
from browser_use.llm.messages import BaseMessage, UserMessage
from browser_use.llm.openai.chat import ChatOpenAI
from browser_use.tokens.service import TokenCost

from bubus import EventBus
from pydantic import ValidationError
from uuid_extensions import uuid7str

# Lazy import for gif to avoid heavy agent.views import at startup
# from browser_use.agent.gif import create_history_gif
from browser_use.agent.message_manager.service import (
    MessageManager,
)
from browser_use.agent.prompts import SystemPrompt
from browser_use.agent.views import (
    ActionResult,
    AgentError,
    AgentHistory,
    AgentHistoryList,
    AgentOutput,
    AgentSettings,
    AgentState,
    AgentStepInfo,
    AgentStructuredOutput,
    BrowserStateHistory,
    StepMetadata,
)
from pydantic import BaseModel, ConfigDict, Field, ValidationError, create_model, model_validator
from browser_use import Browser, BrowserProfile, BrowserSession
from browser_use.browser.session import DEFAULT_BROWSER_PROFILE
from browser_use.browser.views import BrowserStateSummary
from browser_use.config import CONFIG
from browser_use.tools.registry.views import ActionModel
from browser_use.tools.service import Controller, Tools
from browser_use.dom.views import DOMInteractedElement
from browser_use.filesystem.file_system import FileSystem
from browser_use.observability import observe, observe_debug
from browser_use.sync import CloudSync
from browser_use.telemetry.views import AgentTelemetryEvent
from browser_use.utils import (
    _log_pretty_path,
    get_browser_use_version,
    get_git_info,
    time_execution_async,
    time_execution_sync,
)
from browser_use.llm.messages import BaseMessage, ContentPartImageParam, ContentPartTextParam, UserMessage
from browser_use.agent.service import Agent, AgentHookFunc
from vibe_surf.tools.file_system import CustomFileSystem
from vibe_surf.telemetry.service import ProductTelemetry

Context = TypeVar('Context')


class BrowserUseAgent(Agent):
    """
    VibeSurf浏览器自动化代理类

    这是一个基于browser-use框架的增强型浏览器自动化代理，
    继承自Agent基类，专门用于执行复杂的Web页面操作任务。

    主要职责：
    - 解析和理解用户任务描述
    - 制定浏览器操作策略
    - 执行页面交互和自动化操作
    - 处理动态网页内容和JavaScript
    - 管理文件下载和上传操作
    - 提供详细的执行反馈和错误报告

    核心特性：
    - 智能视觉识别：能够识别页面元素并进行精确交互
    - 自然语言理解：将用户指令转换为具体的浏览器操作
    - 多标签页管理：支持同时在多个标签页中执行任务
    - 错误恢复：具备智能的错误处理和重试机制
    - 扩展性：支持自定义工具和功能扩展

    工作流程：
    1. 接收任务描述和参数
    2. 初始化浏览器会话和工具系统
    3. 分析任务并制定执行计划
    4. 执行浏览器操作序列
    5. 收集结果并生成报告
    6. 清理资源并结束任务
    """

    @time_execution_sync('--init')
    def __init__(
            self,
            task: str,
            llm: BaseChatModel = ChatOpenAI(model='gpt-4.1-mini'),
            # Optional parameters - 可选参数
            browser_profile: BrowserProfile | None = None,           # 浏览器配置文件
            browser_session: BrowserSession | None = None,          # 浏览器会话
            browser: Browser | None = None,                         # 浏览器实例（browser_session的别名）
            tools: Tools[Context] | None = None,                    # 工具集
            controller: Tools[Context] | None = None,               # 控制器（tools的别名）
            # Initial agent run parameters - 初始代理运行参数
            sensitive_data: dict[str, str | dict[str, str]] | None = None,  # 敏感数据（如登录凭证）
            initial_actions: list[dict[str, dict[str, Any]]] | None = None,  # 初始化操作列表
            # Cloud Callbacks - 云端回调函数
            register_new_step_callback: (
                    Callable[['BrowserStateSummary', 'AgentOutput', int], None]  # 同步回调
                    | Callable[['BrowserStateSummary', 'AgentOutput', int], Awaitable[None]]  # 异步回调
                    | None
            ) = None,                                               # 新步骤回调函数
            register_done_callback: (
                    Callable[['AgentHistoryList'], Awaitable[None]]  # 异步回调
                    | Callable[['AgentHistoryList'], None]  # 同步回调
                    | None
            ) = None,                                               # 任务完成回调函数
            register_external_agent_status_raise_error_callback: Callable[[], Awaitable[bool]] | None = None,  # 外部代理状态错误回调
            register_should_stop_callback: Callable[[], Awaitable[bool]] | None = None,                    # 停止检查回调
            # Agent settings - 代理设置
            output_model_schema: type[AgentStructuredOutput] | None = None,     # 输出模型架构
            use_vision: bool = True,                              # 是否使用视觉识别
            save_conversation_path: str | Path | None = None,     # 对话保存路径
            save_conversation_path_encoding: str | None = 'utf-8', # 对话保存编码
            max_failures: int = 3,                                # 最大失败次数
            override_system_message: str | None = None,           # 覆盖系统消息
            extend_system_message: str | None = None,             # 扩展系统消息
            generate_gif: bool | str = False,                     # 是否生成GIF动图
            available_file_paths: list[str] | None = None,        # 可用文件路径列表
            include_attributes: list[str] | None = None,          # 包含的HTML属性
            max_actions_per_step: int = 10,                       # 每步最大操作数
            use_thinking: bool = True,                            # 是否启用思考模式
            flash_mode: bool = False,                             # 是否启用快速模式
            max_history_items: int | None = None,                 # 最大历史记录数
            page_extraction_llm: BaseChatModel | None = None,     # 页面提取专用LLM
            injected_agent_state: AgentState | None = None,       # 注入的代理状态
            source: str | None = None,                            # 代理来源标识
            file_system_path: str | None = None,                  # 文件系统路径
            task_id: str | None = None,                           # 任务ID
            calculate_cost: bool = False,                         # 是否计算成本
            display_files_in_done_text: bool = True,              # 在完成文本中显示文件
            include_tool_call_examples: bool = False,            # 是否包含工具调用示例
            vision_detail_level: Literal['auto', 'low', 'high'] = 'auto',  # 视觉详细程度
            llm_timeout: int = 90,                                # LLM超时时间（秒）
            step_timeout: int = 120,                              # 步骤超时时间（秒）
            directly_open_url: bool = False,                      # 是否直接打开URL
            include_recent_events: bool = False,                  # 是否包含最近事件
            sample_images: list[ContentPartTextParam | ContentPartImageParam] | None = None,  # 示例图像
            final_response_after_failure: bool = True,            # 失败后是否给出最终响应
            allow_parallel_action_types: list[str] = ["extract", "extract_content_from_file"],  # 允许的并行操作类型
            _url_shortening_limit: int = 25,                      # URL缩短限制
            token_cost_service: Optional[TokenCost] = None,       # 令牌成本服务
            **kwargs,
    ):
        # 设置默认值
        if page_extraction_llm is None:
            page_extraction_llm = llm
        if available_file_paths is None:
            available_file_paths = []

        # 生成唯一标识符
        self.id = task_id or uuid7str()              # 代理ID
        self.task_id: str = self.id                  # 任务ID（与代理ID相同）
        self.session_id: str = uuid7str()            # 会话ID
        self.allow_parallel_action_types = allow_parallel_action_types  # 允许的并行操作类型
        self._url_shortening_limit = _url_shortening_limit  # URL缩短限制
        self.sample_images = sample_images            # 示例图像
        browser_profile = browser_profile or DEFAULT_BROWSER_PROFILE  # 浏览器配置文件

        # 处理浏览器参数冲突（browser参数优先）
        if browser and browser_session:
            raise ValueError(
                '不能同时指定"browser"和"browser_session"参数。请使用"browser"参数以获得更简洁的API。')
        browser_session = browser or browser_session

        # 初始化浏览器会话
        self.browser_session = browser_session or BrowserSession(
            browser_profile=browser_profile,
            id=uuid7str()[:-4] + self.id[-4:],  # 重用相同的4字符后缀，以便在日志中一起显示
        )

        # 设置可用文件路径作为直接属性
        self.available_file_paths = available_file_paths

        # 核心组件初始化
        self.task = task                              # 任务描述
        self.llm = llm                                # 语言模型实例
        self.directly_open_url = directly_open_url    # 是否直接打开URL
        self.include_recent_events = include_recent_events  # 是否包含最近事件

        # 设置工具系统
        if tools is not None:
            self.tools = tools
        elif controller is not None:
            self.tools = controller
        else:
            self.tools = Tools(display_files_in_done_text=display_files_in_done_text)

        # Structured output
        self.output_model_schema = output_model_schema
        if self.output_model_schema is not None:
            self.tools.use_structured_output_action(self.output_model_schema)

        self.sensitive_data = sensitive_data

        self.settings = AgentSettings(
            use_vision=use_vision,
            vision_detail_level=vision_detail_level,
            save_conversation_path=save_conversation_path,
            save_conversation_path_encoding=save_conversation_path_encoding,
            max_failures=max_failures,
            override_system_message=override_system_message,
            extend_system_message=extend_system_message,
            generate_gif=generate_gif,
            include_attributes=include_attributes,
            max_actions_per_step=max_actions_per_step,
            use_thinking=use_thinking,
            flash_mode=flash_mode,
            max_history_items=max_history_items,
            page_extraction_llm=page_extraction_llm,
            calculate_cost=calculate_cost,
            include_tool_call_examples=include_tool_call_examples,
            llm_timeout=llm_timeout,
            step_timeout=step_timeout,
            final_response_after_failure=final_response_after_failure,
        )

        # Token cost service
        if token_cost_service is None:
            self.token_cost_service = TokenCost(include_cost=calculate_cost)
        else:
            self.token_cost_service = token_cost_service
        self.token_cost_service.register_llm(llm)
        self.token_cost_service.register_llm(page_extraction_llm)

        # Initialize state
        self.state = injected_agent_state or AgentState()

        # Initialize history
        self.history = AgentHistoryList(history=[], usage=None)

        # Initialize agent directory
        import time

        timestamp = int(time.time())
        base_tmp = Path(tempfile.gettempdir())
        self.agent_directory = base_tmp / f'browser_use_agent_{self.id}_{timestamp}'

        # Initialize file system and screenshot service
        self._set_file_system(file_system_path)
        self._set_screenshot_service()

        # Action setup
        self._setup_action_models()
        self._set_browser_use_version_and_source(source)

        initial_url = None

        # only load url if no initial actions are provided
        if self.directly_open_url and not self.state.follow_up_task and not initial_actions:
            initial_url = self._extract_url_from_task(self.task)
            if initial_url:
                self.logger.info(f'🔗 Found URL in task: {initial_url}, adding as initial action...')
                initial_actions = [{'go_to_url': {'url': initial_url, 'new_tab': False}}]

        self.initial_url = initial_url

        self.initial_actions = self._convert_initial_actions(initial_actions) if initial_actions else None
        # Verify we can connect to the model
        self._verify_and_setup_llm()

        # TODO: move this logic to the LLMs
        # Handle users trying to use use_vision=True with DeepSeek models
        if 'deepseek' in self.llm.model.lower():
            self.logger.warning(
                '⚠️ DeepSeek models do not support use_vision=True yet. Setting use_vision=False for now...')
            self.settings.use_vision = False

        if 'kimi-k2' in self.llm.model.lower():
            self.logger.warning(
                '⚠️ Kimi-k2 models do not support use_vision=True yet. Setting use_vision=False for now...')
            self.settings.use_vision = False

        if "qwen" in self.llm.model.lower() and "vl" not in self.llm.model.lower():
            self.logger.warning("⚠️ Qwen without VL doesn't support vision. Ignore Vision input.")
            self.settings.use_vision = False

        # Handle users trying to use use_vision=True with XAI models
        if 'grok' in self.llm.model.lower():
            self.logger.warning('⚠️ XAI models do not support use_vision=True yet. Setting use_vision=False for now...')
            self.settings.use_vision = False

        self.logger.info(f'🧠 Starting a browser-use version {self.version} with model={self.llm.model}')
        self.logger.info(
            f'{" +vision" if self.settings.use_vision else ""}'
            f' extraction_model={self.settings.page_extraction_llm.model if self.settings.page_extraction_llm else "Unknown"}'
            f'{" +file_system" if self.file_system else ""}'
        )

        # Initialize available actions for system prompt (only non-filtered actions)
        # These will be used for the system prompt to maintain caching
        self.unfiltered_actions = self.tools.registry.get_prompt_description()

        # Initialize message manager with state
        # Initial system prompt with all actions - will be updated during each step
        self._message_manager = MessageManager(
            task=task,
            system_message=SystemPrompt(
                max_actions_per_step=self.settings.max_actions_per_step,
                override_system_message=override_system_message,
                extend_system_message=extend_system_message,
                use_thinking=self.settings.use_thinking,
                flash_mode=self.settings.flash_mode,
            ).get_system_message(),
            file_system=self.file_system,
            state=self.state.message_manager_state,
            use_thinking=self.settings.use_thinking,
            # Settings that were previously in MessageManagerSettings
            include_attributes=self.settings.include_attributes,
            sensitive_data=sensitive_data,
            max_history_items=self.settings.max_history_items,
            vision_detail_level=self.settings.vision_detail_level,
            include_tool_call_examples=self.settings.include_tool_call_examples,
            include_recent_events=self.include_recent_events,
            sample_images=self.sample_images,
        )

        if self.sensitive_data:
            # Check if sensitive_data has domain-specific credentials
            has_domain_specific_credentials = any(isinstance(v, dict) for v in self.sensitive_data.values())

            # If no allowed_domains are configured, show a security warning
            if not self.browser_profile.allowed_domains:
                self.logger.error(
                    '⚠️⚠️⚠️ Agent(sensitive_data=••••••••) was provided but BrowserSession(allowed_domains=[...]) is not locked down! ⚠️⚠️⚠️\n'
                    '          ☠️ If the agent visits a malicious website and encounters a prompt-injection attack, your sensitive_data may be exposed!\n\n'
                    '             https://docs.browser-use.com/customize/browser-settings#restrict-urls\n'
                    'Waiting 10 seconds before continuing... Press [Ctrl+C] to abort.'
                )
                if sys.stdin.isatty():
                    try:
                        time.sleep(10)
                    except KeyboardInterrupt:
                        print(
                            '\n\n 🛑 Exiting now... set BrowserSession(allowed_domains=["example.com", "example.org"]) to only domains you trust to see your sensitive_data.'
                        )
                        sys.exit(0)
                else:
                    pass  # no point waiting if we're not in an interactive shell
                self.logger.warning(
                    '‼️ Continuing with insecure settings for now... but this will become a hard error in the future!'
                )

            # If we're using domain-specific credentials, validate domain patterns
            elif has_domain_specific_credentials:
                # For domain-specific format, ensure all domain patterns are included in allowed_domains
                domain_patterns = [k for k, v in self.sensitive_data.items() if isinstance(v, dict)]

                # Validate each domain pattern against allowed_domains
                for domain_pattern in domain_patterns:
                    is_allowed = False
                    for allowed_domain in self.browser_profile.allowed_domains:
                        # Special cases that don't require URL matching
                        if domain_pattern == allowed_domain or allowed_domain == '*':
                            is_allowed = True
                            break

                        # Need to create example URLs to compare the patterns
                        # Extract the domain parts, ignoring scheme
                        pattern_domain = domain_pattern.split('://')[-1] if '://' in domain_pattern else domain_pattern
                        allowed_domain_part = allowed_domain.split('://')[
                            -1] if '://' in allowed_domain else allowed_domain

                        # Check if pattern is covered by an allowed domain
                        # Example: "google.com" is covered by "*.google.com"
                        if pattern_domain == allowed_domain_part or (
                                allowed_domain_part.startswith('*.')
                                and (
                                        pattern_domain == allowed_domain_part[2:]
                                        or pattern_domain.endswith('.' + allowed_domain_part[2:])
                                )
                        ):
                            is_allowed = True
                            break

                    if not is_allowed:
                        self.logger.warning(
                            f'⚠️ Domain pattern "{domain_pattern}" in sensitive_data is not covered by any pattern in allowed_domains={self.browser_profile.allowed_domains}\n'
                            f'   This may be a security risk as credentials could be used on unintended domains.'
                        )

        # Callbacks
        self.register_new_step_callback = register_new_step_callback
        self.register_done_callback = register_done_callback
        self.register_should_stop_callback = register_should_stop_callback
        self.register_external_agent_status_raise_error_callback = register_external_agent_status_raise_error_callback

        # Telemetry
        self.telemetry = ProductTelemetry()

        if self.settings.save_conversation_path:
            self.settings.save_conversation_path = Path(self.settings.save_conversation_path).expanduser().resolve()
            self.logger.info(f'💬 Saving conversation to {_log_pretty_path(self.settings.save_conversation_path)}')

        # Initialize download tracking
        assert self.browser_session is not None, 'BrowserSession is not set up'
        self.has_downloads_path = self.browser_session.browser_profile.downloads_path is not None
        if self.has_downloads_path:
            self._last_known_downloads: list[str] = []
            self.logger.debug('📁 Initialized download tracking for agent')

        self._external_pause_event = asyncio.Event()
        self._external_pause_event.set()

    def _set_file_system(self, file_system_path: str | None = None) -> None:
        # Check for conflicting parameters
        if self.state.file_system_state and file_system_path:
            raise ValueError(
                'Cannot provide both file_system_state (from agent state) and file_system_path. '
                'Either restore from existing state or create new file system at specified path, not both.'
            )

        # Check if we should restore from existing state first
        if self.state.file_system_state:
            try:
                # Restore file system from state at the exact same location
                self.file_system = CustomFileSystem.from_state(self.state.file_system_state)
                # The parent directory of base_dir is the original file_system_path
                self.file_system_path = str(self.file_system.base_dir)
                self.logger.debug(f'💾 File system restored from state to: {self.file_system_path}')
                return
            except Exception as e:
                self.logger.error(f'💾 Failed to restore file system from state: {e}')
                raise e

        # Initialize new file system
        try:
            if file_system_path:
                self.file_system = CustomFileSystem(file_system_path)
                self.file_system_path = file_system_path
            else:
                # Use the agent directory for file system
                self.file_system = CustomFileSystem(self.agent_directory)
                self.file_system_path = str(self.agent_directory)
        except Exception as e:
            self.logger.error(f'💾 Failed to initialize file system: {e}.')
            raise e

        # Save file system state to agent state
        self.state.file_system_state = self.file_system.get_state()

        self.logger.debug(f'💾 File system path: {self.file_system_path}')

    @property
    def logger(self) -> logging.Logger:
        """Get instance-specific logger with task ID and browser session info"""
        # Update target ID dynamically if available
        _browser_session_id = self.browser_session.id if self.browser_session else self.id
        _current_target_id = (
            self.browser_session.agent_focus.target_id[-4:]
            if self.browser_session and hasattr(self.browser_session,
                                                'agent_focus') and self.browser_session.agent_focus and hasattr(
                self.browser_session.agent_focus, 'target_id')
            else '--'
        )
        return logging.getLogger(
            f'browser-use.Agent:{self.task_id[-4:]} on target:{_current_target_id} of browser:{_browser_session_id[-4:]}')

    async def _finalize(self, browser_state_summary: BrowserStateSummary | None) -> None:
        """Finalize the step with history, logging, and events"""
        step_end_time = time.time()
        if not self.state.last_result:
            return

        if browser_state_summary:
            metadata = StepMetadata(
                step_number=self.state.n_steps,
                step_start_time=self.step_start_time,
                step_end_time=step_end_time,
            )

            # Use _make_history_item like main branch
            await self._make_history_item(self.state.last_model_output, browser_state_summary, self.state.last_result,
                                          metadata, state_message=self._message_manager.last_state_message_text,)

        # Log step completion summary
        self._log_step_completion_summary(self.step_start_time, self.state.last_result)

        # Save file system state after step completion
        self.save_file_system_state()

        # Emit both step created and executed events
        if browser_state_summary and self.state.last_model_output:
            # Extract key step data for the event
            actions_data = []
            if self.state.last_model_output.action:
                for action in self.state.last_model_output.action:
                    action_dict = action.model_dump() if hasattr(action, 'model_dump') else {}
                    actions_data.append(action_dict)

        # Increment step counter after step is fully completed
        self.state.n_steps += 1

    def add_new_task(self, new_task: str) -> None:
        """Add a new task to the agent, keeping the same task_id as tasks are continuous"""
        # Simply delegate to message manager - no need for new task_id or events
        # The task continues with new instructions, it doesn't end and start a new one
        self.task = new_task
        self._message_manager.add_new_task(new_task)

        # Mark as follow-up task and recreate eventbus (gets shut down after each run)
        self.state.follow_up_task = True

    @observe(name='agent.run', metadata={'task': '{{task}}', 'debug': '{{debug}}'})
    @time_execution_async('--run')
    async def run(
            self,
            max_steps: int = 100,
            on_step_start: AgentHookFunc | None = None,
            on_step_end: AgentHookFunc | None = None,
    ) -> AgentHistoryList[AgentStructuredOutput]:
        """Execute the task with maximum number of steps"""

        loop = asyncio.get_event_loop()
        agent_run_error: str | None = None  # Initialize error tracking variable
        self._force_exit_telemetry_logged = False  # ADDED: Flag for custom telemetry on force exit

        # Set up the  signal handler with callbacks specific to this agent
        from browser_use.utils import SignalHandler

        # Define the custom exit callback function for second CTRL+C
        def on_force_exit_log_telemetry():
            self._log_agent_event(max_steps=max_steps, agent_run_error='SIGINT: Cancelled by user')
            # NEW: Call the flush method on the telemetry instance
            if hasattr(self, 'telemetry') and self.telemetry:
                self.telemetry.flush()
            self._force_exit_telemetry_logged = True  # Set the flag

        signal_handler = SignalHandler(
            loop=loop,
            pause_callback=self.pause,
            resume_callback=self.resume,
            custom_exit_callback=on_force_exit_log_telemetry,  # Pass the new telemetrycallback
            exit_on_second_int=True,
        )
        signal_handler.register()

        try:
            await self._log_agent_run()

            self.logger.debug(
                f'🔧 Agent setup: Task ID {self.task_id[-4:]}, Session ID {self.session_id[-4:]}, Browser Session ID {self.browser_session.id[-4:] if self.browser_session else "None"}'
            )

            # Initialize timing for session and task
            self._session_start_time = time.time()
            self._task_start_time = self._session_start_time  # Initialize task start time

            self.logger.debug('🔧 Browser session started with watchdogs attached')

            # Execute initial actions if provided
            if self.initial_actions:
                self.logger.debug(f'⚡ Executing {len(self.initial_actions)} initial actions...')
                result = await self.multi_act(self.initial_actions, check_for_new_elements=False)
                self.state.last_result = result
                self.logger.debug('✅ Initial actions completed')

            self.logger.debug(f'🔄 Starting main execution loop with max {max_steps} steps...')
            for step in range(max_steps):
                # Replace the polling with clean pause-wait
                if self.state.paused:
                    self.logger.debug(f'⏸️ Step {step}: Agent paused, waiting to resume...')
                    await self._external_pause_event.wait()
                    signal_handler.reset()

                # Check if we should stop due to too many failures
                if (self.state.consecutive_failures) >= self.settings.max_failures + int(
                        self.settings.final_response_after_failure
                ):
                    self.logger.error(f'❌ Stopping due to {self.settings.max_failures} consecutive failures')
                    agent_run_error = f'Stopped due to {self.settings.max_failures} consecutive failures'
                    break

                # Check control flags before each step
                if self.state.stopped:
                    self.logger.info('🛑 Agent stopped')
                    agent_run_error = 'Agent stopped programmatically'
                    break

                if on_step_start is not None:
                    await on_step_start(self)

                self.logger.debug(f'🚶 Starting step {step + 1}/{max_steps}...')
                step_info = AgentStepInfo(step_number=step, max_steps=max_steps)

                try:
                    await asyncio.wait_for(
                        self.step(step_info),
                        timeout=self.settings.step_timeout,
                    )
                    self.logger.debug(f'✅ Completed step {step + 1}/{max_steps}')
                except TimeoutError:
                    # Handle step timeout gracefully
                    error_msg = f'Step {step + 1} timed out after {self.settings.step_timeout} seconds'
                    self.logger.error(f'⏰ {error_msg}')
                    self.state.consecutive_failures += 1
                    self.state.last_result = [ActionResult(error=error_msg)]

                if on_step_end is not None:
                    await on_step_end(self)

                if self.history.is_done():
                    self.logger.debug(f'🎯 Task completed after {step + 1} steps!')
                    await self.log_completion()

                    if self.register_done_callback:
                        if inspect.iscoroutinefunction(self.register_done_callback):
                            await self.register_done_callback(self.history)
                        else:
                            self.register_done_callback(self.history)

                    # Task completed
                    break
            else:
                agent_run_error = 'Failed to complete task in maximum steps'

                self.history.add_item(
                    AgentHistory(
                        model_output=None,
                        result=[ActionResult(error=agent_run_error, include_in_memory=True)],
                        state=BrowserStateHistory(
                            url='',
                            title='',
                            tabs=[],
                            interacted_element=[],
                            screenshot_path=None,
                        ),
                        metadata=None,
                    )
                )

                self.logger.info(f'❌ {agent_run_error}')

            self.logger.debug('📊 Collecting usage summary...')
            self.history.usage = await self.token_cost_service.get_usage_summary()

            # set the model output schema and call it on the fly
            if self.history._output_model_schema is None and self.output_model_schema is not None:
                self.history._output_model_schema = self.output_model_schema

            self.logger.debug('🏁 Agent.run() completed successfully')
            return self.history

        except KeyboardInterrupt:
            # Already handled by our signal handler, but catch any direct KeyboardInterrupt as well
            self.logger.debug('Got KeyboardInterrupt during execution, returning current history')
            agent_run_error = 'KeyboardInterrupt'

            self.history.usage = await self.token_cost_service.get_usage_summary()

            return self.history

        except Exception as e:
            self.logger.error(f'Agent run failed with exception: {e}', exc_info=True)
            agent_run_error = str(e)
            raise e

        finally:
            # Log token usage summary
            await self.token_cost_service.log_usage_summary()

            self.save_history(os.path.join(self.file_system_path, 'AgentHistory.json'))

            # Unregister signal handlers before cleanup
            signal_handler.unregister()

            if not self._force_exit_telemetry_logged:  # MODIFIED: Check the flag
                try:
                    self._log_agent_event(max_steps=max_steps, agent_run_error=agent_run_error)
                except Exception as log_e:  # Catch potential errors during logging itself
                    self.logger.error(f'Failed to log telemetry event: {log_e}', exc_info=True)
            else:
                # ADDED: Info message when custom telemetry for SIGINT was already logged
                self.logger.debug('Telemetry for force exit (SIGINT) was logged by custom exit callback.')

            # Generate GIF if needed before stopping event bus
            if self.settings.generate_gif:
                output_path: str = 'agent_history.gif'
                if isinstance(self.settings.generate_gif, str):
                    output_path = self.settings.generate_gif

                # Lazy import gif module to avoid heavy startup cost
                from browser_use.agent.gif import create_history_gif

                create_history_gif(task=self.task, history=self.history, output_path=output_path)

            await self.close()