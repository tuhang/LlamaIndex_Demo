"""
教学实践方法获取模块
通过Context7 MCP服务获取最新的教育教学实践、教学方法、课堂管理技巧等信息
"""
import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import httpx
from pydantic import BaseModel, Field, validator

try:
    from config import settings
except ImportError:
    # 如果无法导入config，使用默认设置
    import os
    class Settings:
        context7_api_key = os.getenv("CONTEXT7_API_KEY")
    settings = Settings()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SubjectType(str, Enum):
    """学科类型枚举"""
    CHINESE = "语文"
    MATH = "数学"
    ENGLISH = "英语"
    PHYSICS = "物理"
    CHEMISTRY = "化学"
    BIOLOGY = "生物"
    HISTORY = "历史"
    GEOGRAPHY = "地理"
    POLITICS = "政治"
    MUSIC = "音乐"
    ART = "美术"
    PE = "体育"
    TECHNOLOGY = "信息技术"
    GENERAL = "通用"


class GradeLevel(str, Enum):
    """年级水平枚举"""
    GRADE_1 = "一年级"
    GRADE_2 = "二年级"
    GRADE_3 = "三年级"
    GRADE_4 = "四年级"
    GRADE_5 = "五年级"
    GRADE_6 = "六年级"
    GRADE_7 = "七年级"
    GRADE_8 = "八年级"
    GRADE_9 = "九年级"
    GRADE_10 = "高一"
    GRADE_11 = "高二"
    GRADE_12 = "高三"
    KINDERGARTEN = "幼儿园"
    UNIVERSITY = "大学"


class TeachingObjective(str, Enum):
    """教学目标枚举"""
    KNOWLEDGE_TRANSFER = "知识传授"
    SKILL_DEVELOPMENT = "技能培养"
    CRITICAL_THINKING = "批判性思维"
    CREATIVITY = "创造力培养"
    COLLABORATION = "合作能力"
    COMMUNICATION = "沟通能力"
    PROBLEM_SOLVING = "问题解决"
    CHARACTER_BUILDING = "品格塑造"


class TeachingMethodType(str, Enum):
    """教学方法类型枚举"""
    INTERACTIVE = "互动式教学"
    INQUIRY_BASED = "探究式学习"
    PROJECT_BASED = "项目式学习"
    COLLABORATIVE = "合作学习"
    DIFFERENTIATED = "差异化教学"
    FLIPPED = "翻转课堂"
    GAMIFICATION = "游戏化教学"
    TECHNOLOGY_ENHANCED = "技术增强教学"
    EXPERIENTIAL = "体验式学习"
    SCAFFOLDING = "支架式教学"


@dataclass
class TeachingPracticeQuery:
    """教学实践查询参数"""
    subject: Optional[SubjectType] = None
    grade: Optional[GradeLevel] = None
    objective: Optional[TeachingObjective] = None
    method_type: Optional[TeachingMethodType] = None
    keywords: Optional[List[str]] = None
    language: str = "zh-CN"
    limit: int = 10


class TeachingStrategy(BaseModel):
    """教学策略模型"""
    name: str = Field(..., description="策略名称")
    description: str = Field(..., description="策略描述")
    subject_areas: List[str] = Field(default_factory=list, description="适用学科")
    grade_levels: List[str] = Field(default_factory=list, description="适用年级")
    objectives: List[str] = Field(default_factory=list, description="教学目标")
    implementation_steps: List[str] = Field(default_factory=list, description="实施步骤")
    benefits: List[str] = Field(default_factory=list, description="策略优势")
    considerations: List[str] = Field(default_factory=list, description="注意事项")
    resources_needed: List[str] = Field(default_factory=list, description="所需资源")
    assessment_methods: List[str] = Field(default_factory=list, description="评估方法")


class ClassroomActivity(BaseModel):
    """课堂活动模型"""
    name: str = Field(..., description="活动名称")
    description: str = Field(..., description="活动描述")
    duration: str = Field(..., description="活动时长")
    materials: List[str] = Field(default_factory=list, description="所需材料")
    instructions: List[str] = Field(default_factory=list, description="活动指导")
    learning_outcomes: List[str] = Field(default_factory=list, description="学习成果")
    differentiation_tips: List[str] = Field(default_factory=list, description="差异化建议")
    extension_activities: List[str] = Field(default_factory=list, description="拓展活动")


class AssessmentMethod(BaseModel):
    """评估方法模型"""
    name: str = Field(..., description="评估方法名称")
    type: str = Field(..., description="评估类型")
    description: str = Field(..., description="方法描述")
    when_to_use: str = Field(..., description="使用时机")
    implementation: List[str] = Field(default_factory=list, description="实施方法")
    rubric_criteria: List[str] = Field(default_factory=list, description="评估标准")
    data_collection: List[str] = Field(default_factory=list, description="数据收集")
    feedback_strategies: List[str] = Field(default_factory=list, description="反馈策略")


class ClassroomManagement(BaseModel):
    """课堂管理技巧模型"""
    category: str = Field(..., description="管理类别")
    techniques: List[str] = Field(default_factory=list, description="管理技巧")
    preventive_strategies: List[str] = Field(default_factory=list, description="预防策略")
    intervention_methods: List[str] = Field(default_factory=list, description="干预方法")
    positive_reinforcement: List[str] = Field(default_factory=list, description="正向激励")
    environment_setup: List[str] = Field(default_factory=list, description="环境设置")


class TeachingPracticeResponse(BaseModel):
    """教学实践响应模型"""
    query_info: Dict[str, Any] = Field(..., description="查询信息")
    teaching_strategies: List[TeachingStrategy] = Field(default_factory=list, description="教学策略")
    classroom_activities: List[ClassroomActivity] = Field(default_factory=list, description="课堂活动")
    assessment_methods: List[AssessmentMethod] = Field(default_factory=list, description="评估方法")
    classroom_management: List[ClassroomManagement] = Field(default_factory=list, description="课堂管理")
    additional_resources: List[str] = Field(default_factory=list, description="附加资源")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class Context7Client:
    """Context7 MCP客户端"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化Context7客户端
        
        Args:
            api_key: Context7 API密钥
        """
        self.api_key = api_key or settings.context7_api_key
        self.base_url = "https://api.context7.dev/v1"
        self.timeout = 30.0
        
        if not self.api_key:
            logger.warning("Context7 API密钥未配置，某些功能可能无法使用")
    
    async def resolve_library_id(self, query: str) -> Optional[str]:
        """
        解析教育库ID
        
        Args:
            query: 查询字符串
            
        Returns:
            库ID或None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/resolve-library-id",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "query": query,
                        "domain": "education",
                        "language": "zh-CN"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("library_id")
                else:
                    logger.error(f"解析库ID失败: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"解析库ID异常: {e}")
            return None
    
    async def get_library_docs(self, library_id: str, topic: str) -> Optional[Dict[str, Any]]:
        """
        获取库文档
        
        Args:
            library_id: 库ID
            topic: 主题
            
        Returns:
            文档数据或None
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/get-library-docs",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "library_id": library_id,
                        "topic": topic,
                        "format": "structured",
                        "language": "zh-CN"
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"获取库文档失败: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            logger.error(f"获取库文档异常: {e}")
            return None


class TeachingPracticesService:
    """教学实践方法服务"""
    
    def __init__(self):
        """初始化服务"""
        self.context7_client = Context7Client()
        self.cache: Dict[str, Any] = {}
        self.cache_ttl = 3600  # 缓存1小时
        
    def _generate_cache_key(self, query: TeachingPracticeQuery) -> str:
        """生成缓存键"""
        query_dict = asdict(query)
        # 排序确保一致性
        sorted_items = sorted(query_dict.items())
        return f"teaching_practices:{hash(str(sorted_items))}"
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """检查缓存是否有效"""
        if "timestamp" not in cache_entry:
            return False
        
        cache_time = datetime.fromisoformat(cache_entry["timestamp"])
        now = datetime.now()
        return (now - cache_time).total_seconds() < self.cache_ttl
    
    async def _fetch_teaching_strategies(self, query: TeachingPracticeQuery) -> List[TeachingStrategy]:
        """获取教学策略"""
        strategies = []
        
        try:
            # 构建查询主题
            topics = []
            if query.subject:
                topics.append(f"{query.subject.value}教学策略")
            if query.method_type:
                topics.append(f"{query.method_type.value}")
            if query.objective:
                topics.append(f"{query.objective.value}教学方法")
            
            if not topics:
                topics = ["现代教学策略", "有效教学方法"]
            
            # 解析教育库ID
            library_id = await self.context7_client.resolve_library_id("现代教育教学方法")
            
            if library_id:
                for topic in topics[:3]:  # 限制查询数量
                    docs = await self.context7_client.get_library_docs(library_id, topic)
                    if docs and "content" in docs:
                        # 解析文档内容为教学策略
                        parsed_strategies = self._parse_teaching_strategies(docs["content"])
                        strategies.extend(parsed_strategies)
            
            # 如果Context7没有返回结果，提供默认策略
            if not strategies:
                strategies = self._get_default_teaching_strategies(query)
            
        except Exception as e:
            logger.error(f"获取教学策略失败: {e}")
            strategies = self._get_default_teaching_strategies(query)
        
        return strategies[:query.limit]
    
    async def _fetch_classroom_activities(self, query: TeachingPracticeQuery) -> List[ClassroomActivity]:
        """获取课堂活动"""
        activities = []
        
        try:
            # 构建活动查询主题
            topics = []
            if query.subject:
                topics.append(f"{query.subject.value}课堂活动")
            if query.grade:
                topics.append(f"{query.grade.value}互动活动")
            
            if not topics:
                topics = ["互动课堂活动", "学生参与活动"]
            
            library_id = await self.context7_client.resolve_library_id("课堂活动设计")
            
            if library_id:
                for topic in topics[:2]:
                    docs = await self.context7_client.get_library_docs(library_id, topic)
                    if docs and "content" in docs:
                        parsed_activities = self._parse_classroom_activities(docs["content"])
                        activities.extend(parsed_activities)
            
            if not activities:
                activities = self._get_default_classroom_activities(query)
                
        except Exception as e:
            logger.error(f"获取课堂活动失败: {e}")
            activities = self._get_default_classroom_activities(query)
        
        return activities[:query.limit]
    
    async def _fetch_assessment_methods(self, query: TeachingPracticeQuery) -> List[AssessmentMethod]:
        """获取评估方法"""
        methods = []
        
        try:
            topics = ["形成性评估", "学习评价方法", "教学评估技巧"]
            library_id = await self.context7_client.resolve_library_id("教育评估方法")
            
            if library_id:
                for topic in topics:
                    docs = await self.context7_client.get_library_docs(library_id, topic)
                    if docs and "content" in docs:
                        parsed_methods = self._parse_assessment_methods(docs["content"])
                        methods.extend(parsed_methods)
            
            if not methods:
                methods = self._get_default_assessment_methods(query)
                
        except Exception as e:
            logger.error(f"获取评估方法失败: {e}")
            methods = self._get_default_assessment_methods(query)
        
        return methods[:query.limit]
    
    async def _fetch_classroom_management(self, query: TeachingPracticeQuery) -> List[ClassroomManagement]:
        """获取课堂管理技巧"""
        management_tips = []
        
        try:
            topics = ["课堂管理技巧", "学生行为管理", "课堂纪律管理"]
            library_id = await self.context7_client.resolve_library_id("课堂管理")
            
            if library_id:
                for topic in topics:
                    docs = await self.context7_client.get_library_docs(library_id, topic)
                    if docs and "content" in docs:
                        parsed_management = self._parse_classroom_management(docs["content"])
                        management_tips.extend(parsed_management)
            
            if not management_tips:
                management_tips = self._get_default_classroom_management(query)
                
        except Exception as e:
            logger.error(f"获取课堂管理技巧失败: {e}")
            management_tips = self._get_default_classroom_management(query)
        
        return management_tips[:5]  # 限制管理技巧数量
    
    def _parse_teaching_strategies(self, content: str) -> List[TeachingStrategy]:
        """解析教学策略内容"""
        # 这里应该实现更复杂的解析逻辑
        # 暂时返回示例数据
        strategies = []
        
        # 简单的关键词匹配和结构化解析
        if "互动" in content or "参与" in content:
            strategies.append(TeachingStrategy(
                name="互动式教学",
                description="通过师生互动、生生互动促进学习",
                subject_areas=["通用"],
                grade_levels=["全年级"],
                objectives=["提高参与度", "促进理解"],
                implementation_steps=[
                    "设计互动环节",
                    "鼓励学生参与",
                    "及时反馈",
                    "总结讨论结果"
                ],
                benefits=["提高学习兴趣", "加深理解", "培养表达能力"],
                considerations=["控制讨论时间", "确保全员参与"],
                resources_needed=["多媒体设备", "讨论空间"],
                assessment_methods=["观察记录", "参与度评估"]
            ))
        
        return strategies
    
    def _parse_classroom_activities(self, content: str) -> List[ClassroomActivity]:
        """解析课堂活动内容"""
        activities = []
        
        # 示例解析逻辑
        if "小组" in content or "合作" in content:
            activities.append(ClassroomActivity(
                name="小组合作学习",
                description="学生分组完成学习任务，培养合作能力",
                duration="20-30分钟",
                materials=["任务卡片", "记录表", "展示材料"],
                instructions=[
                    "将学生分成4-6人小组",
                    "分配明确的角色和任务",
                    "设定时间限制",
                    "组织成果展示"
                ],
                learning_outcomes=["团队合作能力", "沟通技能", "问题解决能力"],
                differentiation_tips=[
                    "根据能力分配不同难度任务",
                    "提供不同类型的支持材料"
                ],
                extension_activities=["跨组交流", "反思总结"]
            ))
        
        return activities
    
    def _parse_assessment_methods(self, content: str) -> List[AssessmentMethod]:
        """解析评估方法内容"""
        methods = []
        
        # 示例解析逻辑
        methods.append(AssessmentMethod(
            name="形成性评估",
            type="过程性评估",
            description="在教学过程中持续评估学生学习进展",
            when_to_use="整个教学过程中",
            implementation=[
                "课堂观察",
                "即时反馈",
                "小测验",
                "学习日志"
            ],
            rubric_criteria=["参与度", "理解程度", "进步情况"],
            data_collection=["观察记录", "作业分析", "学生自评"],
            feedback_strategies=["及时口头反馈", "书面评语", "同伴互评"]
        ))
        
        return methods
    
    def _parse_classroom_management(self, content: str) -> List[ClassroomManagement]:
        """解析课堂管理内容"""
        management_tips = []
        
        management_tips.append(ClassroomManagement(
            category="课堂纪律管理",
            techniques=[
                "建立明确的课堂规则",
                "使用积极的语言",
                "及时表扬良好行为"
            ],
            preventive_strategies=[
                "创造积极的学习环境",
                "建立例行程序",
                "预设活动转换"
            ],
            intervention_methods=[
                "重定向注意力",
                "私下提醒",
                "暂停活动"
            ],
            positive_reinforcement=[
                "口头表扬",
                "积分系统",
                "特权奖励"
            ],
            environment_setup=[
                "合理安排座位",
                "准备充足材料",
                "营造温馨氛围"
            ]
        ))
        
        return management_tips
    
    def _get_default_teaching_strategies(self, query: TeachingPracticeQuery) -> List[TeachingStrategy]:
        """获取默认教学策略"""
        strategies = [
            TeachingStrategy(
                name="探究式学习",
                description="引导学生主动探索和发现知识",
                subject_areas=["科学", "数学", "社会"],
                grade_levels=["中高年级"],
                objectives=["培养探究能力", "提高批判思维"],
                implementation_steps=[
                    "提出问题或挑战",
                    "引导学生制定探究计划",
                    "支持学生收集和分析数据",
                    "促进结论分享和讨论"
                ],
                benefits=["提高学习主动性", "培养科学思维", "增强解决问题能力"],
                considerations=["需要充足时间", "要求教师引导技巧"],
                resources_needed=["探究材料", "参考资源", "记录工具"],
                assessment_methods=["过程观察", "成果展示", "反思报告"]
            ),
            TeachingStrategy(
                name="差异化教学",
                description="根据学生不同需求提供个性化教学",
                subject_areas=["全学科"],
                grade_levels=["全年级"],
                objectives=["满足个体需求", "促进全面发展"],
                implementation_steps=[
                    "评估学生起点水平",
                    "设计分层任务",
                    "提供多样化资源",
                    "实施个性化指导"
                ],
                benefits=["提高学习效果", "增强学习信心", "促进包容性"],
                considerations=["需要详细规划", "资源需求较大"],
                resources_needed=["多层次材料", "辅助工具", "评估量表"],
                assessment_methods=["个性化评估", "成长档案", "自我评价"]
            )
        ]
        
        return strategies
    
    def _get_default_classroom_activities(self, query: TeachingPracticeQuery) -> List[ClassroomActivity]:
        """获取默认课堂活动"""
        activities = [
            ClassroomActivity(
                name="思维导图制作",
                description="学生创建思维导图来组织和展示知识",
                duration="15-25分钟",
                materials=["纸张", "彩笔", "思维导图模板"],
                instructions=[
                    "选择中心主题",
                    "添加主要分支",
                    "补充详细信息",
                    "美化和完善"
                ],
                learning_outcomes=["知识整理能力", "创造性思维", "视觉表达能力"],
                differentiation_tips=[
                    "提供不同复杂度的模板",
                    "允许使用数字工具"
                ],
                extension_activities=["分享展示", "互相评价", "数字化制作"]
            ),
            ClassroomActivity(
                name="角色扮演",
                description="学生扮演不同角色来理解概念或情境",
                duration="20-40分钟",
                materials=["角色卡片", "道具", "剧本大纲"],
                instructions=[
                    "分配角色",
                    "准备表演",
                    "进行表演",
                    "讨论反思"
                ],
                learning_outcomes=["理解能力", "表达能力", "同理心"],
                differentiation_tips=[
                    "根据性格分配角色",
                    "提供表演支持"
                ],
                extension_activities=["录制视频", "改编剧本", "跨班交流"]
            )
        ]
        
        return activities
    
    def _get_default_assessment_methods(self, query: TeachingPracticeQuery) -> List[AssessmentMethod]:
        """获取默认评估方法"""
        methods = [
            AssessmentMethod(
                name="学习档案评估",
                type="综合性评估",
                description="收集学生学习成果建立成长档案",
                when_to_use="整个学期或学年",
                implementation=[
                    "设定收集标准",
                    "定期收集作品",
                    "学生自我反思",
                    "教师点评指导"
                ],
                rubric_criteria=["完整性", "质量提升", "反思深度"],
                data_collection=["作业作品", "测试结果", "活动记录"],
                feedback_strategies=["定期回顾", "目标设定", "成长庆祝"]
            ),
            AssessmentMethod(
                name="同伴互评",
                type="互动性评估",
                description="学生相互评价学习成果和表现",
                when_to_use="项目完成后或展示活动中",
                implementation=[
                    "制定评价标准",
                    "培训评价技巧",
                    "组织互评活动",
                    "总结反馈结果"
                ],
                rubric_criteria=["客观性", "建设性", "具体性"],
                data_collection=["评价表格", "口头反馈", "改进建议"],
                feedback_strategies=["匿名反馈", "面对面交流", "改进计划"]
            )
        ]
        
        return methods
    
    def _get_default_classroom_management(self, query: TeachingPracticeQuery) -> List[ClassroomManagement]:
        """获取默认课堂管理技巧"""
        management_tips = [
            ClassroomManagement(
                category="学习环境管理",
                techniques=[
                    "创建舒适的物理环境",
                    "建立学习角落",
                    "展示学生作品"
                ],
                preventive_strategies=[
                    "合理规划空间布局",
                    "确保材料易于获取",
                    "营造温馨氛围"
                ],
                intervention_methods=[
                    "调整座位安排",
                    "改变活动区域",
                    "优化光线和温度"
                ],
                positive_reinforcement=[
                    "环境美化奖励",
                    "清洁维护表扬",
                    "空间使用认可"
                ],
                environment_setup=[
                    "功能区域划分",
                    "材料分类存放",
                    "学习成果展示区"
                ]
            ),
            ClassroomManagement(
                category="时间管理",
                techniques=[
                    "制定时间表",
                    "使用计时器",
                    "建立转换信号"
                ],
                preventive_strategies=[
                    "预告时间安排",
                    "准备过渡活动",
                    "留有缓冲时间"
                ],
                intervention_methods=[
                    "重新分配时间",
                    "简化活动步骤",
                    "提供时间提醒"
                ],
                positive_reinforcement=[
                    "守时表扬",
                    "效率认可",
                    "时间管理奖励"
                ],
                environment_setup=[
                    "时钟显示",
                    "进度条展示",
                    "时间管理工具"
                ]
            )
        ]
        
        return management_tips
    
    async def get_teaching_practices(self, query: TeachingPracticeQuery) -> TeachingPracticeResponse:
        """
        获取教学实践方法
        
        Args:
            query: 查询参数
            
        Returns:
            教学实践响应
        """
        # 检查缓存
        cache_key = self._generate_cache_key(query)
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            logger.info("从缓存返回教学实践数据")
            cached_data = self.cache[cache_key]["data"]
            return TeachingPracticeResponse(**cached_data)
        
        try:
            logger.info(f"获取教学实践方法: {query}")
            
            # 并发获取各类数据
            tasks = [
                self._fetch_teaching_strategies(query),
                self._fetch_classroom_activities(query),
                self._fetch_assessment_methods(query),
                self._fetch_classroom_management(query)
            ]
            
            strategies, activities, methods, management = await asyncio.gather(*tasks)
            
            # 构建响应
            response = TeachingPracticeResponse(
                query_info=asdict(query),
                teaching_strategies=strategies,
                classroom_activities=activities,
                assessment_methods=methods,
                classroom_management=management,
                additional_resources=[
                    "现代教育技术应用指南",
                    "学生参与度提升策略",
                    "差异化教学实践手册",
                    "形成性评估工具包"
                ]
            )
            
            # 缓存结果
            self.cache[cache_key] = {
                "data": response.dict(),
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"成功获取教学实践方法: {len(strategies)}个策略, {len(activities)}个活动")
            return response
            
        except Exception as e:
            logger.error(f"获取教学实践方法失败: {e}")
            # 返回默认响应
            return TeachingPracticeResponse(
                query_info=asdict(query),
                teaching_strategies=self._get_default_teaching_strategies(query),
                classroom_activities=self._get_default_classroom_activities(query),
                assessment_methods=self._get_default_assessment_methods(query),
                classroom_management=self._get_default_classroom_management(query)
            )
    
    def clear_cache(self):
        """清除缓存"""
        self.cache.clear()
        logger.info("教学实践方法缓存已清除")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        total_entries = len(self.cache)
        valid_entries = sum(1 for entry in self.cache.values() if self._is_cache_valid(entry))
        
        return {
            "total_entries": total_entries,
            "valid_entries": valid_entries,
            "expired_entries": total_entries - valid_entries,
            "cache_ttl": self.cache_ttl
        }


# 创建全局服务实例
teaching_practices_service = TeachingPracticesService()


# 便利函数
async def get_teaching_strategies(
    subject: Optional[str] = None,
    grade: Optional[str] = None, 
    objective: Optional[str] = None,
    method_type: Optional[str] = None,
    keywords: Optional[List[str]] = None,
    limit: int = 10
) -> List[TeachingStrategy]:
    """
    获取教学策略的便利函数
    
    Args:
        subject: 学科
        grade: 年级  
        objective: 教学目标
        method_type: 教学方法类型
        keywords: 关键词列表
        limit: 返回数量限制
        
    Returns:
        教学策略列表
    """
    query = TeachingPracticeQuery(
        subject=SubjectType(subject) if subject else None,
        grade=GradeLevel(grade) if grade else None,
        objective=TeachingObjective(objective) if objective else None,
        method_type=TeachingMethodType(method_type) if method_type else None,
        keywords=keywords,
        limit=limit
    )
    
    response = await teaching_practices_service.get_teaching_practices(query)
    return response.teaching_strategies


async def get_classroom_activities(
    subject: Optional[str] = None,
    grade: Optional[str] = None,
    duration: Optional[str] = None,
    limit: int = 10
) -> List[ClassroomActivity]:
    """
    获取课堂活动的便利函数
    
    Args:
        subject: 学科
        grade: 年级
        duration: 活动时长
        limit: 返回数量限制
        
    Returns:
        课堂活动列表
    """
    query = TeachingPracticeQuery(
        subject=SubjectType(subject) if subject else None,
        grade=GradeLevel(grade) if grade else None,
        limit=limit
    )
    
    response = await teaching_practices_service.get_teaching_practices(query)
    return response.classroom_activities


async def get_assessment_methods(
    subject: Optional[str] = None,
    assessment_type: Optional[str] = None,
    limit: int = 10
) -> List[AssessmentMethod]:
    """
    获取评估方法的便利函数
    
    Args:
        subject: 学科
        assessment_type: 评估类型
        limit: 返回数量限制
        
    Returns:
        评估方法列表
    """
    query = TeachingPracticeQuery(
        subject=SubjectType(subject) if subject else None,
        limit=limit
    )
    
    response = await teaching_practices_service.get_teaching_practices(query)
    return response.assessment_methods


if __name__ == "__main__":
    # 测试代码
    async def test_teaching_practices():
        """测试教学实践服务"""
        print("测试教学实践方法获取模块...")
        
        # 测试查询
        query = TeachingPracticeQuery(
            subject=SubjectType.MATH,
            grade=GradeLevel.GRADE_5,
            objective=TeachingObjective.PROBLEM_SOLVING,
            method_type=TeachingMethodType.INTERACTIVE,
            keywords=["数学", "互动"],
            limit=5
        )
        
        try:
            response = await teaching_practices_service.get_teaching_practices(query)
            
            print(f"\n获取结果:")
            print(f"- 教学策略: {len(response.teaching_strategies)}个")
            print(f"- 课堂活动: {len(response.classroom_activities)}个") 
            print(f"- 评估方法: {len(response.assessment_methods)}个")
            print(f"- 管理技巧: {len(response.classroom_management)}个")
            
            if response.teaching_strategies:
                print(f"\n第一个教学策略:")
                strategy = response.teaching_strategies[0]
                print(f"名称: {strategy.name}")
                print(f"描述: {strategy.description}")
                print(f"实施步骤: {strategy.implementation_steps}")
            
        except Exception as e:
            print(f"测试失败: {e}")
    
    # 运行测试
    asyncio.run(test_teaching_practices())