"""
简历筛选和匹配模块

该模块负责根据预设条件筛选和匹配简历，
包括关键词匹配、评分系统、优先级排序等。
"""

import re
import json
import logging
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .config import BossZhipinConfig

logger = logging.getLogger(__name__)

class MatchLevel(Enum):
    """匹配级别"""
    EXCELLENT = 5  # 优秀匹配
    GOOD = 4       # 良好匹配
    FAIR = 3       # 一般匹配
    POOR = 2       # 较差匹配
    REJECT = 1     # 不匹配

@dataclass
class MatchCriteria:
    """匹配条件"""
    # 必须匹配的条件
    required_skills: Set[str] = field(default_factory=set)
    min_experience: int = 0  # 最小工作经验（年）
    max_experience: Optional[int] = None  # 最大工作经验（年）
    education_level: str = ""  # 学历要求
    location_preference: Set[str] = field(default_factory=set)  # 期望地点

    # 优先匹配的条件
    preferred_skills: Set[str] = field(default_factory=set)
    preferred_companies: Set[str] = field(default_factory=set)
    preferred_education: Set[str] = field(default_factory=set)

    # 排除条件
    exclude_keywords: Set[str] = field(default_factory=set)
    exclude_companies: Set[str] = field(default_factory=set)
    max_salary_expectation: Optional[int] = None  # 最大期望薪资

    # 时间条件
    max_inactive_days: int = 30  # 最近活跃天数

@dataclass
class MatchResult:
    """匹配结果"""
    candidate: Dict
    match_level: MatchLevel
    match_score: float  # 0-100
    match_reasons: List[str]
    missing_skills: List[str]
    strength_points: List[str]
    timestamp: datetime = field(default_factory=datetime.now)

class ResumeMatcher:
    """简历匹配器"""

    def __init__(self, config: BossZhipinConfig):
        """
        初始化匹配器

        Args:
            config: Boss 直聘配置
        """
        self.config = config
        self.match_criteria = self._build_criteria()

    def _build_criteria(self) -> MatchCriteria:
        """根据配置构建匹配条件"""
        # 这里可以根据配置文件动态构建
        # 示例数据，实际应该从配置中读取
        return MatchCriteria(
            required_skills={
                "JavaScript", "TypeScript", "React", "Vue",
                "HTML", "CSS", "Node.js"
            },
            min_experience=3,
            education_level="本科",
            location_preference={"北京", "上海", "深圳"},
            preferred_skills={
                "Webpack", "Vite", "微信小程序", "UniApp",
                "Docker", "Git", "CI/CD"
            },
            exclude_keywords={
                "外包", "驻场", "实习", "应届"
            },
            exclude_companies=set(),
            max_inactive_days=30
        )

    async def match_candidate(self, candidate: Dict, resume_detail: Optional[Dict] = None) -> MatchResult:
        """
        匹配候选人

        Args:
            candidate: 候选人基本信息
            resume_detail: 简历详细信息（如果有的话）

        Returns:
            MatchResult: 匹配结果
        """
        try:
            score = 0.0
            reasons = []
            missing_skills = []
            strength_points = []

            # 1. 检查排除条件
            if self._check_exclusions(candidate, resume_detail):
                return MatchResult(
                    candidate=candidate,
                    match_level=MatchLevel.REJECT,
                    match_score=0.0,
                    match_reasons=["不符合排除条件"],
                    missing_skills=[],
                    strength_points=[]
                )

            # 2. 检查活跃时间
            activity_score = self._check_activity(candidate)
            score += activity_score[0]
            if activity_score[1]:
                strength_points.append(activity_score[1])
            elif activity_score[2]:
                reasons.append(activity_score[2])

            # 3. 检查工作经验
            experience_score = self._check_experience(candidate)
            score += experience_score[0]
            if experience_score[1]:
                strength_points.append(experience_score[1])
            elif experience_score[2]:
                reasons.append(experience_score[2])

            # 4. 检查技能匹配
            skill_result = self._check_skills(candidate, resume_detail)
            score += skill_result[0]
            strength_points.extend(skill_result[1])
            reasons.extend(skill_result[2])
            missing_skills.extend(skill_result[3])

            # 5. 检查地点
            location_score = self._check_location(candidate)
            score += location_score[0]
            if location_score[1]:
                strength_points.append(location_score[1])
            elif location_score[2]:
                reasons.append(location_score[2])

            # 6. 检查公司背景
            company_score = self._check_company_background(candidate)
            score += company_score[0]
            if company_score[1]:
                strength_points.append(company_score[1])
            elif company_score[2]:
                reasons.append(company_score[2])

            # 7. 检查薪资期望
            salary_score = self._check_salary_expectation(candidate)
            score += salary_score[0]
            if salary_score[1]:
                strength_points.append(salary_score[1])
            elif salary_score[2]:
                reasons.append(salary_score[2])

            # 8. 确定匹配级别
            match_level = self._determine_match_level(score)

            return MatchResult(
                candidate=candidate,
                match_level=match_level,
                match_score=min(score, 100.0),
                match_reasons=reasons,
                missing_skills=list(set(missing_skills)),
                strength_points=strength_points
            )

        except Exception as e:
            logger.error(f"匹配候选人失败: {e}")
            return MatchResult(
                candidate=candidate,
                match_level=MatchLevel.REJECT,
                match_score=0.0,
                match_reasons=["匹配过程出错"],
                missing_skills=[],
                strength_points=[]
            )

    def _check_exclusions(self, candidate: Dict, resume_detail: Optional[Dict] = None) -> bool:
        """检查排除条件"""
        text_to_check = " ".join([
            candidate.get("position", ""),
            candidate.get("company", ""),
            candidate.get("experience", "")
        ])

        # 检查排除关键词
        for keyword in self.match_criteria.exclude_keywords:
            if keyword.lower() in text_to_check.lower():
                logger.debug(f"候选人因排除关键词被排除: {keyword}")
                return True

        # 检查排除公司
        if self.match_criteria.exclude_companies:
            company = candidate.get("company", "")
            if any(exc in company for exc in self.match_criteria.exclude_companies):
                logger.debug(f"候选人因公司被排除: {company}")
                return True

        return False

    def _check_activity(self, candidate: Dict) -> Tuple[float, str, str]:
        """检查活跃时间"""
        active_time = candidate.get("active_time", "")

        if "刚刚活跃" in active_time or "今日活跃" in active_time:
            return 15.0, "最近活跃，沟通响应快", ""
        elif "本周活跃" in active_time:
            return 10.0, "本周活跃", ""
        elif "本月活跃" in active_time:
            return 5.0, "本月活跃", ""
        else:
            return 0.0, "", "活跃时间较早"

    def _check_experience(self, candidate: Dict) -> Tuple[float, str, str]:
        """检查工作经验"""
        experience_text = candidate.get("experience", "")
        years = self._parse_experience_years(experience_text)

        if years >= self.match_criteria.min_experience:
            if self.match_criteria.max_experience and years > self.match_criteria.max_experience:
                return 5.0, f"经验丰富({years}年)", "经验可能过高"
            else:
                return 15.0, f"经验符合要求({years}年)", ""
        else:
            return 0.0, "", f"经验不足(要求{self.match_criteria.min_experience}年)"

    def _parse_experience_years(self, experience_text: str) -> int:
        """解析工作经验年限"""
        # 尝试匹配数字
        patterns = [
            r"(\d+)年",
            r"(\d+)-(\d+)年",
            r"应届生",
            r"在校生"
        ]

        for pattern in patterns:
            match = re.search(pattern, experience_text)
            if match:
                if "年" in experience_text:
                    if "-" in match.group():
                        # 范围，取最小值
                        years = int(match.group(1))
                    else:
                        years = int(match.group(1))
                    return years
                elif "应届" in experience_text or "在校" in experience_text:
                    return 0

        return 0

    def _check_skills(self, candidate: Dict, resume_detail: Optional[Dict] = None) -> Tuple[float, List[str], List[str], List[str]]:
        """检查技能匹配"""
        score = 0.0
        strengths = []
        reasons = []
        missing = []

        # 合并所有文本用于搜索
        all_text = " ".join([
            candidate.get("position", ""),
            candidate.get("company", ""),
            resume_detail.get("description", "") if resume_detail else ""
        ]).lower()

        # 检查必需技能
        required_found = 0
        for skill in self.match_criteria.required_skills:
            if skill.lower() in all_text:
                required_found += 1
            else:
                missing.append(skill)

        if required_found > 0:
            score += (required_found / len(self.match_criteria.required_skills)) * 30
            strengths.append(f"匹配{required_found}个必需技能")
        else:
            reasons.append("缺乏必需技能")

        # 检查优先技能
        preferred_found = 0
        for skill in self.match_criteria.preferred_skills:
            if skill.lower() in all_text:
                preferred_found += 1

        if preferred_found > 0:
            score += (preferred_found / len(self.match_criteria.preferred_skills)) * 10
            strengths.append(f"具备{preferred_found}个加分技能")

        return score, strengths, reasons, missing

    def _check_location(self, candidate: Dict) -> Tuple[float, str, str]:
        """检查地点"""
        # 假设候选人在北京（实际应该从简历中获取）
        candidate_location = "北京"  # 这里应该从实际数据中获取

        if self.match_criteria.location_preference:
            if any(pref in candidate_location for pref in self.match_criteria.location_preference):
                return 10.0, "地点符合要求", ""
            else:
                return 0.0, "", "地点不符合要求"
        else:
            return 5.0, "地点不限", ""

    def _check_company_background(self, candidate: Dict) -> Tuple[float, str, str]:
        """检查公司背景"""
        company = candidate.get("company", "")

        # 检查是否是知名公司
        if self.match_criteria.preferred_companies:
            if any(pref in company for pref in self.match_criteria.preferred_companies):
                return 10.0, f"有{company}背景", ""

        # 检查是否是大厂
        big_companies = ["腾讯", "阿里", "百度", "字节跳动", "美团", "京东", "网易", "小米"]
        if any(big in company for big in big_companies):
            return 8.0, f"有大厂背景({company})", ""

        return 5.0, "", "公司背景一般"

    def _check_salary_expectation(self, candidate: Dict) -> Tuple[float, str, str]:
        """检查薪资期望"""
        salary_text = candidate.get("salary", "")
        salary_range = self._parse_salary_range(salary_text)

        if self.match_criteria.max_salary_expectation:
            if salary_range and salary_range[1] <= self.match_criteria.max_salary_expectation:
                return 5.0, "薪资期望合理", ""
            elif salary_range and salary_range[0] > self.match_criteria.max_salary_expectation:
                return 0.0, "", "薪资期望过高"

        return 3.0, "", "薪资期望未明确"

    def _parse_salary_range(self, salary_text: str) -> Optional[Tuple[int, int]]:
        """解析薪资范围"""
        # 匹配如 "15-25K" 的格式
        match = re.search(r"(\d+)-(\d+)K", salary_text)
        if match:
            return int(match.group(1)), int(match.group(2))

        # 匹配如 "15K" 的格式
        match = re.search(r"(\d+)K", salary_text)
        if match:
            salary = int(match.group(1))
            return salary, salary

        return None

    def _determine_match_level(self, score: float) -> MatchLevel:
        """根据分数确定匹配级别"""
        if score >= 80:
            return MatchLevel.EXCELLENT
        elif score >= 60:
            return MatchLevel.GOOD
        elif score >= 40:
            return MatchLevel.FAIR
        elif score >= 20:
            return MatchLevel.POOR
        else:
            return MatchLevel.REJECT

    def filter_candidates(self, candidates: List[Dict],
                         min_match_level: MatchLevel = MatchLevel.FAIR,
                         max_results: int = 50) -> List[MatchResult]:
        """
        批量筛选候选人

        Args:
            candidates: 候选人列表
            min_match_level: 最低匹配级别
            max_results: 最大返回数量

        Returns:
            List[MatchResult]: 筛选结果
        """
        results = []

        for candidate in candidates:
            result = self.match_candidate(candidate)

            # 过滤不满足最低匹配级别的
            if result.match_level.value >= min_match_level.value:
                results.append(result)

            # 按分数排序
            results.sort(key=lambda x: x.match_score, reverse=True)

            # 限制结果数量
            if len(results) >= max_results:
                break

        return results

    def generate_match_report(self, results: List[MatchResult]) -> Dict:
        """生成匹配报告"""
        report = {
            "total_candidates": len(results),
            "match_distribution": {
                "excellent": 0,
                "good": 0,
                "fair": 0,
                "poor": 0
            },
            "average_score": 0.0,
            "common_missing_skills": {},
            "top_candidates": []
        }

        if not results:
            return report

        # 统计匹配分布
        total_score = 0
        missing_skills_count = {}

        for result in results:
            # 分布统计
            if result.match_level == MatchLevel.EXCELLENT:
                report["match_distribution"]["excellent"] += 1
            elif result.match_level == MatchLevel.GOOD:
                report["match_distribution"]["good"] += 1
            elif result.match_level == MatchLevel.FAIR:
                report["match_distribution"]["fair"] += 1
            else:
                report["match_distribution"]["poor"] += 1

            # 分数统计
            total_score += result.match_score

            # 缺失技能统计
            for skill in result.missing_skills:
                missing_skills_count[skill] = missing_skills_count.get(skill, 0) + 1

        # 平均分
        report["average_score"] = total_score / len(results)

        # 最常见的缺失技能
        report["common_missing_skills"] = dict(
            sorted(missing_skills_count.items(), key=lambda x: x[1], reverse=True)[:10]
        )

        # Top 10 候选人
        report["top_candidates"] = [
            {
                "name": result.candidate.get("name", ""),
                "position": result.candidate.get("position", ""),
                "company": result.candidate.get("company", ""),
                "score": result.match_score,
                "level": result.match_level.name,
                "strengths": result.strength_points[:3]
            }
            for result in results[:10]
        ]

        return report