"""
Boss 直聘自动化配置模块

该模块包含所有 Boss 直聘自动化的配置参数，
包括搜索条件、消息模板、行为策略等。
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json
import os
from pathlib import Path

@dataclass
class SearchConfig:
    """搜索配置"""
    # 职位搜索条件
    position: str = "前端开发"
    city: str = "101010100"  # 北京
    experience: str = "3"  # 3-5年
    salary: str = "10K-15K"
    education: str = "bachelor"
    scale: str = "company"  # 公司规模

    # 搜索范围
    page_limit: int = 10  # 最多搜索页数
    results_per_page: int = 30

    # 更新频率
    refresh_interval: int = 3600  # 1小时刷新一次

@dataclass
class MessageTemplates:
    """消息模板"""
    # 邀请消息模板
    invitation_templates: List[str] = None

    # 常见问题回答
    qa_templates: Dict[str, str] = None

    # 跟进消息
    follow_up_templates: List[str] = None

    def __post_init__(self):
        if self.invitation_templates is None:
            self.invitation_templates = [
                """您好，我是{company_name}的{position_name}。
看到您的简历很感兴趣，我们在招聘{job_title}，
不知道您是否感兴趣？期待与您进一步沟通！""",

                """您好，我是{company_name}的HR。
看到您在{job_field}领域有{experience}年经验，
我们有一个很好的{job_title}机会，薪资范围{salary_range}，
希望可以和您聊聊！""",

                """您好，我是{company_name}的{position_name}。
您的技术背景和我们正在招聘的{job_title}很匹配，
我们提供{benefits}，不知道您是否考虑新机会？"""
            ]

        if self.qa_templates is None:
            self.qa_templates = {
                "薪资范围": "我们提供有竞争力的薪资，具体范围根据您的能力和经验而定，通常在15-30K之间。",
                "工作地点": "公司位于{location}，交通便利，靠近{metro_station}地铁站。",
                "公司介绍": "我们是一家专注于{field}的科技公司，团队规模{team_size}人，业务发展迅速。",
                "技术栈": "主要技术栈包括{tech_stack}，我们重视技术成长，提供技术分享和培训机会。",
                "福利待遇": "我们提供五险一金、带薪年假、弹性工作时间、技术培训、定期团建等福利。",
                "面试流程": "面试流程一般是：技术初试 → 技术复试 → HR面试 → offer，整个过程约1-2周。",
                "上班时间": "工作时间是周一至周五 9:00-18:00，周末双休。",
                "远程办公": "目前是全职办公，特殊情况下可以申请临时远程。"
            }

        if self.follow_up_templates is None:
            self.follow_up_templates = [
                "您好，不知道您对我们公司的职位是否还有兴趣？",
                "您好，如果您有时间的话，我们可以约个时间详细聊聊这个机会。",
                "您好，我们的职位还在招聘中，期待您的回复。"
            ]

@dataclass
class BehaviorConfig:
    """行为配置（防检测）"""
    # 操作间隔（秒）
    action_interval_min: int = 2
    action_interval_max: int = 5

    # 每日限制
    daily_message_limit: int = 50
    hourly_message_limit: int = 10

    # 鼠标行为
    enable_mouse_movement: bool = True
    random_scroll: bool = True

    # 时间窗口
    work_hours_start: int = 9  # 9点开始
    work_hours_end: int = 18   # 18点结束
    avoid_lunch: bool = True   # 避开午饭时间

    # 退出策略
    consecutive_failures_threshold: int = 3
    session_timeout: int = 1800  # 30分钟

@dataclass
class BossZhipinConfig:
    """Boss 直聘自动化主配置"""
    search: SearchConfig = None
    messages: MessageTemplates = None
    behavior: BehaviorConfig = None

    # 公司信息
    company_name: str = ""
    position_name: str = "HR"

    def __post_init__(self):
        if self.search is None:
            self.search = SearchConfig()
        if self.messages is None:
            self.messages = MessageTemplates()
        if self.behavior is None:
            self.behavior = BehaviorConfig()

    @classmethod
    def from_file(cls, config_path: str) -> 'BossZhipinConfig':
        """从配置文件加载"""
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls(**data)
        return cls()

    def to_file(self, config_path: str) -> None:
        """保存到配置文件"""
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.__dict__, f, ensure_ascii=False, indent=2)

# 默认配置实例
DEFAULT_CONFIG = BossZhipinConfig()

# 获取配置
def get_config(config_dir: Optional[str] = None) -> BossZhipinConfig:
    """获取配置"""
    if config_dir:
        config_path = Path(config_dir) / "boss_zhipin_config.json"
        if config_path.exists():
            return BossZhipinConfig.from_file(str(config_path))

    # 尝试从用户目录加载
    user_config = Path.home() / ".vibesurf" / "boss_zhipin_config.json"
    if user_config.exists():
        return BossZhipinConfig.from_file(str(user_config))

    # 返回默认配置
    return DEFAULT_CONFIG