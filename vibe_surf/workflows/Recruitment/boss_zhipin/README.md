# Boss 直聘自动化系统

基于 VibeSurf 的 Boss 直聘智能招聘助手，实现自动化简历筛选、消息发送和智能回复。

## ⚠️ 重要提醒

**使用前请务必了解**：
- 遵守 Boss 直聘的服务条款
- 合理使用自动化功能，避免过度操作
- 建议从半自动化模式开始
- 保护好个人账号安全

## ✨ 主要功能

### 1. 智能简历筛选
- 基于技能、经验、地点等多维度匹配
- 自定义匹配条件和权重
- 自动评分和排序

### 2. 自动化消息发送
- 个性化消息模板
- 智能发送时机控制
- 防检测机制

### 3. 智能问答系统
- 自动识别问题意图
- 预设答案库
- 支持自定义问答

### 4. 防检测保护
- 模拟人类行为
- 操作频率控制
- 异常检测和恢复

## 📦 安装和配置

### 1. 环境要求
```bash
Python 3.11+
Node.js 18+
Chrome/Edge 浏览器
```

### 2. 安装依赖
```bash
pip install vibesurf
# 或
uv pip install vibesurf -U
```

### 3. 配置文件
创建配置文件 `~/.vibesurf/boss_zhipin_config.json`：

```json
{
  "company_name": "你的公司名称",
  "position_name": "招聘负责人",

  "search": {
    "position": "前端开发",
    "city": "101010100",
    "experience": "3",
    "page_limit": 5
  },

  "messages": {
    "invitation_templates": [
      "您好，我是{company_name}的{position_name}。看到您的简历很感兴趣..."
    ],
    "qa_templates": {
      "薪资范围": "我们提供15-25K的薪资范围...",
      "工作地点": "公司位于北京市朝阳区..."
    }
  },

  "behavior": {
    "daily_message_limit": 50,
    "hourly_message_limit": 10,
    "action_interval_min": 2,
    "action_interval_max": 5,
    "enable_mouse_movement": true
  }
}
```

## 🚀 快速开始

### 1. 基础使用
```python
import asyncio
from vibe_surf.workflows.Recruitment.boss_zhipin import BossZhipinAutomation

async def main():
    # 创建自动化实例
    automation = BossZhipinAutomation()

    try:
        # 初始化（会打开浏览器）
        if await automation.initialize(headless=False):
            # 手动登录后运行
            result = await automation.run_once()
            print("运行结果:", result)
    finally:
        await automation.stop()

# 运行
asyncio.run(main())
```

### 2. 持续运行模式
```python
# 配置持续运行
automation.workflow_config.mode = "auto"  # 全自动
automation.workflow_config.max_pages = 3
automation.workflow_config.run_interval = 3600  # 每小时运行一次

# 运行8小时
await automation.run_continuous(duration_hours=8)
```

### 3. 试运行模式（不实际发送消息）
```python
automation.workflow_config.dry_run = True
result = await automation.run_once()
```

## 📝 详细使用指南

### 1. 简历筛选配置

```python
from vibe_surf.workflows.Recruitment.boss_zhipin.matcher import MatchCriteria

# 自定义匹配条件
criteria = MatchCriteria(
    required_skills={"React", "TypeScript", "Node.js"},
    min_experience=3,
    max_experience=8,
    education_level="本科",
    location_preference={"北京", "上海"},
    exclude_keywords={"外包", "驻场"},
    exclude_competitors={"竞争公司A", "竞争公司B"}
)

# 应用到匹配器
matcher.match_criteria = criteria
```

### 2. 消息模板定制

```python
# 个性化消息模板
templates = {
    "优秀候选人": """您好！看到您在{candidate_position}领域有{experience}年经验，
特别是在{strengths}方面与我们的需求高度匹配。

我们正在招聘前端工程师，主要负责{job_responsibilities}。
薪资范围{salary_range}，福利包括{benefits}。

期待您的回复！""",

    "技术专家": """您好！注意到您在{specific_skill}方面的专业能力，
我们正好需要这样的技术专家来带领{team_info}。

如果您对技术挑战和成长感兴趣，欢迎聊聊！"""
}
```

### 3. 智能问答扩展

```python
from vibe_surf.workflows.Recruitment.boss_zhipin.qa_system import IntentType

# 添加自定义问答
qa_system.add_custom_qa(
    question="公司技术栈是什么？",
    answer="我们主要使用 React、TypeScript、Next.js 做前端，"
          "后端是 Node.js + GraphQL，数据库用 PostgreSQL，"
          "部署在 AWS 上。",
    intent_type=IntentType.TECH_STACK
)

# 批量添加问答
custom_qas = [
    ("有期权吗？", "是的，我们有期权激励计划，根据职级和表现授予。"),
    ("团队多大？", "前端团队目前15人，分成3个小组。"),
    ("需要加班吗？", "我们不鼓励加班，项目紧急时会适度加班，有调休。")
]

for q, a in custom_qas:
    qa_system.add_custom_qa(q, a)
```

### 4. 安全策略配置

```python
# 调整防检测参数
config.behavior.daily_message_limit = 30    # 每日最多30条
config.behavior.hourly_message_limit = 5    # 每小时最多5条
config.behavior.action_interval_min = 3     # 最小间隔3秒
config.behavior.action_interval_max = 8     # 最大间隔8秒

# 工作时间设置
config.behavior.work_hours_start = 9       # 9点开始
config.behavior.work_hours_end = 18        # 18点结束
config.behavior.avoid_lunch = True         # 避开午饭时间
```

## 📊 监控和报告

### 1. 实时状态监控
```python
# 获取运行状态
status = automation.get_status()
print(f"运行状态: {status['is_running']}")
print(f"已处理候选人: {status['stats']['candidates_processed']}")
print(f"已发送消息: {status['stats']['messages_sent']}")

# 获取风险报告
risk_report = automation.anti_detection.get_risk_report()
print(f"当前风险等级: {risk_report['current_risk_level']}")
print(f"成功率: {risk_report['success_rate']:.2f}%")
```

### 2. 查看详细统计
```python
# 消息发送统计
msg_stats = automation.messenger.get_statistics()
print(f"回复率: {msg_stats['reply_rate']:.2f}%")

# 问答系统统计
qa_stats = automation.qa_system.get_qa_statistics()
print(f"自动回复率: {qa_stats['auto_reply_rate']:.2f}%")
print(f"问题分布: {qa_stats['intent_distribution']}")
```

## 🔧 高级功能

### 1. 分批处理策略
```python
# 分页处理大量候选人
async def process_in_batches():
    automation.workflow_config.max_pages = 1  # 每次只处理1页

    for batch in range(5):  # 处理5批
        result = await automation.run_once()
        print(f"批次 {batch + 1} 完成，发送 {result['messages_sent']} 条消息")

        # 批次间等待更长时间
        await asyncio.sleep(3600)  # 等待1小时
```

### 2. 条件触发模式
```python
# 只在有新候选人时运行
async def conditional_run():
    # 先搜索但不发送
    automation.workflow_config.dry_run = True
    result = await automation.run_once()

    # 如果有匹配的候选人
    if result['matched_candidates'] > 0:
        print(f"发现 {result['matched_candidates']} 个匹配候选人")

        # 切换到实际发送模式
        automation.workflow_config.dry_run = False
        result = await automation.run_once()
```

### 3. 集成外部系统
```python
# 导出数据到其他系统
async def export_to_ats():
    # 获取匹配的候选人
    matched_results = matcher.filter_candidates(candidates)

    # 转换为 ATS 格式
    ats_data = []
    for result in matched_results:
        candidate = {
            "name": result.candidate['name'],
            "position": result.candidate['position'],
            "company": result.candidate['company'],
            "match_score": result.match_score,
            "contact_status": "待联系"
        }
        ats_data.append(candidate)

    # 发送到 ATS 系统
    await send_to_ats(ats_data)
```

## ⚠️ 最佳实践

### 1. 安全建议
- 始终从试运行模式开始
- 设置合理的发送限制
- 定期检查风险报告
- 保持会话更新

### 2. 效率优化
- 精确设置匹配条件
- 优化消息模板
- 合理安排运行时间
- 定期更新问答库

### 3. 避免封号
- 不要全天候运行
- 模拟真实用户行为
- 响应系统警告
- 保留手动操作

## 🔍 故障排除

### 1. 常见问题

**Q: 提示需要验证码？**
A: 暂停运行，手动完成验证，等待30分钟后继续。

**Q: 消息发送失败？**
A: 检查网络连接，确认已登录，查看错误日志。

**Q: 匹配结果不准确？**
A: 调整匹配条件，检查关键词设置，优化评分权重。

**Q: 运行速度慢？**
A: 减少搜索页数，简化匹配逻辑，检查网络状况。

### 2. 日志查看
```bash
# 查看运行日志
tail -f boss_zhipin_automation.log

# 查看错误信息
grep ERROR boss_zhipin_automation.log
```

### 3. 数据恢复
```python
# 从保存的状态恢复
automation.session._load_session()
automation.messenger._load_records()
```

## 📄 更新日志

### v1.0.0
- 初始版本发布
- 基础自动化功能
- 防检测机制
- 智能问答系统

## 📞 支持

如有问题或建议，请：
1. 查看本文档的故障排除部分
2. 检查日志文件
3. 提交 Issue 到 GitHub

## 📝 免责声明

本工具仅用于合法的招聘活动，使用者需要：
- 遵守相关法律法规
- 遵守平台服务条款
- 承担使用风险
- 保护账号安全

开发者不对因使用本工具导致的任何问题承担责任。