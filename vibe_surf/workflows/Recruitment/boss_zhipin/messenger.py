"""
自动消息发送模块

该模块负责自动发送消息给候选人，
包括消息模板管理、发送控制、个性化定制等。
"""

import asyncio
import random
import json
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime, time as dt_time
from dataclasses import dataclass, field
from enum import Enum

from .session_manager import BossZhipinSessionManager
from .matcher import MatchResult, MatchLevel
from .config import BossZhipinConfig

logger = logging.getLogger(__name__)

class MessageStatus(Enum):
    """消息状态"""
    PENDING = "pending"      # 待发送
    SENT = "sent"           # 已发送
    FAILED = "failed"       # 发送失败
    REPLIED = "replied"     # 已回复

@dataclass
class MessageRecord:
    """消息记录"""
    candidate_id: str
    candidate_name: str
    message_content: str
    status: MessageStatus
    timestamp: datetime = field(default_factory=datetime.now)
    error_message: Optional[str] = None
    reply_content: Optional[str] = None
    reply_time: Optional[datetime] = None

class AutoMessenger:
    """自动消息发送器"""

    def __init__(self,
                 session: BossZhipinSessionManager,
                 config: BossZhipinConfig):
        """
        初始化消息发送器

        Args:
            session: Boss 直聘会话管理器
            config: 配置信息
        """
        self.session = session
        self.config = config
        self.message_records: List[MessageRecord] = []
        self.daily_sent_count = 0
        self.hourly_sent_count = 0
        self.last_reset_time = datetime.now()

        # 消息发送历史（用于避免重复发送）
        self.sent_candidates: set = set()

    async def send_to_candidates(self,
                                match_results: List[MatchResult],
                                custom_template: Optional[str] = None) -> Dict[str, int]:
        """
        发送消息给候选人

        Args:
            match_results: 匹配结果列表
            custom_template: 自定义消息模板

        Returns:
            Dict[str, int]: 发送结果统计
        """
        stats = {
            "total": len(match_results),
            "sent": 0,
            "failed": 0,
            "skipped": 0
        }

        # 检查发送限制
        if not self._check_send_limits():
            logger.warning("已达到发送限制")
            return stats

        # 过滤已发送的候选人
        candidates_to_send = []
        for result in match_results:
            candidate = result.candidate
            candidate_id = self._get_candidate_id(candidate)

            # 跳过已发送的
            if candidate_id in self.sent_candidates:
                stats["skipped"] += 1
                continue

            # 只发送给符合匹配级别的
            if result.match_level in [MatchLevel.EXCELLENT, MatchLevel.GOOD, MatchLevel.FAIR]:
                candidates_to_send.append((candidate, result))
            else:
                stats["skipped"] += 1

        logger.info(f"准备发送消息给 {len(candidates_to_send)} 个候选人")

        # 批量发送
        for candidate, match_result in candidates_to_send:
            try:
                # 检查发送限制
                if not self._check_send_limits():
                    logger.warning("达到发送限制，停止发送")
                    break

                # 检查时间窗口
                if not self._check_time_window():
                    logger.info("不在工作时间，暂停发送")
                    break

                # 生成个性化消息
                message = self._generate_message(candidate, match_result, custom_template)

                # 发送消息
                success = await self._send_message(candidate, message)

                # 记录结果
                if success:
                    stats["sent"] += 1
                    self.daily_sent_count += 1
                    self.hourly_sent_count += 1
                    self.sent_candidates.add(candidate_id)

                    # 记录成功
                    record = MessageRecord(
                        candidate_id=candidate_id,
                        candidate_name=candidate.get("name", ""),
                        message_content=message,
                        status=MessageStatus.SENT
                    )
                    self.message_records.append(record)

                    logger.info(f"消息已发送给: {candidate.get('name', '')}")
                else:
                    stats["failed"] += 1
                    record = MessageRecord(
                        candidate_id=candidate_id,
                        candidate_name=candidate.get("name", ""),
                        message_content=message,
                        status=MessageStatus.FAILED
                    )
                    self.message_records.append(record)

                # 随机延迟（模拟人类行为）
                delay = random.uniform(
                    self.config.behavior.action_interval_min,
                    self.config.behavior.action_interval_max
                )
                await asyncio.sleep(delay)

            except Exception as e:
                logger.error(f"发送消息失败: {e}")
                stats["failed"] += 1
                continue

        # 保存记录
        await self._save_records()

        return stats

    def _check_send_limits(self) -> bool:
        """检查发送限制"""
        # 重置计数器
        now = datetime.now()
        if now.date() != self.last_reset_time.date():
            self.daily_sent_count = 0
            self.last_reset_time = now

        if now.hour != self.last_reset_time.hour:
            self.hourly_sent_count = 0
            self.last_reset_time = now

        # 检查限制
        if self.daily_sent_count >= self.config.behavior.daily_message_limit:
            logger.warning(f"已达到每日发送限制: {self.config.behavior.daily_message_limit}")
            return False

        if self.hourly_sent_count >= self.config.behavior.hourly_message_limit:
            logger.warning(f"已达到每小时发送限制: {self.config.behavior.hourly_message_limit}")
            return False

        return True

    def _check_time_window(self) -> bool:
        """检查是否在发送时间窗口"""
        now = datetime.now()
        current_time = now.time()
        current_hour = now.hour

        # 检查工作时间
        work_start = dt_time(self.config.behavior.work_hours_start)
        work_end = dt_time(self.config.behavior.work_hours_end)

        if current_time < work_start or current_time > work_end:
            return False

        # 检查午饭时间
        if self.config.behavior.avoid_lunch:
            if 12 <= current_hour <= 13:
                return False

        return True

    def _generate_message(self,
                          candidate: Dict,
                          match_result: MatchResult,
                          custom_template: Optional[str] = None) -> str:
        """
        生成个性化消息

        Args:
            candidate: 候选人信息
            match_result: 匹配结果
            custom_template: 自定义模板

        Returns:
            str: 生成的消息
        """
        # 选择模板
        if custom_template:
            template = custom_template
        else:
            # 根据匹配级别选择模板
            if match_result.match_level == MatchLevel.EXCELLENT:
                template = self.config.messages.invitation_templates[0]
            elif match_result.match_level == MatchLevel.GOOD:
                template = self.config.messages.invitation_templates[1]
            else:
                template = self.config.messages.invitation_templates[2]

        # 个性化参数
        params = {
            "company_name": self.config.company_name,
            "position_name": self.config.position_name,
            "candidate_name": candidate.get("name", ""),
            "candidate_position": candidate.get("position", ""),
            "candidate_company": candidate.get("company", ""),
            "job_title": "前端开发工程师",  # 从配置中获取
            "job_field": "前端开发",
            "experience": candidate.get("experience", ""),
            "salary_range": "15-25K",
            "benefits": "五险一金、带薪年假、弹性工作、技术培训",
            "location": "北京",
            "metro_station": "望京",
            "tech_stack": "React、TypeScript、Node.js",
            "team_size": "50-100人",
            "field": "互联网"
        }

        # 添加匹配相关的个性化内容
        if match_result.strength_points:
            params["strengths"] = "、".join(match_result.strength_points[:3])
            template += f"\n\n特别注意到您的{params['strengths']}，这与我们的要求非常匹配。"

        # 填充模板
        try:
            message = template.format(**params)
        except KeyError as e:
            logger.error(f"模板参数缺失: {e}")
            # 使用默认消息
            message = f"您好，我是{self.config.company_name}的{self.config.position_name}。看到您的简历很感兴趣，希望可以进一步沟通。"

        # 添加个人化结尾
        if match_result.match_level == MatchLevel.EXCELLENT:
            message += "\n\n您的背景非常符合我们的要求，期待您的回复！"
        elif match_result.match_level == MatchLevel.GOOD:
            message += "\n\n如果您对这个机会感兴趣，期待与您交流。"
        else:
            message += "\n\n如果您正在考虑新的机会，欢迎聊聊。"

        return message

    async def _send_message(self, candidate: Dict, message: str) -> bool:
        """
        发送消息给单个候选人

        Args:
            candidate: 候选人信息
            message: 消息内容

        Returns:
            bool: 是否发送成功
        """
        try:
            # 构建候选人详情页URL
            base_url = "https://www.zhipin.com"
            candidate_url = candidate.get("href", "")
            if candidate_url and not candidate_url.startswith("http"):
                candidate_url = base_url + candidate_url

            if not candidate_url:
                logger.error(f"候选人URL缺失: {candidate.get('name', '')}")
                return False

            # 发送消息
            success = await self.session.send_message(candidate_url, message)

            # 模拟人类行为
            if self.config.behavior.enable_mouse_movement:
                await self._simulate_human_behavior()

            return success

        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            return False

    async def _simulate_human_behavior(self):
        """模拟人类行为"""
        try:
            # 随机滚动
            if self.config.behavior.random_scroll:
                scroll_distance = random.randint(100, 500)
                await self.session.page.evaluate(f"window.scrollBy(0, {scroll_distance})")
                await asyncio.sleep(random.uniform(0.5, 1.0))

                # 滚回去
                await self.session.page.evaluate(f"window.scrollBy(0, -{scroll_distance})")
                await asyncio.sleep(random.uniform(0.5, 1.0))

            # 随机鼠标移动
            if self.config.behavior.enable_mouse_movement:
                x = random.randint(100, 800)
                y = random.randint(100, 600)
                await self.session.page.mouse.move(x, y)

        except Exception as e:
            logger.error(f"模拟人类行为失败: {e}")

    def _get_candidate_id(self, candidate: Dict) -> str:
        """获取候选人唯一ID"""
        # 使用姓名+公司+职位作为唯一标识
        name = candidate.get("name", "")
        company = candidate.get("company", "")
        position = candidate.get("position", "")
        return f"{name}_{company}_{position}".replace(" ", "_")

    async def send_follow_up(self,
                            days_ago: int = 3,
                            follow_up_template: Optional[str] = None) -> Dict[str, int]:
        """
        发送跟进消息

        Args:
            days_ago: 多少天前发送的消息
            follow_up_template: 跟进消息模板

        Returns:
            Dict[str, int]: 发送结果统计
        """
        stats = {
            "total": 0,
            "sent": 0,
            "failed": 0,
            "skipped": 0
        }

        # 查找需要跟进的候选人
        cutoff_date = datetime.now() - timedelta(days=days_ago)

        for record in self.message_records:
            if (record.status == MessageStatus.SENT and
                record.timestamp < cutoff_date and
                record.reply_content is None):

                stats["total"] += 1

                # 检查发送限制
                if not self._check_send_limits():
                    stats["skipped"] += 1
                    continue

                # 选择跟进消息模板
                if follow_up_template:
                    message = follow_up_template
                else:
                    message = random.choice(self.config.messages.follow_up_templates)

                # 这里需要找到候选人并重新发送消息
                # 实际实现中需要保存候选人的详细信息
                logger.info(f"准备发送跟进消息给: {record.candidate_name}")

                # TODO: 实现实际的跟进发送逻辑
                # success = await self._send_follow_up_message(record, message)

        return stats

    async def check_replies(self) -> List[MessageRecord]:
        """
        检查新回复

        Returns:
            List[MessageRecord]: 有新回复的消息记录
        """
        try:
            # 获取新消息
            messages = await self.session.check_new_messages()

            # 更新消息记录
            replied_records = []
            for message in messages:
                # 查找对应的消息记录
                for record in self.message_records:
                    if (record.candidate_name in message["sender"] and
                        record.status == MessageStatus.SENT and
                        record.reply_content is None):

                        # 更新记录
                        record.reply_content = message["content"]
                        record.reply_time = datetime.now()
                        record.status = MessageStatus.REPLIED
                        replied_records.append(record)

                        logger.info(f"收到 {record.candidate_name} 的回复")
                        break

            # 保存记录
            if replied_records:
                await self._save_records()

            return replied_records

        except Exception as e:
            logger.error(f"检查回复失败: {e}")
            return []

    async def _save_records(self):
        """保存消息记录"""
        try:
            records_file = "message_records.json"
            data = {
                "records": [
                    {
                        "candidate_id": r.candidate_id,
                        "candidate_name": r.candidate_name,
                        "message_content": r.message_content,
                        "status": r.status.value,
                        "timestamp": r.timestamp.isoformat(),
                        "error_message": r.error_message,
                        "reply_content": r.reply_content,
                        "reply_time": r.reply_time.isoformat() if r.reply_time else None
                    }
                    for r in self.message_records
                ],
                "daily_sent_count": self.daily_sent_count,
                "hourly_sent_count": self.hourly_sent_count,
                "last_reset_time": self.last_reset_time.isoformat()
            }

            with open(records_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info("消息记录已保存")

        except Exception as e:
            logger.error(f"保存消息记录失败: {e}")

    def get_statistics(self) -> Dict:
        """获取发送统计"""
        total = len(self.message_records)
        if total == 0:
            return {
                "total_sent": 0,
                "reply_rate": 0.0,
                "success_rate": 0.0,
                "today_sent": self.daily_sent_count,
                "this_hour_sent": self.hourly_sent_count
            }

        sent_count = sum(1 for r in self.message_records if r.status == MessageStatus.SENT)
        replied_count = sum(1 for r in self.message_records if r.status == MessageStatus.REPLIED)

        return {
            "total_sent": sent_count,
            "replied": replied_count,
            "reply_rate": (replied_count / sent_count * 100) if sent_count > 0 else 0,
            "success_rate": (sent_count / total * 100) if total > 0 else 0,
            "today_sent": self.daily_sent_count,
            "this_hour_sent": self.hourly_sent_count
        }