"""
智能教案生成核心模块
整合知识库检索、学情分析和教学实践方法，生成个性化教案
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
import json

from llama_index.core import Settings
from llama_index.llms.openai import OpenAI

from config import settings
from src.knowledge_base import knowledge_base
from src.student_data import student_data_manager
from src.teaching_practices import get_teaching_practices, TeachingPracticeQuery, SubjectType, GradeLevel

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class LessonPlanRequest:
    """教案生成请求"""
    class_id: str
    subject: str
    grade: str
    topic: str
    duration: int = 45  # 课时长度（分钟）
    learning_objectives: List[str] = None
    special_requirements: str = ""
    
    def __post_init__(self):
        if self.learning_objectives is None:
            self.learning_objectives = []

@dataclass
class LessonPlanResponse:
    """教案生成响应"""
    lesson_plan: Dict[str, Any]
    reference_materials: List[Dict[str, Any]]
    student_analysis: Dict[str, Any]
    teaching_practices: Dict[str, Any]
    generated_at: datetime
    confidence_score: float

class IntelligentLessonGenerator:
    """智能教案生成器"""
    
    def __init__(self):
        """初始化教案生成器"""
        self.llm = OpenAI(
            model=settings.llm_model,
            api_key=settings.openai_api_key,
            api_base=settings.openai_api_base,
            temperature=0.7  # 适中的创造性
        )
        
        # 教案模板
        self.lesson_plan_template = {
            "基本信息": {
                "课程名称": "",
                "学科": "",
                "年级": "",
                "课时": "",
                "授课教师": "",
                "授课时间": ""
            },
            "教学目标": {
                "知识目标": [],
                "能力目标": [],
                "情感态度目标": []
            },
            "教学重点": [],
            "教学难点": [],
            "教学方法": [],
            "教学准备": {
                "教师准备": [],
                "学生准备": []
            },
            "教学过程": {
                "导入环节": {
                    "时间": "5分钟",
                    "内容": "",
                    "设计意图": ""
                },
                "新课讲授": {
                    "时间": "25分钟",
                    "内容": "",
                    "设计意图": ""
                },
                "练习巩固": {
                    "时间": "10分钟",
                    "内容": "",
                    "设计意图": ""
                },
                "课堂小结": {
                    "时间": "3分钟",
                    "内容": "",
                    "设计意图": ""
                },
                "作业布置": {
                    "时间": "2分钟",
                    "内容": "",
                    "设计意图": ""
                }
            },
            "板书设计": "",
            "教学反思": "",
            "差异化教学": {
                "优秀学生": "",
                "中等学生": "",
                "学困学生": ""
            }
        }
    
    async def generate_lesson_plan(self, request: LessonPlanRequest) -> LessonPlanResponse:
        """
        生成智能教案
        
        Args:
            request: 教案生成请求
            
        Returns:
            生成的教案响应
        """
        try:
            logger.info(f"开始生成教案: {request.subject} - {request.topic}")
            
            # 1. 并行获取所有必要数据
            tasks = [
                self._get_reference_materials(request),
                self._get_student_analysis(request),
                self._get_teaching_practices(request)
            ]
            
            reference_materials, student_analysis, teaching_practices = await asyncio.gather(*tasks)
            
            # 2. 生成教案内容
            lesson_plan = await self._generate_lesson_content(
                request, reference_materials, student_analysis, teaching_practices
            )
            
            # 3. 计算置信度分数
            confidence_score = self._calculate_confidence_score(
                reference_materials, student_analysis, teaching_practices
            )
            
            response = LessonPlanResponse(
                lesson_plan=lesson_plan,
                reference_materials=reference_materials,
                student_analysis=student_analysis,
                teaching_practices=teaching_practices,
                generated_at=datetime.now(),
                confidence_score=confidence_score
            )
            
            logger.info(f"教案生成完成，置信度: {confidence_score:.2f}")
            return response
            
        except Exception as e:
            logger.error(f"生成教案失败: {e}")
            raise
    
    async def _get_reference_materials(self, request: LessonPlanRequest) -> List[Dict[str, Any]]:
        """获取参考教案材料"""
        try:
            # 构建查询文本
            query_text = f"{request.subject} {request.topic} {request.grade} 教案"
            
            # 从知识库检索相似教案
            similar_lessons = knowledge_base.search_similar_lessons(
                query=query_text,
                top_k=settings.max_lesson_plans
            )
            
            logger.info(f"检索到 {len(similar_lessons)} 个参考教案")
            return similar_lessons
            
        except Exception as e:
            logger.error(f"获取参考材料失败: {e}")
            return []
    
    async def _get_student_analysis(self, request: LessonPlanRequest) -> Dict[str, Any]:
        """获取学生学情分析"""
        try:
            # 获取班级表现数据
            class_performance = await student_data_manager.get_class_performance(
                class_id=request.class_id,
                subject=request.subject
            )
            
            # 获取知识薄弱点
            knowledge_gaps = await student_data_manager.get_knowledge_gaps(
                class_id=request.class_id,
                subject=request.subject
            )
            
            # 分析教学需求
            class_needs = student_data_manager.analyze_class_needs(
                class_performance, knowledge_gaps
            )
            
            return {
                "class_performance": class_performance,
                "knowledge_gaps": knowledge_gaps,
                "class_needs": class_needs
            }
            
        except Exception as e:
            logger.error(f"获取学生分析失败: {e}")
            return {}
    
    async def _get_teaching_practices(self, request: LessonPlanRequest) -> Dict[str, Any]:
        """获取教学实践方法"""
        try:
            # 构建查询
            query = TeachingPracticeQuery(
                subject=self._map_subject_to_enum(request.subject),
                grade=self._map_grade_to_enum(request.grade),
                topic=request.topic
            )
            
            # 获取教学实践方法
            practices = await get_teaching_practices(query)
            
            return {
                "teaching_strategies": practices.teaching_strategies,
                "classroom_activities": practices.classroom_activities,
                "assessment_methods": practices.assessment_methods,
                "classroom_management": practices.classroom_management
            }
            
        except Exception as e:
            logger.error(f"获取教学实践失败: {e}")
            return {}
    
    def _map_subject_to_enum(self, subject: str) -> SubjectType:
        """将学科字符串映射到枚举"""
        subject_map = {
            "语文": SubjectType.CHINESE,
            "数学": SubjectType.MATH,
            "英语": SubjectType.ENGLISH,
            "物理": SubjectType.PHYSICS,
            "化学": SubjectType.CHEMISTRY,
            "生物": SubjectType.BIOLOGY,
            "历史": SubjectType.HISTORY,
            "地理": SubjectType.GEOGRAPHY,
            "政治": SubjectType.POLITICS
        }
        return subject_map.get(subject, SubjectType.GENERAL)
    
    def _map_grade_to_enum(self, grade: str) -> GradeLevel:
        """将年级字符串映射到枚举"""
        grade_map = {
            "一年级": GradeLevel.GRADE_1,
            "二年级": GradeLevel.GRADE_2,
            "三年级": GradeLevel.GRADE_3,
            "四年级": GradeLevel.GRADE_4,
            "五年级": GradeLevel.GRADE_5,
            "六年级": GradeLevel.GRADE_6,
            "七年级": GradeLevel.GRADE_7,
            "八年级": GradeLevel.GRADE_8,
            "九年级": GradeLevel.GRADE_9,
            "高一": GradeLevel.HIGH_SCHOOL_1,
            "高二": GradeLevel.HIGH_SCHOOL_2,
            "高三": GradeLevel.HIGH_SCHOOL_3
        }
        return grade_map.get(grade, GradeLevel.GRADE_5)
    
    async def _generate_lesson_content(self, request: LessonPlanRequest,
                                     reference_materials: List[Dict[str, Any]],
                                     student_analysis: Dict[str, Any],
                                     teaching_practices: Dict[str, Any]) -> Dict[str, Any]:
        """生成教案内容"""
        try:
            # 构建提示词
            prompt = self._build_generation_prompt(
                request, reference_materials, student_analysis, teaching_practices
            )
            
            # 调用LLM生成教案
            response = await self.llm.acomplete(prompt)
            
            # 解析生成的教案
            lesson_plan = self._parse_lesson_plan(response.text, request)
            
            return lesson_plan
            
        except Exception as e:
            logger.error(f"生成教案内容失败: {e}")
            # 返回基础模板
            return self._create_basic_lesson_plan(request)
    
    def _build_generation_prompt(self, request: LessonPlanRequest,
                               reference_materials: List[Dict[str, Any]],
                               student_analysis: Dict[str, Any],
                               teaching_practices: Dict[str, Any]) -> str:
        """构建教案生成提示词"""
        
        # 提取参考材料要点
        reference_summary = ""
        if reference_materials:
            reference_summary = "参考优秀教案要点:\n"
            for i, material in enumerate(reference_materials[:3], 1):
                reference_summary += f"{i}. {material.get('content', '')[:200]}...\n"
        
        # 提取学情分析要点
        student_summary = ""
        if student_analysis.get('class_needs'):
            needs = student_analysis['class_needs']
            student_summary = f"班级学情分析:\n"
            student_summary += f"- 平均成绩: {student_analysis.get('class_performance', {}).get('average_score', '未知')}\n"
            student_summary += f"- 重点关注: {', '.join([t['topic'] for t in needs.get('priority_topics', [])])}\n"
            student_summary += f"- 教学策略: {', '.join(needs.get('teaching_strategies', []))}\n"
        
        # 提取教学实践方法
        practices_summary = ""
        if teaching_practices.get('teaching_strategies'):
            practices_summary = "推荐教学方法:\n"
            for strategy in teaching_practices['teaching_strategies'][:2]:
                practices_summary += f"- {strategy.get('name', '')}: {strategy.get('description', '')}\n"
        
        prompt = f"""
作为一名资深教育专家，请根据以下信息生成一份详细的教案：

基本信息：
- 学科: {request.subject}
- 年级: {request.grade}
- 课题: {request.topic}
- 课时: {request.duration}分钟
- 学习目标: {', '.join(request.learning_objectives)}
- 特殊要求: {request.special_requirements}

{reference_summary}

{student_summary}

{practices_summary}

请按照以下结构生成教案，确保内容具体、可操作性强：

1. 教学目标（知识目标、能力目标、情感态度目标）
2. 教学重点和难点
3. 教学方法和策略
4. 教学准备（教师和学生）
5. 教学过程（导入、新课讲授、练习巩固、小结、作业）
6. 板书设计
7. 差异化教学安排
8. 教学反思要点

请确保教案符合学生认知水平，教学方法多样化，注重学生参与和互动。

教案内容：
"""
        
        return prompt
    
    def _parse_lesson_plan(self, generated_text: str, request: LessonPlanRequest) -> Dict[str, Any]:
        """解析生成的教案文本"""
        lesson_plan = self.lesson_plan_template.copy()
        
        # 填充基本信息
        lesson_plan["基本信息"]["课程名称"] = request.topic
        lesson_plan["基本信息"]["学科"] = request.subject
        lesson_plan["基本信息"]["年级"] = request.grade
        lesson_plan["基本信息"]["课时"] = f"{request.duration}分钟"
        lesson_plan["基本信息"]["授课时间"] = datetime.now().strftime("%Y-%m-%d")
        
        # 简单的文本解析（实际应用中可以使用更复杂的NLP方法）
        sections = generated_text.split('\n\n')
        current_section = ""
        
        for section in sections:
            section = section.strip()
            if not section:
                continue
                
            # 识别不同部分并填充到模板中
            if "教学目标" in section:
                lesson_plan["生成内容"] = generated_text
            elif "教学重点" in section:
                pass  # 可以进一步解析
            # ... 其他部分的解析
        
        # 如果解析失败，直接存储生成的文本
        if "生成内容" not in lesson_plan:
            lesson_plan["生成内容"] = generated_text
        
        return lesson_plan
    
    def _create_basic_lesson_plan(self, request: LessonPlanRequest) -> Dict[str, Any]:
        """创建基础教案模板"""
        lesson_plan = self.lesson_plan_template.copy()
        
        # 填充基本信息
        lesson_plan["基本信息"]["课程名称"] = request.topic
        lesson_plan["基本信息"]["学科"] = request.subject
        lesson_plan["基本信息"]["年级"] = request.grade
        lesson_plan["基本信息"]["课时"] = f"{request.duration}分钟"
        lesson_plan["基本信息"]["授课时间"] = datetime.now().strftime("%Y-%m-%d")
        
        # 设置默认目标
        lesson_plan["教学目标"]["知识目标"] = request.learning_objectives or [f"掌握{request.topic}的基本概念"]
        lesson_plan["教学目标"]["能力目标"] = ["培养学生的分析能力和解决问题能力"]
        lesson_plan["教学目标"]["情感态度目标"] = ["激发学生的学习兴趣，培养良好的学习习惯"]
        
        return lesson_plan
    
    def _calculate_confidence_score(self, reference_materials: List[Dict[str, Any]],
                                  student_analysis: Dict[str, Any],
                                  teaching_practices: Dict[str, Any]) -> float:
        """计算教案生成的置信度分数"""
        score = 0.0
        
        # 参考材料质量评分 (40%)
        if reference_materials:
            avg_score = sum(material.get('score', 0) for material in reference_materials) / len(reference_materials)
            material_score = min(avg_score, 1.0) * 0.4
            score += material_score
        
        # 学情分析完整性评分 (30%)
        if student_analysis:
            analysis_completeness = 0
            if student_analysis.get('class_performance'):
                analysis_completeness += 0.1
            if student_analysis.get('knowledge_gaps'):
                analysis_completeness += 0.1
            if student_analysis.get('class_needs'):
                analysis_completeness += 0.1
            score += analysis_completeness
        
        # 教学实践方法丰富度评分 (30%)
        if teaching_practices:
            practices_richness = 0
            for practice_type in ['teaching_strategies', 'classroom_activities', 'assessment_methods']:
                if teaching_practices.get(practice_type):
                    practices_richness += 0.1
            score += practices_richness
        
        return min(score, 1.0)
    
    async def batch_generate_lesson_plans(self, requests: List[LessonPlanRequest]) -> List[LessonPlanResponse]:
        """批量生成教案"""
        tasks = [self.generate_lesson_plan(request) for request in requests]
        return await asyncio.gather(*tasks, return_exceptions=True)

# 创建全局教案生成器实例
lesson_generator = IntelligentLessonGenerator()

# 便利函数
async def generate_lesson_plan(class_id: str, subject: str, grade: str, topic: str,
                             duration: int = 45, learning_objectives: List[str] = None,
                             special_requirements: str = "") -> LessonPlanResponse:
    """
    便利函数：生成教案
    
    Args:
        class_id: 班级ID
        subject: 学科
        grade: 年级
        topic: 课题
        duration: 课时长度
        learning_objectives: 学习目标
        special_requirements: 特殊要求
        
    Returns:
        教案生成响应
    """
    request = LessonPlanRequest(
        class_id=class_id,
        subject=subject,
        grade=grade,
        topic=topic,
        duration=duration,
        learning_objectives=learning_objectives or [],
        special_requirements=special_requirements
    )
    
    return await lesson_generator.generate_lesson_plan(request)