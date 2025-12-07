"""
Boss 直聘自动化工作流

主要入口文件，导出所有核心组件
"""

from .config import BossZhipinConfig, get_config
from .session_manager import BossZhipinSessionManager
from .matcher import ResumeMatcher, MatchResult, MatchLevel
from .messenger import AutoMessenger, MessageStatus
from .qa_system import IntelligentQA, IntentType
from .anti_detection import AntiDetectionSystem, RiskLevel
from .automation_workflow import BossZhipinAutomation

__version__ = "1.0.0"
__author__ = "VibeSurf Team"

# 导出主要类
__all__ = [
    "BossZhipinConfig",
    "get_config",
    "BossZhipinSessionManager",
    "ResumeMatcher",
    "MatchResult",
    "MatchLevel",
    "AutoMessenger",
    "MessageStatus",
    "IntelligentQA",
    "IntentType",
    "AntiDetectionSystem",
    "RiskLevel",
    "BossZhipinAutomation"
]