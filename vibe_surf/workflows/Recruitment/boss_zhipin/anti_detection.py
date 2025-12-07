"""
防检测和安全机制模块

该模块实现各种防检测策略，保护账号安全，
包括行为模拟、频率控制、异常检测、安全策略等。
"""

import asyncio
import random
import time
import json
import logging
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import hmac

from .session_manager import BossZhipinSessionManager
from .config import BossZhipinConfig

logger = logging.getLogger(__name__)

class RiskLevel(Enum):
    """风险级别"""
    LOW = 1        # 低风险
    MEDIUM = 2     # 中风险
    HIGH = 3       # 高风险
    CRITICAL = 4   # 严重风险

class DetectionType(Enum):
    """检测类型"""
    RATE_LIMIT = "rate_limit"        # 频率限制
    BEHAVIOR_PATTERN = "behavior"    # 行为模式
    FINGERPRINT = "fingerprint"      # 浏览器指纹
    CAPTCHA = "captcha"              # 验证码
    ACCOUNT_LOCK = "account_lock"    # 账号锁定
    IP_BLOCK = "ip_block"            # IP 封禁

@dataclass
class RiskEvent:
    """风险事件"""
    type: DetectionType
    level: RiskLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict = field(default_factory=dict)

@dataclass
class ActionPattern:
    """行为模式"""
    action_type: str
    avg_interval: float
    variance: float
    typical_hours: List[int]
    max_per_hour: int
    max_per_day: int

class AntiDetectionSystem:
    """防检测系统"""

    def __init__(self,
                 session: BossZhipinSessionManager,
                 config: BossZhipinConfig):
        """
        初始化防检测系统

        Args:
            session: Boss 直聘会话管理器
            config: 配置信息
        """
        self.session = session
        self.config = config
        self.risk_events: List[RiskEvent] = []
        self.action_history: List[Dict] = []
        self.session_fingerprint = None

        # 初始化行为模式
        self._init_behavior_patterns()

        # 初始化安全策略
        self._init_security_strategies()

    def _init_behavior_patterns(self):
        """初始化行为模式"""
        self.behavior_patterns = {
            "click": ActionPattern(
                action_type="click",
                avg_interval=2.0,
                variance=0.5,
                typical_hours=list(range(9, 19)),  # 工作时间
                max_per_hour=60,
                max_per_day=500
            ),
            "scroll": ActionPattern(
                action_type="scroll",
                avg_interval=1.5,
                variance=0.3,
                typical_hours=list(range(9, 19)),
                max_per_hour=100,
                max_per_day=800
            ),
            "type": ActionPattern(
                action_type="type",
                avg_interval=0.1,
                variance=0.05,
                typical_hours=list(range(9, 19)),
                max_per_hour=1000,
                max_per_day=5000
            ),
            "message": ActionPattern(
                action_type="message",
                avg_interval=180,  # 3分钟
                variance=60,       # 1分钟方差
                typical_hours=[10, 11, 14, 15, 16, 17],
                max_per_hour=self.config.behavior.hourly_message_limit,
                max_per_day=self.config.behavior.daily_message_limit
            )
        }

    def _init_security_strategies(self):
        """初始化安全策略"""
        self.security_strategies = {
            "rate_limiter": self._rate_limiting_strategy,
            "behavior_normalizer": self._behavior_normalization_strategy,
            "fingerprint_manager": self._fingerprint_management_strategy,
            "anomaly_detector": self._anomaly_detection_strategy,
            "recovery_handler": self._recovery_strategy
        }

    async def execute_with_protection(self,
                                    action: Callable,
                                    action_type: str,
                                    *args,
                                    **kwargs) -> Tuple[bool, any]:
        """
        带保护机制执行操作

        Args:
            action: 要执行的操作
            action_type: 操作类型
            *args: 操作参数
            **kwargs: 操作参数

        Returns:
            Tuple[bool, any]: (是否成功, 结果)
        """
        try:
            # 1. 检查风险等级
            risk_level = self._assess_risk()
            if risk_level == RiskLevel.CRITICAL:
                await self._handle_critical_risk()
                return False, "Risk level too high"

            # 2. 应用频率限制
            if not await self._apply_rate_limit(action_type):
                return False, "Rate limit exceeded"

            # 3. 行为标准化
            await self._normalize_behavior(action_type)

            # 4. 执行操作
            start_time = time.time()
            result = await action(*args, **kwargs)
            execution_time = time.time() - start_time

            # 5. 记录行为
            self._record_action(action_type, execution_time, True)

            # 6. 异常检测
            await self._detect_anomalies()

            return True, result

        except Exception as e:
            # 记录失败
            self._record_action(action_type, 0, False, str(e))

            # 分析异常
            await self._analyze_exception(e)

            return False, str(e)

    async def _rate_limiting_strategy(self, action_type: str) -> bool:
        """频率限制策略"""
        pattern = self.behavior_patterns.get(action_type)
        if not pattern:
            return True

        now = datetime.now()

        # 检查小时限制
        hour_actions = [
            a for a in self.action_history
            if (a['type'] == action_type and
                a['timestamp'].hour == now.hour and
                a['timestamp'].date() == now.date())
        ]

        if len(hour_actions) >= pattern.max_per_hour:
            self._add_risk_event(
                DetectionType.RATE_LIMIT,
                RiskLevel.HIGH,
                f"Hourly rate limit exceeded for {action_type}",
                {"count": len(hour_actions), "limit": pattern.max_per_hour}
            )
            return False

        # 检查日限制
        day_actions = [
            a for a in self.action_history
            if (a['type'] == action_type and
                a['timestamp'].date() == now.date())
        ]

        if len(day_actions) >= pattern.max_per_day:
            self._add_risk_event(
                DetectionType.RATE_LIMIT,
                RiskLevel.CRITICAL,
                f"Daily rate limit exceeded for {action_type}",
                {"count": len(day_actions), "limit": pattern.max_per_day}
            )
            return False

        # 计算下次操作的延迟
        recent_actions = [
            a for a in self.action_history
            if a['type'] == action_type and
               (now - a['timestamp']).total_seconds() < 300  # 5分钟内
        ]

        if recent_actions:
            # 计算平均间隔
            intervals = [
                (recent_actions[i]['timestamp'] - recent_actions[i-1]['timestamp']).total_seconds()
                for i in range(1, len(recent_actions))
            ]

            if intervals:
                avg_interval = sum(intervals) / len(intervals)
                # 如果间隔太小，增加延迟
                if avg_interval < pattern.avg_interval * 0.5:
                    delay = pattern.avg_interval - avg_interval
                    logger.info(f"Adding delay {delay:.2f}s for {action_type}")
                    await asyncio.sleep(delay)

        return True

    async def _behavior_normalization_strategy(self, action_type: str):
        """行为标准化策略"""
        # 模拟人类行为的随机性
        if random.random() < 0.1:  # 10% 的概率进行额外操作
            await self._simulate_random_action()

        # 随机鼠标移动
        if action_type in ['click', 'message'] and self.config.behavior.enable_mouse_movement:
            await self._random_mouse_movement()

        # 随机滚动
        if action_type == 'message' and self.config.behavior.random_scroll:
            await self._random_scroll()

    async def _fingerprint_management_strategy(self):
        """指纹管理策略"""
        if not self.session_fingerprint:
            self.session_fingerprint = self._generate_fingerprint()

        # 定期更新某些指纹特征
        if random.random() < 0.05:  # 5% 概率更新
            await self._update_fingerprint()

    async def _anomaly_detection_strategy(self):
        """异常检测策略"""
        anomalies = []

        # 检测异常频率
        current_actions = len([
            a for a in self.action_history
            if (datetime.now() - a['timestamp']).total_seconds() < 3600
        ])

        if current_actions > 200:
            anomalies.append({
                "type": "high_frequency",
                "value": current_actions,
                "threshold": 200
            })

        # 检测异常模式
        if len(self.action_history) > 10:
            recent_failures = sum(
                1 for a in self.action_history[-10:]
                if not a.get('success', True)
            )

            if recent_failures > 5:
                anomalies.append({
                    "type": "high_failure_rate",
                    "value": recent_failures,
                    "threshold": 5
                })

        # 处理异常
        for anomaly in anomalies:
            self._handle_anomaly(anomaly)

    async def _recovery_strategy(self):
        """恢复策略"""
        # 如果检测到风险，执行恢复操作
        if self.risk_events:
            recent_risks = [
                e for e in self.risk_events
                if (datetime.now() - e.timestamp).total_seconds() < 300
            ]

            if recent_risks:
                # 暂停操作
                pause_time = min(len(recent_risks) * 30, 300)  # 最多暂停5分钟
                logger.warning(f"Detected risks, pausing for {pause_time} seconds")
                await asyncio.sleep(pause_time)

                # 清理会话
                await self._cleanup_session()

    async def _apply_rate_limit(self, action_type: str) -> bool:
        """应用频率限制"""
        return await self.security_strategies["rate_limiter"](action_type)

    async def _normalize_behavior(self, action_type: str):
        """标准化行为"""
        await self.security_strategies["behavior_normalizer"](action_type)

    async def _detect_anomalies(self):
        """检测异常"""
        await self.security_strategies["anomaly_detector"]()

    def _assess_risk(self) -> RiskLevel:
        """评估风险等级"""
        # 获取最近的风险事件
        recent_risks = [
            e for e in self.risk_events
            if (datetime.now() - e.timestamp).total_seconds() < 3600
        ]

        if not recent_risks:
            return RiskLevel.LOW

        # 根据风险事件数量和级别评估
        critical_count = sum(1 for r in recent_risks if r.level == RiskLevel.CRITICAL)
        high_count = sum(1 for r in recent_risks if r.level == RiskLevel.HIGH)

        if critical_count > 0:
            return RiskLevel.CRITICAL
        elif high_count > 2:
            return RiskLevel.HIGH
        elif high_count > 0 or len(recent_risks) > 5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _add_risk_event(self, type: DetectionType, level: RiskLevel, message: str, details: Dict = None):
        """添加风险事件"""
        event = RiskEvent(
            type=type,
            level=level,
            message=message,
            details=details or {}
        )
        self.risk_events.append(event)
        logger.warning(f"Risk event: {level.name} - {message}")

    async def _handle_critical_risk(self):
        """处理严重风险"""
        logger.error("Critical risk detected, stopping operations")
        await self._emergency_stop()

    async def _emergency_stop(self):
        """紧急停止"""
        # 保存状态
        await self._save_state()

        # 清理会话
        await self.session.cleanup()

        # 等待人工干预
        raise Exception("Emergency stop triggered due to critical risk")

    def _record_action(self, action_type: str, duration: float, success: bool, error: str = None):
        """记录操作"""
        action = {
            "type": action_type,
            "timestamp": datetime.now(),
            "duration": duration,
            "success": success,
            "error": error
        }
        self.action_history.append(action)

        # 限制历史记录数量
        if len(self.action_history) > 1000:
            self.action_history = self.action_history[-500:]

    async def _simulate_random_action(self):
        """模拟随机操作"""
        actions = [
            self._random_mouse_movement,
            self._random_scroll,
            self._random_wait,
            self._random_tab_change
        ]

        if random.random() < 0.3:  # 30% 概率执行
            action = random.choice(actions)
            try:
                await action()
            except Exception as e:
                logger.debug(f"Random action failed: {e}")

    async def _random_mouse_movement(self):
        """随机鼠标移动"""
        try:
            # 生成随机坐标
            x = random.randint(100, 1200)
            y = random.randint(100, 800)

            # 模拟人类移动路径（贝塞尔曲线）
            steps = 10
            for i in range(steps):
                progress = i / steps
                # 添加随机偏移
                offset_x = random.randint(-20, 20)
                offset_y = random.randint(-20, 20)
                curr_x = x * progress + offset_x
                curr_y = y * progress + offset_y

                await self.session.page.mouse.move(curr_x, curr_y)
                await asyncio.sleep(0.01)

        except Exception as e:
            logger.debug(f"Mouse movement failed: {e}")

    async def _random_scroll(self):
        """随机滚动"""
        try:
            scroll_distance = random.randint(100, 500)
            scroll_direction = random.choice(['up', 'down'])

            if scroll_direction == 'down':
                await self.session.page.evaluate(f"window.scrollBy(0, {scroll_distance})")
            else:
                await self.session.page.evaluate(f"window.scrollBy(0, -{scroll_distance})")

            await asyncio.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            logger.debug(f"Scroll failed: {e}")

    async def _random_wait(self):
        """随机等待"""
        wait_time = random.uniform(0.5, 2.0)
        await asyncio.sleep(wait_time)

    async def _random_tab_change(self):
        """随机标签切换（如果有多个标签）"""
        # 这里可以实现标签切换逻辑
        pass

    def _generate_fingerprint(self) -> str:
        """生成浏览器指纹"""
        # 基于多个因素生成唯一指纹
        factors = [
            str(time.time()),
            str(random.random()),
            "BossZhipinBot",
            str(self.session.browser.user_agent if self.session.browser else "")
        ]

        fingerprint_data = ":".join(factors)
        fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()

        return fingerprint

    async def _update_fingerprint(self):
        """更新指纹特征"""
        try:
            # 随机修改一些可变的指纹特征
            await self.session.page.evaluate("""
                // 随机修改屏幕分辨率
                Object.defineProperty(screen, 'availWidth', {
                    get: () => Math.floor(Math.random() * 100) + 1800
                });

                // 随机修改时区
                Object.defineProperty(Intl.DateTimeFormat.prototype, 'resolvedOptions', {
                    get: () => ({ timeZone: 'Asia/Shanghai' })
                });
            """)
        except Exception as e:
            logger.debug(f"Update fingerprint failed: {e}")

    def _handle_anomaly(self, anomaly: Dict):
        """处理异常"""
        anomaly_type = anomaly["type"]
        value = anomaly["value"]
        threshold = anomaly["threshold"]

        logger.warning(f"Anomaly detected: {anomaly_type} (value: {value}, threshold: {threshold})")

        # 添加风险事件
        if anomaly_type == "high_frequency":
            self._add_risk_event(
                DetectionType.BEHAVIOR_PATTERN,
                RiskLevel.MEDIUM,
                "Unusually high operation frequency",
                anomaly
            )
        elif anomaly_type == "high_failure_rate":
            self._add_risk_event(
                DetectionType.ACCOUNT_LOCK,
                RiskLevel.HIGH,
                "High failure rate detected",
                anomaly
            )

    async def _analyze_exception(self, exception: Exception):
        """分析异常"""
        error_msg = str(exception).lower()

        # 检测特定类型的错误
        if "captcha" in error_msg or "验证码" in error_msg:
            self._add_risk_event(
                DetectionType.CAPTCHA,
                RiskLevel.HIGH,
                "CAPTCHA detected",
                {"error": str(exception)}
            )

        elif "rate limit" in error_msg or "频率" in error_msg:
            self._add_risk_event(
                DetectionType.RATE_LIMIT,
                RiskLevel.MEDIUM,
                "Rate limit triggered",
                {"error": str(exception)}
            )

        elif "blocked" in error_msg or "封禁" in error_msg:
            self._add_risk_event(
                DetectionType.IP_BLOCK,
                RiskLevel.CRITICAL,
                "IP blocked",
                {"error": str(exception)}
            )

        elif "account locked" in error_msg or "账号锁定" in error_msg:
            self._add_risk_event(
                DetectionType.ACCOUNT_LOCK,
                RiskLevel.CRITICAL,
                "Account locked",
                {"error": str(exception)}
            )

    async def _cleanup_session(self):
        """清理会话"""
        try:
            # 清理 cookies
            await self.session.context.clear_cookies()

            # 清理本地存储
            await self.session.page.evaluate("""
                localStorage.clear();
                sessionStorage.clear();
            """)

            logger.info("Session cleaned up")
        except Exception as e:
            logger.error(f"Session cleanup failed: {e}")

    async def _save_state(self):
        """保存状态"""
        try:
            state = {
                "risk_events": [
                    {
                        "type": e.type.value,
                        "level": e.level.value,
                        "message": e.message,
                        "timestamp": e.timestamp.isoformat(),
                        "details": e.details
                    }
                    for e in self.risk_events[-100:]  # 只保存最近100个
                ],
                "action_count": len(self.action_history),
                "last_action": self.action_history[-1].timestamp.isoformat() if self.action_history else None,
                "fingerprint": self.session_fingerprint
            }

            with open("anti_detection_state.json", "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Save state failed: {e}")

    def get_risk_report(self) -> Dict:
        """获取风险报告"""
        # 最近24小时的风险事件
        recent_risks = [
            e for e in self.risk_events
            if (datetime.now() - e.timestamp).total_seconds() < 86400
        ]

        # 风险分布
        risk_distribution = {
            "LOW": 0,
            "MEDIUM": 0,
            "HIGH": 0,
            "CRITICAL": 0
        }

        for risk in recent_risks:
            risk_distribution[risk.level.name] += 1

        # 检测类型分布
        detection_distribution = {}
        for risk in recent_risks:
            detection_type = risk.type.value
            detection_distribution[detection_type] = detection_distribution.get(detection_type, 0) + 1

        return {
            "total_risks": len(recent_risks),
            "risk_distribution": risk_distribution,
            "detection_distribution": detection_distribution,
            "current_risk_level": self._assess_risk().name,
            "action_count_24h": len([
                a for a in self.action_history
                if (datetime.now() - a['timestamp']).total_seconds() < 86400
            ]),
            "success_rate": self._calculate_success_rate(),
            "fingerprint": self.session_fingerprint
        }

    def _calculate_success_rate(self) -> float:
        """计算操作成功率"""
        recent_actions = [
            a for a in self.action_history
            if (datetime.now() - a['timestamp']).total_seconds() < 86400
        ]

        if not recent_actions:
            return 100.0

        success_count = sum(1 for a in recent_actions if a.get('success', True))
        return (success_count / len(recent_actions)) * 100