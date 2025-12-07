"""
智能问答系统

该模块负责自动回复求职者的常见问题，
包括意图识别、答案匹配、个性化回复等。
"""

import asyncio
import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from .session_manager import BossZhipinSessionManager
from .config import BossZhipinConfig

logger = logging.getLogger(__name__)

class IntentType(Enum):
    """问题意图类型"""
    SALARY = "salary"              # 薪资相关
    LOCATION = "location"          # 工作地点
    COMPANY = "company"            # 公司介绍
    TECH_STACK = "tech_stack"      # 技术栈
    BENEFITS = "benefits"          # 福利待遇
    INTERVIEW_PROCESS = "interview" # 面试流程
    WORK_TIME = "work_time"        # 工作时间
    REMOTE_WORK = "remote_work"    # 远程办公
    TEAM = "team"                  # 团队信息
    CAREER_DEVELOPMENT = "career"  # 职业发展
    PROJECT_DETAILS = "project"    # 项目细节
    OTHER = "other"                # 其他问题

@dataclass
class QuestionIntent:
    """问题意图"""
    type: IntentType
    confidence: float  # 置信度 0-1
    keywords: List[str]  # 关键词
    entities: Dict[str, str]  # 提取的实体

@dataclass
class QARecord:
    """问答记录"""
    question: str
    answer: str
    intent: QuestionIntent
    timestamp: datetime = field(default_factory=datetime.now)
    is_auto_reply: bool = True
    candidate_name: str = ""

class IntelligentQA:
    """智能问答系统"""

    def __init__(self,
                 session: BossZhipinSessionManager,
                 config: BossZhipinConfig):
        """
        初始化问答系统

        Args:
            session: Boss 直聘会话管理器
            config: 配置信息
        """
        self.session = session
        self.config = config
        self.qa_records: List[QARecord] = []

        # 初始化关键词和模板
        self._init_keywords()
        self._init_templates()

        # 初始化 TF-IDF 向量器
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=None  # 中文需要自定义停用词
        )
        self._fit_vectorizer()

    def _init_keywords(self):
        """初始化意图关键词"""
        self.intent_keywords = {
            IntentType.SALARY: [
                "薪资", "工资", "薪水", "待遇", "收入", "多少钱", "多少k", "税前",
                "税后", "年终奖", "期权", "股票", "调薪", "涨薪", "待遇怎么样"
            ],
            IntentType.LOCATION: [
                "地址", "地点", "位置", "在哪", "哪里", "办公地点", "上班地点",
                "交通便利", "地铁", "班车", "附近", "具体地址"
            ],
            IntentType.COMPANY: [
                "公司", "介绍一下", "做什么", "业务", "产品", "规模", "人数",
                "发展", "融资", "轮次", "成立", "背景", "团队"
            ],
            IntentType.TECH_STACK: [
                "技术栈", "技术", "框架", "语言", "工具", "架构", "开发",
                "前端", "后端", "数据库", "服务器", "部署"
            ],
            IntentType.BENEFITS: [
                "福利", "五险", "一金", "保险", "公积金", "年假", "假期",
                "团建", "活动", "培训", "学习", "补贴", "餐补", "交通"
            ],
            IntentType.INTERVIEW_PROCESS: [
                "面试", "流程", "几轮", "面试官", "技术面", "hr面", "终面",
                "复试", "初试", "电话面", "视频面", "现场面"
            ],
            IntentType.WORK_TIME: [
                "上班", "下班", "工作时间", "几点", "打卡", "加班", "996",
                "007", "弹性", "双休", "单休", "大小周"
            ],
            IntentType.REMOTE_WORK: [
                "远程", "居家", "在家", " WFH", "work from home",
                "远程办公", "居家办公"
            ],
            IntentType.TEAM: [
                "团队", "部门", "同事", "领导", "老板", "主管", "成员",
                "多少人", "组成", "氛围", "文化"
            ],
            IntentType.CAREER_DEVELOPMENT: [
                "发展", "晋升", "成长", "机会", "空间", "路径", "规划",
                "职业发展", "晋升通道", "技术路线"
            ]
        }

    def _init_templates(self):
        """初始化回答模板"""
        self.answer_templates = {
            IntentType.SALARY: {
                "default": "我们提供有竞争力的薪资，具体范围根据您的能力和经验而定。岗位薪资范围在{salary_range}，还有年终奖和期权激励。",
                "range": "这个岗位的薪资范围是{salary_range}，具体会根据面试评估结果来确定。我们每年都会有调薪机会。",
                "negotiation": "薪资可以根据您的实际情况进行沟通，我们更看重候选人的整体能力。除了基本薪资，还有丰富的福利待遇。"
            },
            IntentType.LOCATION: {
                "default": "公司位于{location}，{location_detail}，交通便利。",
                "transport": "公司地址是{location}{location_detail}，最近的地铁站是{metro_station}，步行约{walk_time}分钟。",
                "parking": "公司提供{parking_info}，开车的话也比较方便。"
            },
            IntentType.COMPANY: {
                "default": "我们是一家{company_type}，专注于{field}领域。公司成立于{founded_year}，目前团队规模约{team_size}人。",
                "business": "我们的主要业务包括{business_description}。在行业中处于{market_position}地位。",
                "culture": "公司文化注重{culture_points}，我们相信好的文化能够帮助员工更好地成长。"
            },
            IntentType.TECH_STACK: {
                "default": "主要技术栈包括{tech_stack}。我们注重技术创新，会定期进行技术分享。",
                "frontend": "前端主要使用{frontend_tech}，我们鼓励尝试新技术和最佳实践。",
                "backend": "后端采用{backend_tech}，架构设计注重{architecture_principles}。",
                "devops": "我们使用{devops_tools}进行开发部署，实现了{deployment_frequency}。"
            },
            IntentType.BENEFITS: {
                "default": "我们提供完善的福利体系，包括五险一金、带薪年假、弹性工作、定期团建等。",
                "insurance": "除了五险一金，我们还提供{additional_insurance}，保障员工的健康。",
                "leave": "年假{annual_leave}天起，根据司龄增加。还有{other_leaves}等特殊假期。",
                "development": "我们重视员工成长，提供{training_opportunities}，支持参加{external_training}。"
            },
            IntentType.INTERVIEW_PROCESS: {
                "default": "面试流程一般是：技术初试 → 技术复试 → HR面试 → offer。整个过程约1-2周。",
                "technical": "技术面试主要考察{technical_focus}，建议准备{preparation_tips}。",
                "timeline": "如果面试通过，我们会在{decision_days}内给出反馈。offer会在{offer_days}内发出。"
            },
            IntentType.WORK_TIME: {
                "default": "工作时间是周一至周五 {work_hours}，周末双休。",
                "flexible": "我们实行弹性工作制，核心工作时间是{core_hours}，可以灵活安排上下班时间。",
                "overtime": "我们不鼓励加班，如确有需要会支付加班费或安排调休。"
            },
            IntentType.REMOTE_WORK: {
                "default": "目前是全职办公模式，特殊情况下可以申请临时远程。",
                "hybrid": "我们采用{remote_policy}模式，每周可以有{remote_days}天远程办公。",
                "requirement": "岗位需要{office_requirement}，因此不能完全远程。"
            },
            IntentType.TEAM: {
                "default": "团队目前有{team_size}人，氛围{team_culture}。",
                "structure": "团队包括{team_composition}，每个人都负责{responsibilities}。",
                "growth": "团队成员平均工作经验{average_experience}，我们有{growth_opportunities}。"
            },
            IntentType.CAREER_DEVELOPMENT: {
                "default": "我们提供清晰的职业发展路径，包括技术和管理双通道。",
                "promotion": "晋升机制基于{promotion_criteria}，通常{promotion_cycle}评估一次。",
                "learning": "公司支持{learning_support}，每年有{learning_budget}用于学习提升。"
            }
        }

    def _fit_vectorizer(self):
        """训练 TF-IDF 向量器"""
        # 准备训练数据（所有问题样本）
        all_questions = []
        for keywords in self.intent_keywords.values():
            all_questions.extend(keywords)

        # 添加配置中的问答
        if hasattr(self.config.messages, 'qa_templates'):
            all_questions.extend(self.config.messages.qa_templates.keys())

        if all_questions:
            self.vectorizer.fit(all_questions)

    def identify_intent(self, question: str) -> QuestionIntent:
        """
        识别问题意图

        Args:
            question: 用户问题

        Returns:
            QuestionIntent: 识别的意图
        """
        # 预处理问题
        processed_question = self._preprocess_question(question)

        # 方法1：关键词匹配
        keyword_scores = self._keyword_match(processed_question)

        # 方法2：TF-IDF 相似度（如果有历史问答）
        similarity_scores = self._similarity_match(processed_question)

        # 综合评分
        final_scores = self._combine_scores(keyword_scores, similarity_scores)

        # 获取最高分的意图
        if final_scores:
            best_intent_type, confidence = max(final_scores.items(), key=lambda x: x[1])
        else:
            best_intent_type = IntentType.OTHER
            confidence = 0.0

        # 提取实体
        entities = self._extract_entities(processed_question)

        return QuestionIntent(
            type=best_intent_type,
            confidence=confidence,
            keywords=self.intent_keywords.get(best_intent_type, []),
            entities=entities
        )

    def _preprocess_question(self, question: str) -> str:
        """预处理问题"""
        # 转换为小写
        question = question.lower()

        # 移除特殊字符
        question = re.sub(r'[^\w\s]', '', question)

        # 使用 jieba 分词
        words = jieba.lcut(question)

        # 停用词过滤（简单的停用词列表）
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}
        words = [w for w in words if w not in stop_words]

        return ' '.join(words)

    def _keyword_match(self, question: str) -> Dict[IntentType, float]:
        """基于关键词匹配计算意图得分"""
        scores = {}
        question_words = set(question.split())

        for intent_type, keywords in self.intent_keywords.items():
            # 计算交集
            matches = question_words.intersection(set(keywords))
            if matches:
                # 得分 = 匹配词数 / 关键词总数
                score = len(matches) / len(keywords)
                scores[intent_type] = score

        return scores

    def _similarity_match(self, question: str) -> Dict[IntentType, float]:
        """基于相似度匹配计算意图得分"""
        if not self.qa_records:
            return {}

        scores = {}
        try:
            # 转换问题为向量
            question_vector = self.vectorizer.transform([question])

            # 计算与历史问题的相似度
            for intent_type in IntentType:
                if intent_type == IntentType.OTHER:
                    continue

                # 获取该意图的历史问题
                intent_questions = [
                    self._preprocess_question(r.question)
                    for r in self.qa_records
                    if r.intent.type == intent_type
                ]

                if intent_questions:
                    # 计算相似度
                    intent_vectors = self.vectorizer.transform(intent_questions)
                    similarities = cosine_similarity(question_vector, intent_vectors)
                    max_similarity = np.max(similarities)
                    if max_similarity > 0.3:  # 阈值
                        scores[intent_type] = max_similarity

        except Exception as e:
            logger.error(f"相似度匹配失败: {e}")

        return scores

    def _combine_scores(self, keyword_scores: Dict, similarity_scores: Dict) -> Dict:
        """综合两种方法的得分"""
        combined = {}

        # 获取所有意图类型
        all_intents = set(keyword_scores.keys()).union(set(similarity_scores.keys()))

        for intent_type in all_intents:
            kw_score = keyword_scores.get(intent_type, 0.0)
            sim_score = similarity_scores.get(intent_type, 0.0)

            # 加权平均（关键词权重更高）
            combined_score = kw_score * 0.7 + sim_score * 0.3
            combined[intent_type] = combined_score

        return combined

    def _extract_entities(self, question: str) -> Dict[str, str]:
        """提取实体信息"""
        entities = {}

        # 提取数字（薪资、经验等）
        numbers = re.findall(r'\d+', question)
        if numbers:
            entities['numbers'] = numbers

        # 提取地点
        cities = ['北京', '上海', '深圳', '广州', '杭州', '成都', '武汉', '南京']
        for city in cities:
            if city in question:
                entities['location'] = city
                break

        # 提取技术关键词
        tech_keywords = ['react', 'vue', 'angular', 'node', 'python', 'java', 'go', 'rust']
        found_techs = []
        for tech in tech_keywords:
            if tech in question.lower():
                found_techs.append(tech)
        if found_techs:
            entities['technologies'] = found_techs

        return entities

    def generate_answer(self, intent: QuestionIntent, candidate_name: str = "") -> str:
        """
        生成回答

        Args:
            intent: 问题意图
            candidate_name: 候选人姓名

        Returns:
            str: 生成的回答
        """
        # 获取回答模板
        templates = self.answer_templates.get(intent.type, {})

        # 根据实体和上下文选择最合适的模板
        if intent.type == IntentType.SALARY and 'numbers' in intent.entities:
            template = templates.get('range', templates.get('default'))
        elif intent.type == IntentType.LOCATION and 'location' in intent.entities:
            template = templates.get('transport', templates.get('default'))
        else:
            template = templates.get('default', '')

        # 如果没有找到模板，使用配置中的模板
        if not template and hasattr(self.config.messages, 'qa_templates'):
            template = self.config.messages.qa_templates.get(
                intent.type.value,
                "感谢您的问题，我会尽快为您解答。"
            )

        # 如果还是没有，使用默认回答
        if not template:
            template = "感谢您的问题，我会尽快为您详细解答。"

        # 填充参数
        params = {
            "salary_range": "15-25K",
            "location": "北京",
            "location_detail": "朝阳区望京SOHO T1",
            "metro_station": "望京",
            "walk_time": "5",
            "parking_info": "地下停车场",
            "company_type": "快速发展的科技公司",
            "field": "互联网招聘",
            "founded_year": "2020",
            "team_size": "50-100",
            "business_description": "智能招聘系统和人才管理平台",
            "market_position": "领先",
            "culture_points": "开放、创新、协作",
            "tech_stack": "React、TypeScript、Node.js、Python",
            "frontend_tech": "React、TypeScript、Vite",
            "backend_tech": "Node.js、Express、PostgreSQL",
            "architecture_principles": "高内聚低耦合",
            "devops_tools": "Docker、Jenkins、K8s",
            "deployment_frequency": "持续部署",
            "additional_insurance": "补充医疗保险",
            "annual_leave": "10",
            "other_leaves": "病假、婚假、产假",
            "training_opportunities": "内部分享、外部培训、技术大会",
            "external_training": "技术认证、行业会议",
            "technical_focus": "技术能力、解决问题的思路",
            "preparation_tips": "算法、数据结构、项目经验",
            "decision_days": "3-5",
            "offer_days": "5-7",
            "work_hours": "9:00-18:00",
            "core_hours": "10:00-16:00",
            "remote_policy": "混合办公",
            "remote_days": "2",
            "office_requirement": "团队协作和快速沟通",
            "team_culture": "开放、互助、成长",
            "team_composition": "前端、后端、产品、设计",
            "responsibilities": "不同模块的开发和维护",
            "average_experience": "3-5年",
            "growth_opportunities": "技术分享、培训、晋升",
            "promotion_criteria": "技术能力、项目贡献、团队协作",
            "promotion_cycle": "半年",
            "learning_support": "技术书籍、在线课程、认证考试",
            "learning_budget": "每年5000元"
        }

        # 根据实体更新参数
        if intent.entities:
            if 'location' in intent.entities:
                params['location'] = intent.entities['location']
            if 'technologies' in intent.entities:
                params['tech_stack'] = '、'.join(intent.entities['technologies'])

        # 填充模板
        try:
            answer = template.format(**params)
        except KeyError as e:
            logger.error(f"模板参数缺失: {e}")
            answer = template

        # 个性化调整
        if candidate_name:
            answer = f"{candidate_name}，" + answer

        # 根据置信度调整
        if intent.confidence < 0.6:
            answer += "\n\n如果回答不够准确，您可以再详细描述一下问题。"

        return answer

    async def auto_reply(self, message: Dict, candidate_name: str = "") -> Optional[str]:
        """
        自动回复消息

        Args:
            message: 消息内容
            candidate_name: 候选人姓名

        Returns:
            Optional[str]: 回复内容，如果不需要回复则返回 None
        """
        try:
            question = message.get("content", "").strip()
            if not question:
                return None

            # 识别意图
            intent = self.identify_intent(question)

            # 如果置信度太低，可能需要人工回复
            if intent.confidence < 0.3:
                logger.info(f"置信度太低 ({intent.confidence})，跳过自动回复")
                return None

            # 生成回答
            answer = self.generate_answer(intent, candidate_name)

            # 记录问答
            qa_record = QARecord(
                question=question,
                answer=answer,
                intent=intent,
                is_auto_reply=True,
                candidate_name=candidate_name
            )
            self.qa_records.append(qa_record)

            logger.info(f"自动回复 {candidate_name}: {intent.type.value} (置信度: {intent.confidence:.2f})")

            return answer

        except Exception as e:
            logger.error(f"自动回复失败: {e}")
            return None

    async def check_and_reply(self) -> Dict[str, int]:
        """
        检查新消息并自动回复

        Returns:
            Dict[str, int]: 回复统计
        """
        stats = {
            "total_messages": 0,
            "auto_replied": 0,
            "need_manual": 0,
            "errors": 0
        }

        try:
            # 检查新消息
            messages = await self.session.check_new_messages()
            stats["total_messages"] = len(messages)

            # 处理每条消息
            for message in messages:
                try:
                    sender = message.get("sender", "")
                    content = message.get("content", "")

                    # 自动回复
                    reply = await self.auto_reply(message, sender)

                    if reply:
                        # 发送回复
                        success = await self.session.reply_message(sender, reply)
                        if success:
                            stats["auto_replied"] += 1
                        else:
                            stats["errors"] += 1
                    else:
                        stats["need_manual"] += 1

                    # 延迟避免过快回复
                    await asyncio.sleep(random.uniform(2, 5))

                except Exception as e:
                    logger.error(f"处理消息失败: {e}")
                    stats["errors"] += 1

        except Exception as e:
            logger.error(f"检查和回复消息失败: {e}")
            stats["errors"] += 1

        return stats

    def add_custom_qa(self, question: str, answer: str, intent_type: IntentType = IntentType.OTHER):
        """
        添加自定义问答

        Args:
            question: 问题
            answer: 回答
            intent_type: 意图类型
        """
        # 识别意图
        intent = self.identify_intent(question)
        intent.type = intent_type  # 覆盖识别结果

        # 添加到记录
        qa_record = QARecord(
            question=question,
            answer=answer,
            intent=intent,
            is_auto_reply=False
        )
        self.qa_records.append(qa_record)

        # 重新训练向量器
        self._fit_vectorizer()

        logger.info(f"添加自定义问答: {question[:30]}...")

    def get_qa_statistics(self) -> Dict:
        """获取问答统计"""
        if not self.qa_records:
            return {
                "total_questions": 0,
                "intent_distribution": {},
                "auto_reply_rate": 0.0,
                "confidence_distribution": {}
            }

        # 意图分布
        intent_counts = {}
        confidence_sum = {}

        for record in self.qa_records:
            intent = record.intent.type.value
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
            confidence_sum[intent] = confidence_sum.get(intent, 0) + record.intent.confidence

        # 自动回复率
        auto_replied = sum(1 for r in self.qa_records if r.is_auto_reply)
        auto_reply_rate = (auto_replied / len(self.qa_records)) * 100

        # 平均置信度
        confidence_distribution = {}
        for intent, count in intent_counts.items():
            avg_confidence = confidence_sum[intent] / count
            confidence_distribution[intent] = round(avg_confidence, 2)

        return {
            "total_questions": len(self.qa_records),
            "intent_distribution": intent_counts,
            "auto_reply_rate": round(auto_reply_rate, 2),
            "confidence_distribution": confidence_distribution
        }