# -*- coding: utf-8 -*-
"""
VibeSurf代理数据模型和配置视图

这个模块定义了VibeSurf代理系统的核心数据模型、配置选项和输出格式。
包含了代理设置、输出结构、以及工具集成的Pydantic模型定义。

主要组件：
- VibeSurfAgentOutput: 代理输出模型
- VibeSurfAgentSettings: 代理配置设置
- CustomAgentOutput: 自定义代理输出格式
"""

import asyncio
import json
import logging
import os
import pickle
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid_extensions import uuid7str
from json_repair import repair_json

# Browser-Use框架相关导入
from browser_use.browser.session import BrowserSession
from browser_use.llm.base import BaseChatModel
from browser_use.llm.messages import UserMessage, SystemMessage, BaseMessage, AssistantMessage, ContentPartTextParam, \
    ContentPartImageParam, ImageURL
from browser_use.browser.views import TabInfo, BrowserStateSummary
from browser_use.filesystem.file_system import FileSystem
from browser_use.agent.views import AgentSettings
from pydantic import BaseModel, Field, ConfigDict, create_model
from browser_use.agent.views import AgentSettings, DEFAULT_INCLUDE_ATTRIBUTES
from browser_use.tools.registry.views import ActionModel


class VibeSurfAgentOutput(BaseModel):
    """
    VibeSurf代理输出模型

    遵循browser-use模式的代理输出结构，包含思考过程和动作列表。
    支持动态类型扩展和自定义动作模型。

    属性：
        thinking: 代理的思考过程，用于决策推理
        action: 需要执行的动作列表
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')

    thinking: str | None = None     # 代理思考过程，可选字段
    action: List[Any] = Field(     # 动作列表，至少包含一个动作
        ...,
        description='List of actions to execute',
        json_schema_extra={'min_items': 1},
    )

    @classmethod
    def model_json_schema(cls, **kwargs):
        schema = super().model_json_schema(**kwargs)
        schema['required'] = ['thinking', 'action']
        return schema

    @staticmethod
    def type_with_custom_actions(custom_actions: type) -> type:
        """Extend actions with custom actions"""
        model_ = create_model(
            'VibeSurfAgentOutput',
            __base__=VibeSurfAgentOutput,
            action=(
                list[custom_actions],  # type: ignore
                Field(..., description='List of actions to execute', json_schema_extra={'min_items': 1}),
            ),
            __module__=VibeSurfAgentOutput.__module__,
        )
        model_.__doc__ = 'VibeSurfAgentOutput model with custom actions'
        return model_


class VibeSurfAgentSettings(BaseModel):
    """
    VibeSurf代理配置设置模型

    定义了代理运行时的各项配置参数，包括超时设置、
    执行模式、性能优化选项等。

    配置项：
        use_vision: 是否启用视觉识别功能
        max_failures: 最大失败重试次数
        agent_mode: 代理执行模式（thinking/no-thinking/flash）
        各种超时和性能设置
    """
    use_vision: bool = True                                   # 是否启用视觉识别
    max_failures: int = 3                                    # 最大失败重试次数
    override_system_message: str | None = None               # 完全替换系统消息
    extend_system_message: str | None = None                 # 扩展系统消息
    include_attributes: list[str] | None = DEFAULT_INCLUDE_ATTRIBUTES  # 包含的HTML属性
    max_actions_per_step: int = 4                           # 每步最大动作数
    max_history_items: int | None = None                     # 最大历史记录项数
    include_token_cost: bool = False                        # 是否包含令牌成本

    calculate_cost: bool = True                              # 是否计算成本
    include_tool_call_examples: bool = False                 # 是否包含工具调用示例
    llm_timeout: int = 60                                    # LLM调用超时时间（秒）
    step_timeout: int = 180                                  # 每步执行超时时间（秒）

    agent_mode: str = "thinking"                             # 代理模式：thinking/no-thinking/flash


class CustomAgentOutput(BaseModel):
    """
    自定义代理输出模型

    提供了更灵活的代理输出格式，支持动态动作类型扩展。
    可根据不同的代理模式和工具集定制输出结构。

    特性：
        - 支持thinking模式的思考过程输出
        - 支持无thinking模式的快速执行
        - 动态类型扩展能力
        - 与工具注册系统的无缝集成

    属性：
        thinking: 代理思考过程（可选）
        action: 要执行的动作（ActionModel格式）
    """
    model_config = ConfigDict(arbitrary_types_allowed=True, extra='forbid')
    thinking: str | None = None              # 代理思考过程，支持no-thinking模式
    action: ActionModel = Field(             # 使用ActionModel类型的动作定义
        ...,
        description='Action to execute',
    )
    @classmethod
    def model_json_schema(cls, **kwargs):
        schema = super().model_json_schema(**kwargs)
        schema['required'] = ['action']
        return schema
    @staticmethod
    def type_with_custom_actions(custom_actions: type[ActionModel]) -> type['CustomAgentOutput']:
        """Extend actions with custom actions"""
        model_ = create_model(
            'AgentOutput',
            __base__=CustomAgentOutput,
            action=(
                custom_actions,  # type: ignore
                Field(..., description='Action to execute'),
            ),
            __module__=CustomAgentOutput.__module__,
        )
        model_.__doc__ = 'AgentOutput model with custom actions'
        return model_
    @staticmethod
    def type_with_custom_actions_no_thinking(custom_actions: type[ActionModel]) -> type['CustomAgentOutput']:
        """Extend actions with custom actions and exclude thinking field"""
        class AgentOutputNoThinking(CustomAgentOutput):
            @classmethod
            def model_json_schema(cls, **kwargs):
                schema = super().model_json_schema(**kwargs)
                del schema['properties']['thinking']
                schema['required'] = ['action']
                return schema
        model = create_model(
            'AgentOutputNoThinking',
            __base__=AgentOutputNoThinking,
            action=(
                custom_actions,  # type: ignore
                Field(..., description='Action to execute'),
            ),
            __module__=AgentOutputNoThinking.__module__,
        )
        model.__doc__ = 'AgentOutput model with custom actions'
        return model
