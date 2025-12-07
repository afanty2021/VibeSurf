"""
Boss 直聘自动化主工作流

该模块整合所有功能组件，提供完整的自动化工作流程。
"""

import asyncio
import logging
import json
from typing import Dict, List, Optional, Tuple
from datetime import datetime, time as dt_time
from dataclasses import dataclass, field
from pathlib import Path

from .config import BossZhipinConfig, get_config
from .session_manager import BossZhipinSessionManager
from .matcher import ResumeMatcher, MatchLevel
from .messenger import AutoMessenger
from .qa_system import IntelligentQA
from .anti_detection import AntiDetectionSystem

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('boss_zhipin_automation.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@dataclass
class WorkflowConfig:
    """工作流配置"""
    # 运行模式
    mode: str = "auto"  # auto: 全自动, semi: 半自动, manual: 手动
    dry_run: bool = False  # 是否试运行（不实际发送消息）

    # 搜索配置
    search_position: str = "前端开发"
    search_city: str = "101010100"  # 北京
    search_experience: str = "3"
    max_pages: int = 5
    min_match_level: MatchLevel = MatchLevel.FAIR

    # 运行时间
    start_time: Optional[dt_time] = None
    end_time: Optional[dt_time] = None
    run_interval: int = 3600  # 运行间隔（秒）

    # 输出配置
    save_reports: bool = True
    report_dir: str = "reports"

class BossZhipinAutomation:
    """Boss 直聘自动化主类"""

    def __init__(self, config: Optional[BossZhipinConfig] = None):
        """
        初始化自动化系统

        Args:
            config: Boss 直聘配置，如果不提供则使用默认配置
        """
        self.config = config or get_config()
        self.workflow_config = WorkflowConfig()

        # 初始化各个组件
        self.session: Optional[BossZhipinSessionManager] = None
        self.matcher: Optional[ResumeMatcher] = None
        self.messenger: Optional[AutoMessenger] = None
        self.qa_system: Optional[IntelligentQA] = None
        self.anti_detection: Optional[AntiDetectionSystem] = None

        # 运行状态
        self.is_running = False
        self.stats = {
            "start_time": None,
            "candidates_processed": 0,
            "messages_sent": 0,
            "replies_received": 0,
            "errors": 0
        }

    async def initialize(self,
                        headless: bool = False,
                        user_data_dir: Optional[str] = None) -> bool:
        """
        初始化所有组件

        Args:
            headless: 是否无头模式
            user_data_dir: 用户数据目录

        Returns:
            bool: 是否初始化成功
        """
        try:
            logger.info("正在初始化 Boss 直聘自动化系统...")

            # 1. 初始化会话管理器
            self.session = BossZhipinSessionManager(
                headless=headless,
                user_data_dir=user_data_dir
            )

            if not await self.session.initialize():
                logger.error("会话管理器初始化失败")
                return False

            # 2. 初始化简历匹配器
            self.matcher = ResumeMatcher(self.config)

            # 3. 初始化消息发送器
            self.messenger = AutoMessenger(self.session, self.config)

            # 4. 初始化问答系统
            self.qa_system = IntelligentQA(self.session, self.config)

            # 5. 初始化防检测系统
            self.anti_detection = AntiDetectionSystem(self.session, self.config)

            logger.info("Boss 直聘自动化系统初始化成功")
            return True

        except Exception as e:
            logger.error(f"初始化失败: {e}")
            return False

    async def run_once(self) -> Dict:
        """
        执行一次完整的自动化流程

        Returns:
            Dict: 执行结果统计
        """
        if not all([self.session, self.matcher, self.messenger, self.qa_system, self.anti_detection]):
            raise RuntimeError("系统未初始化")

        logger.info("开始执行自动化流程...")

        stats = {
            "search_results": 0,
            "matched_candidates": 0,
            "messages_sent": 0,
            "replies_processed": 0,
            "errors": 0,
            "start_time": datetime.now()
        }

        try:
            # 1. 检查登录状态
            if not await self._check_login():
                raise RuntimeError("未登录或登录失败")

            # 2. 搜索候选人
            candidates = await self._search_candidates()
            stats["search_results"] = len(candidates)

            # 3. 筛选和匹配
            matched_results = self._match_candidates(candidates)
            stats["matched_candidates"] = len(matched_results)

            # 4. 发送消息
            if not self.workflow_config.dry_run:
                message_stats = await self.messenger.send_to_candidates(
                    matched_results,
                    min_match_level=self.workflow_config.min_match_level
                )
                stats["messages_sent"] = message_stats["sent"]

            # 5. 检查新回复
            reply_stats = await self.qa_system.check_and_reply()
            stats["replies_processed"] = reply_stats["auto_replied"]

            # 6. 生成报告
            if self.workflow_config.save_reports:
                await self._generate_report(stats, matched_results)

            logger.info(f"流程执行完成: {stats}")
            return stats

        except Exception as e:
            logger.error(f"执行流程失败: {e}")
            stats["errors"] += 1
            raise

    async def run_continuous(self, duration_hours: Optional[int] = None):
        """
        持续运行自动化流程

        Args:
            duration_hours: 运行时长（小时），None 表示无限运行
        """
        self.is_running = True
        self.stats["start_time"] = datetime.now()

        logger.info(f"开始持续运行模式，间隔 {self.workflow_config.run_interval} 秒")

        try:
            while self.is_running:
                # 检查运行时间
                if duration_hours:
                    elapsed = (datetime.now() - self.stats["start_time"]).total_seconds()
                    if elapsed > duration_hours * 3600:
                        logger.info("达到预设运行时长，停止运行")
                        break

                # 检查时间窗口
                if not self._is_in_time_window():
                    logger.info("不在运行时间窗口，等待...")
                    await asyncio.sleep(300)  # 等待5分钟
                    continue

                # 检查风险等级
                risk_level = self.anti_detection._assess_risk()
                if risk_level.value >= 3:  # HIGH 或 CRITICAL
                    logger.warning(f"风险等级过高 ({risk_level.name})，暂停运行")
                    await asyncio.sleep(self.workflow_config.run_interval * 2)
                    continue

                # 执行一次流程
                try:
                    await self.run_once()
                    self.stats["candidates_processed"] += 1

                    # 等待下次运行
                    logger.info(f"等待 {self.workflow_config.run_interval} 秒后再次运行...")
                    await asyncio.sleep(self.workflow_config.run_interval)

                except Exception as e:
                    logger.error(f"运行出错: {e}")
                    self.stats["errors"] += 1
                    await asyncio.sleep(60)  # 出错后等待1分钟

        except KeyboardInterrupt:
            logger.info("收到中断信号，停止运行")
        finally:
            self.is_running = False

    async def _check_login(self) -> bool:
        """检查登录状态"""
        # 使用防检测系统执行操作
        success, result = await self.anti_detection.execute_with_protection(
            self.session.check_login_status,
            "check_login"
        )

        if success and result:
            logger.info("已登录")
            return True

        # 尝试导航并登录
        success, _ = await self.anti_detection.execute_with_protection(
            self.session.navigate_to_boss,
            "navigate"
        )

        return success

    async def _search_candidates(self) -> List[Dict]:
        """搜索候选人"""
        all_candidates = []

        for page in range(1, self.workflow_config.max_pages + 1):
            logger.info(f"搜索第 {page} 页...")

            # 使用防检测系统执行搜索
            success, _ = await self.anti_detection.execute_with_protection(
                lambda: self.session.search_candidates(
                    self.workflow_config.search_position,
                    self.workflow_config.search_city,
                    self.workflow_config.search_experience
                ),
                "search"
            )

            if success:
                # 获取候选人列表
                candidates = await self.session.get_candidate_list()
                all_candidates.extend(candidates)

                # 翻页
                if page < self.workflow_config.max_pages:
                    await asyncio.sleep(2)  # 页面等待
            else:
                logger.warning(f"第 {page} 页搜索失败")
                break

        logger.info(f"总共搜索到 {len(all_candidates)} 个候选人")
        return all_candidates

    def _match_candidates(self, candidates: List[Dict]) -> List:
        """筛选和匹配候选人"""
        logger.info(f"开始匹配 {len(candidates)} 个候选人...")

        # 批量匹配
        matched_results = self.matcher.filter_candidates(
            candidates,
            min_match_level=self.workflow_config.min_match_level,
            max_results=100  # 限制最多100个
        )

        logger.info(f"匹配到 {len(matched_results)} 个符合条件的候选人")

        # 生成匹配报告
        report = self.matcher.generate_match_report(matched_results)
        logger.info(f"匹配分布 - 优秀: {report['match_distribution']['excellent']}, "
                   f"良好: {report['match_distribution']['good']}, "
                   f"一般: {report['match_distribution']['fair']}")

        return matched_results

    def _is_in_time_window(self) -> bool:
        """检查是否在运行时间窗口"""
        now = datetime.now().time()
        start = self.workflow_config.start_time or dt_time(9, 0)
        end = self.workflow_config.end_time or dt_time(18, 0)

        return start <= now <= end

    async def _generate_report(self, stats: Dict, matched_results: List):
        """生成运行报告"""
        try:
            report_dir = Path(self.workflow_config.report_dir)
            report_dir.mkdir(exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = report_dir / f"automation_report_{timestamp}.json"

            # 准备报告数据
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "config": {
                    "mode": self.workflow_config.mode,
                    "search_position": self.workflow_config.search_position,
                    "min_match_level": self.workflow_config.min_match_level.name
                },
                "stats": stats,
                "messenger_stats": self.messenger.get_statistics() if self.messenger else {},
                "qa_stats": self.qa_system.get_qa_statistics() if self.qa_system else {},
                "risk_report": self.anti_detection.get_risk_report() if self.anti_detection else {},
                "top_candidates": [
                    {
                        "name": r.candidate.get("name", ""),
                        "score": r.match_score,
                        "level": r.match_level.name
                    }
                    for r in matched_results[:10]
                ]
            }

            # 保存报告
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=2)

            logger.info(f"报告已保存: {report_file}")

        except Exception as e:
            logger.error(f"生成报告失败: {e}")

    async def stop(self):
        """停止自动化系统"""
        logger.info("正在停止自动化系统...")
        self.is_running = False

        # 清理资源
        if self.session:
            await self.session.cleanup()

        logger.info("自动化系统已停止")

    def get_status(self) -> Dict:
        """获取当前状态"""
        return {
            "is_running": self.is_running,
            "uptime": str(datetime.now() - self.stats["start_time"]) if self.stats["start_time"] else "00:00:00",
            "stats": self.stats,
            "config": {
                "mode": self.workflow_config.mode,
                "dry_run": self.workflow_config.dry_run,
                "search_position": self.workflow_config.search_position
            }
        }

# 便捷函数
async def run_automation(config: Optional[Dict] = None,
                         mode: str = "auto",
                         dry_run: bool = False,
                         duration_hours: Optional[int] = None) -> Dict:
    """
    便捷的自动化运行函数

    Args:
        config: 配置字典
        mode: 运行模式
        dry_run: 是否试运行
        duration_hours: 运行时长

    Returns:
        Dict: 运行结果
    """
    # 创建自动化实例
    automation = BossZhipinAutomation()

    # 配置工作流
    if config:
        # 更新配置
        pass  # 实际实现中需要更新配置

    automation.workflow_config.mode = mode
    automation.workflow_config.dry_run = dry_run

    try:
        # 初始化
        if not await automation.initialize():
            return {"success": False, "error": "初始化失败"}

        # 运行
        if duration_hours:
            await automation.run_continuous(duration_hours)
        else:
            result = await automation.run_once()
            return {"success": True, "result": result}

    finally:
        # 停止
        await automation.stop()

# 使用示例
async def main():
    # 创建自动化实例
    automation = BossZhipinAutomation()

    try:
        # 初始化
        if await automation.initialize(headless=False):
            # 配置
            automation.workflow_config.search_position = "前端开发工程师"
            automation.workflow_config.max_pages = 3
            automation.workflow_config.mode = "semi"
            automation.workflow_config.dry_run = True  # 试运行模式

            # 执行一次
            result = await automation.run_once()
            print("执行结果:", result)

            # 或持续运行
            # await automation.run_continuous(duration_hours=8)

    finally:
        await automation.stop()

if __name__ == "__main__":
    asyncio.run(main())