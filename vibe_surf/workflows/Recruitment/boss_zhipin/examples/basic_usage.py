"""
Boss 直聘自动化基础使用示例

这个示例展示了如何快速开始使用 Boss 直聘自动化系统。
"""

import asyncio
import logging
from datetime import time

from vibe_surf.workflows.Recruitment.boss_zhipin import BossZhipinAutomation

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

async def basic_example():
    """基础使用示例"""
    print("=" * 50)
    print("Boss 直聘自动化基础使用示例")
    print("=" * 50)

    # 1. 创建自动化实例
    automation = BossZhipinAutomation()

    try:
        # 2. 初始化系统
        print("\n1. 正在初始化系统...")
        if not await automation.initialize(headless=False):
            print("初始化失败！")
            return

        print("✅ 系统初始化成功")

        # 3. 配置运行参数
        print("\n2. 配置运行参数...")
        automation.workflow_config.search_position = "前端开发工程师"
        automation.workflow_config.search_city = "101010100"  # 北京
        automation.workflow_config.search_experience = "3"
        automation.workflow_config.max_pages = 2
        automation.workflow_config.mode = "semi"  # 半自动模式
        automation.workflow_config.dry_run = True  # 试运行（不实际发送）
        print("✅ 配置完成")

        # 4. 检查登录状态
        print("\n3. 检查登录状态...")
        if await automation._check_login():
            print("✅ 已登录")
        else:
            print("❌ 未登录，请手动登录后重试")
            return

        # 5. 执行一次自动化流程
        print("\n4. 开始执行自动化流程...")
        result = await automation.run_once()

        # 6. 显示结果
        print("\n5. 执行结果：")
        print(f"   - 搜索到候选人: {result['search_results']} 个")
        print(f"   - 匹配候选人: {result['matched_candidates']} 个")
        print(f"   - 发送消息: {result['messages_sent']} 条")
        print(f"   - 处理回复: {result['replies_processed']} 条")
        print(f"   - 错误数: {result['errors']} 个")

        # 7. 显示统计信息
        print("\n6. 详细统计：")
        if automation.messenger:
            msg_stats = automation.messenger.get_statistics()
            print(f"   - 今日已发送: {msg_stats['today_sent']} 条")
            print(f"   - 本小时已发送: {msg_stats['this_hour_sent']} 条")

        if automation.anti_detection:
            risk_report = automation.anti_detection.get_risk_report()
            print(f"   - 当前风险等级: {risk_report['current_risk_level']}")
            print(f"   - 操作成功率: {risk_report['success_rate']:.2f}%")

    except Exception as e:
        logger.error(f"运行出错: {e}")

    finally:
        # 8. 清理资源
        print("\n7. 清理资源...")
        await automation.stop()
        print("✅ 已停止")

async def custom_template_example():
    """自定义消息模板示例"""
    print("\n" + "=" * 50)
    print("自定义消息模板示例")
    print("=" * 50)

    from vibe_surf.workflows.Recruitment.boss_zhipin.config import BossZhipinConfig

    # 创建自定义配置
    config = BossZhipinConfig()
    config.company_name = "示例科技公司"
    config.position_name = "技术负责人"

    # 自定义消息模板
    config.messages.invitation_templates = [
        """您好！我是{company_name}的{position_name}。

在 Boss 直聘上看到您的简历，您在{candidate_position}领域的经验给我们留下深刻印象。

我们正在寻找优秀的{target_position}加入团队，主要负责：
- 核心功能开发
- 技术架构优化
- 团队技术分享

我们提供：
- 有竞争力的薪资（{salary_range}）
- 技术成长空间
- 弹性工作制度
- 期权激励

如果您对技术挑战和成长有兴趣，期待与您聊聊！""",
    ]

    # 自定义问答模板
    config.messages.qa_templates.update({
        "公司规模": "我们是一家发展中的科技公司，目前团队约50人，技术团队占60%。",
        "技术栈": "前端使用 React/TypeScript/Next.js，后端是 Node.js/GraphQL，云服务在 AWS。",
        "加班情况": "我们崇尚工作生活平衡，一般不需要加班。项目紧急时会有适度加班，并发放加班费或安排调休。"
    })

    # 使用自定义配置创建自动化实例
    automation = BossZhipinAutomation(config)

    try:
        if await automation.initialize(headless=False):
            # 设置运行参数
            automation.workflow_config.dry_run = True
            automation.workflow_config.search_position = "高级前端工程师"

            # 运行一次
            result = await automation.run_once()
            print(f"\n使用自定义模板运行结果：")
            print(f"匹配到 {result['matched_candidates']} 个候选人")

    finally:
        await automation.stop()

async def scheduled_run_example():
    """定时运行示例"""
    print("\n" + "=" * 50)
    print("定时运行示例")
    print("=" * 50)

    automation = BossZhipinAutomation()

    try:
        if await automation.initialize(headless=False):
            # 配置定时运行
            automation.workflow_config.search_position = "React 开发"
            automation.workflow_config.max_pages = 1
            automation.workflow_config.run_interval = 1800  # 30分钟运行一次
            automation.workflow_config.start_time = time(9, 0)  # 9点开始
            automation.workflow_config.end_time = time(18, 0)   # 18点结束

            print("开始定时运行模式（按 Ctrl+C 停止）...")

            # 运行4小时
            await automation.run_continuous(duration_hours=4)

    except KeyboardInterrupt:
        print("\n收到中断信号，停止运行")
    finally:
        await automation.stop()

async def monitoring_example():
    """监控示例"""
    print("\n" + "=" * 50)
    print("监控和统计示例")
    print("=" * 50)

    automation = BossZhipinAutomation()

    try:
        if await automation.initialize(headless=False):
            # 运行几次以生成数据
            automation.workflow_config.dry_run = True
            for i in range(3):
                print(f"\n--- 第 {i+1} 次运行 ---")
                result = await automation.run_once()
                print(f"搜索到: {result['search_results']} 个候选人")
                await asyncio.sleep(2)  # 短暂等待

            # 显示详细统计
            print("\n--- 详细统计报告 ---")

            # 消息发送统计
            if automation.messenger:
                msg_stats = automation.messenger.get_statistics()
                print("\n消息发送统计：")
                print(f"  总发送数: {msg_stats['total_sent']}")
                print(f"  已回复数: {msg_stats['replied']}")
                print(f"  回复率: {msg_stats['reply_rate']:.2f}%")
                print(f"  成功率: {msg_stats['success_rate']:.2f}%")

            # 防检测统计
            if automation.anti_detection:
                risk_report = automation.anti_detection.get_risk_report()
                print("\n风险监控报告：")
                print(f"  当前风险等级: {risk_report['current_risk_level']}")
                print(f"  24小时操作数: {risk_report['action_count_24h']}")
                print(f"  风险事件数: {risk_report['total_risks']}")
                print(f"  风险分布: {risk_report['risk_distribution']}")

            # 系统状态
            status = automation.get_status()
            print("\n系统状态：")
            print(f"  运行中: {status['is_running']}")
            print(f"  运行时长: {status['uptime']}")
            print(f"  处理候选人: {status['stats']['candidates_processed']}")

    finally:
        await automation.stop()

async def main():
    """主函数 - 运行所有示例"""
    print("Boss 直聘自动化系统示例")
    print("请选择要运行的示例：")
    print("1. 基础使用示例")
    print("2. 自定义消息模板示例")
    print("3. 定时运行示例")
    print("4. 监控和统计示例")
    print("5. 运行所有示例")

    choice = input("\n请输入选项 (1-5): ").strip()

    if choice == "1":
        await basic_example()
    elif choice == "2":
        await custom_template_example()
    elif choice == "3":
        await scheduled_run_example()
    elif choice == "4":
        await monitoring_example()
    elif choice == "5":
        print("\n运行所有示例（每个之间有间隔）...")
        await basic_example()
        await asyncio.sleep(2)
        await custom_template_example()
        await asyncio.sleep(2)
        await monitoring_example()
    else:
        print("无效选项，运行基础示例...")
        await basic_example()

if __name__ == "__main__":
    # 直接运行基础示例
    # asyncio.run(basic_example())

    # 或运行交互式菜单
    asyncio.run(main())