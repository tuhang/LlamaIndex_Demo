"""
基于LangChain工具链的增强教案生成模块
结合LangChain的Agents、Tools和Chains来增强教案生成能力
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass

# LangChain imports
from langchain.agents import AgentType, initialize_agent, Tool
from langchain.agents.agent_toolkits import create_retriever_tool
from langchain.chains import (
    LLMChain,
    SequentialChain,
    TransformChain,
    ConversationalRetrievalChain
)
from langchain.prompts import (
    PromptTemplate,
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.schema import Document
from langchain_openai import ChatOpenAI
from langchain.callbacks import StreamingStdOutCallbackHandler

from config import settings
from src.langchain_document_processor import langchain_processor
from src.memory_manager import memory_manager
from src.student_data import student_data_manager
from src.teaching_practices import get_teaching_practices, TeachingPracticeQuery

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class EnhancedLessonPlanRequest:
    """增强的教案生成请求"""
    user_id: str
    class_id: str
    subject: str
    grade: str
    topic: str
    duration: int = 45
    learning_objectives: List[str] = None
    special_requirements: str = ""
    difficulty_level: str = "中等"
    teaching_style: str = "综合"
    use_memory: bool = True
    
    def __post_init__(self):
        if self.learning_objectives is None:
            self.learning_objectives = []

class LangChainLessonGenerator:
    """基于LangChain的增强教案生成器"""
    
    def __init__(self):
        """初始化生成器"""
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_api_base,
            model_name=settings.llm_model,
            temperature=0.7,
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()]
        )
        
        # 初始化工具链
        self._initialize_tools()
        self._initialize_chains()
        self._initialize_agents()
    
    def _initialize_tools(self):
        """初始化工具集"""
        self.tools = []
        
        # 1. 文档检索工具
        if langchain_processor.vectorstore:
            retriever_tool = create_retriever_tool(
                langchain_processor.vectorstore.as_retriever(
                    search_kwargs={"k": settings.similarity_top_k}
                ),
                "knowledge_base_retriever",
                "检索教案知识库中的相关教案内容。输入应该是与教学主题相关的查询。"
            )
            self.tools.append(retriever_tool)
        
        # 2. 学情分析工具
        async def analyze_student_data(input_str: str) -> str:
            """分析学生学情数据"""
            try:
                # 解析输入参数
                params = eval(input_str)  # 在生产环境中应使用更安全的解析方法
                class_id = params.get('class_id', '')
                subject = params.get('subject', '')
                
                # 获取学情数据
                class_performance = await student_data_manager.get_class_performance(class_id, subject)
                knowledge_gaps = await student_data_manager.get_knowledge_gaps(class_id, subject)
                
                # 格式化结果
                analysis = f"班级表现: 平均分{class_performance.get('average_score', 0)}, "
                analysis += f"及格率{class_performance.get('pass_rate', 0):.1%}\\n"
                analysis += f"知识薄弱点: {', '.join([gap['knowledge_point'] for gap in knowledge_gaps[:3]])}"
                
                return analysis
            except Exception as e:
                return f"学情分析失败: {str(e)}"
        
        student_analysis_tool = Tool(
            name="student_analysis",
            description="分析班级学生的学习情况。输入格式: {'class_id': '班级ID', 'subject': '学科'}",
            func=lambda x: asyncio.run(analyze_student_data(x))
        )
        self.tools.append(student_analysis_tool)
        
        # 3. 教学实践建议工具
        async def get_teaching_suggestions(input_str: str) -> str:
            """获取教学实践建议"""
            try:
                params = eval(input_str)
                subject = params.get('subject', '')
                grade = params.get('grade', '')
                topic = params.get('topic', '')
                
                # 这里应该调用teaching_practices模块
                suggestions = f"针对{grade}{subject}-{topic}的教学建议:\n"
                suggestions += "1. 采用互动式教学方法\n"
                suggestions += "2. 结合多媒体辅助教学\n"
                suggestions += "3. 设计分层练习题"
                
                return suggestions
            except Exception as e:
                return f"获取教学建议失败: {str(e)}"
        
        teaching_suggestions_tool = Tool(
            name="teaching_suggestions",
            description="获取最新的教学实践建议。输入格式: {'subject': '学科', 'grade': '年级', 'topic': '主题'}",
            func=lambda x: asyncio.run(get_teaching_suggestions(x))
        )
        self.tools.append(teaching_suggestions_tool)
        
        # 4. 历史教案检索工具
        def get_lesson_history(input_str: str) -> str:
            """获取历史教案"""
            try:
                params = eval(input_str)
                user_id = params.get('user_id', '')
                current_request = params
                
                similar_plans = memory_manager.find_similar_lesson_plans(user_id, current_request, limit=3)
                
                if not similar_plans:
                    return "没有找到相似的历史教案"
                
                result = "相似的历史教案:\n"
                for i, plan in enumerate(similar_plans, 1):
                    data = plan['data']
                    result += f"{i}. {data.get('subject')}-{data.get('topic')} "
                    result += f"(相似度: {plan['similarity_score']:.2f})\n"
                
                return result
            except Exception as e:
                return f"检索历史教案失败: {str(e)}"
        
        history_tool = Tool(
            name="lesson_history",
            description="检索用户的历史教案。输入格式: {'user_id': '用户ID', 'subject': '学科', 'topic': '主题'}",
            func=get_lesson_history
        )
        self.tools.append(history_tool)
    
    def _initialize_chains(self):
        """初始化链条"""
        
        # 1. 教案结构生成链
        structure_template = """
基于以下信息，生成教案的基本结构框架：

学科: {subject}
年级: {grade}
课题: {topic}
课时: {duration}分钟
学习目标: {learning_objectives}
特殊要求: {special_requirements}

请生成包含以下部分的教案结构：
1. 教学目标（知识、能力、情感态度）
2. 教学重点和难点
3. 教学方法和策略
4. 教学准备
5. 教学过程（详细步骤）
6. 板书设计
7. 课后作业
8. 教学反思

结构框架:
"""
        
        self.structure_prompt = PromptTemplate(
            input_variables=["subject", "grade", "topic", "duration", "learning_objectives", "special_requirements"],
            template=structure_template
        )
        
        self.structure_chain = LLMChain(
            llm=self.llm,
            prompt=self.structure_prompt,
            output_key="lesson_structure"
        )
        
        # 2. 内容填充链
        content_template = """
基于教案结构框架和参考资料，生成详细的教案内容：

教案结构框架:
{lesson_structure}

参考教案资料:
{reference_materials}

学情分析:
{student_analysis}

教学实践建议:
{teaching_suggestions}

请填充详细的教案内容，确保：
1. 内容符合学生认知水平
2. 教学方法多样化
3. 重点突出，难点突破
4. 具有可操作性
5. 体现个性化教学

详细教案内容:
"""
        
        self.content_prompt = PromptTemplate(
            input_variables=["lesson_structure", "reference_materials", "student_analysis", "teaching_suggestions"],
            template=content_template
        )
        
        self.content_chain = LLMChain(
            llm=self.llm,
            prompt=self.content_prompt,
            output_key="lesson_content"
        )
        
        # 3. 个性化优化链
        optimization_template = """
基于用户历史偏好和教学模式，优化教案内容：

原始教案内容:
{lesson_content}

用户教学偏好:
{user_preferences}

历史成功模式:
{teaching_patterns}

请根据用户偏好和成功模式，优化教案的：
1. 教学方法选择
2. 活动设计
3. 时间分配
4. 评估方式
5. 差异化安排

优化后的教案:
"""
        
        self.optimization_prompt = PromptTemplate(
            input_variables=["lesson_content", "user_preferences", "teaching_patterns"],
            template=optimization_template
        )
        
        self.optimization_chain = LLMChain(
            llm=self.llm,
            prompt=self.optimization_prompt,
            output_key="optimized_lesson"
        )
        
        # 4. 完整的序列链
        self.complete_chain = SequentialChain(
            chains=[self.structure_chain, self.content_chain, self.optimization_chain],
            input_variables=["subject", "grade", "topic", "duration", "learning_objectives", 
                           "special_requirements", "reference_materials", "student_analysis", 
                           "teaching_suggestions", "user_preferences", "teaching_patterns"],
            output_variables=["lesson_structure", "lesson_content", "optimized_lesson"],
            verbose=True
        )
    
    def _initialize_agents(self):
        """初始化智能体"""
        if self.tools:
            self.agent = initialize_agent(
                tools=self.tools,
                llm=self.llm,
                agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
                verbose=True,
                max_iterations=5,
                early_stopping_method="generate"
            )
        else:
            self.agent = None
    
    async def generate_enhanced_lesson_plan(self, request: EnhancedLessonPlanRequest) -> Dict[str, Any]:
        """
        生成增强教案
        
        Args:
            request: 教案生成请求
            
        Returns:
            生成的教案数据
        """
        try:
            logger.info(f"开始生成增强教案: {request.subject} - {request.topic}")
            
            # 1. 收集上下文信息
            context = await self._gather_context(request)
            
            # 2. 使用Agent进行智能分析（如果可用）
            if self.agent:
                agent_analysis = await self._run_agent_analysis(request, context)
                context.update(agent_analysis)
            
            # 3. 生成教案结构和内容
            lesson_result = await self._generate_lesson_with_chains(request, context)
            
            # 4. 后处理和记忆更新
            final_lesson = self._post_process_lesson(lesson_result, request)
            
            # 5. 更新记忆（如果启用）
            if request.use_memory:
                self._update_memory(request, final_lesson)
            
            logger.info("增强教案生成完成")
            return final_lesson
            
        except Exception as e:
            logger.error(f"生成增强教案失败: {e}")
            # 返回基础教案作为fallback
            return await self._generate_fallback_lesson(request)
    
    async def _gather_context(self, request: EnhancedLessonPlanRequest) -> Dict[str, Any]:
        """收集上下文信息"""
        context = {}
        
        try:
            # 获取参考材料
            if langchain_processor.vectorstore:
                query = f"{request.subject} {request.topic} {request.grade} 教案"
                reference_docs = langchain_processor.similarity_search(query, k=3)
                context['reference_materials'] = "\\n".join([doc.page_content[:500] for doc in reference_docs])
            else:
                context['reference_materials'] = "暂无参考材料"
            
            # 获取学情分析
            try:
                class_performance = await student_data_manager.get_class_performance(request.class_id, request.subject)
                knowledge_gaps = await student_data_manager.get_knowledge_gaps(request.class_id, request.subject)
                
                analysis = f"班级平均分: {class_performance.get('average_score', 0)}\\n"
                analysis += f"及格率: {class_performance.get('pass_rate', 0):.1%}\\n"
                analysis += f"薄弱知识点: {', '.join([gap['knowledge_point'] for gap in knowledge_gaps[:3]])}"
                context['student_analysis'] = analysis
            except:
                context['student_analysis'] = "学情数据暂不可用"
            
            # 获取教学建议（简化版）
            context['teaching_suggestions'] = "建议采用互动式教学，结合多媒体辅助，注重实践操作"
            
            # 获取用户偏好和模式
            if request.use_memory:
                user_prefs = memory_manager.get_user_preferences(request.user_id)
                teaching_recommendations = memory_manager.get_teaching_recommendations(request.user_id, {
                    'subject': request.subject,
                    'grade': request.grade,
                    'topic': request.topic
                })
                
                context['user_preferences'] = str(user_prefs) if user_prefs else "无特定偏好"
                context['teaching_patterns'] = str(teaching_recommendations) if teaching_recommendations else "无历史模式"
            else:
                context['user_preferences'] = "无特定偏好"
                context['teaching_patterns'] = "无历史模式"
            
            return context
            
        except Exception as e:
            logger.error(f"收集上下文信息失败: {e}")
            return {
                'reference_materials': "暂无参考材料",
                'student_analysis': "学情数据暂不可用",
                'teaching_suggestions': "建议采用常规教学方法",
                'user_preferences': "无特定偏好",
                'teaching_patterns': "无历史模式"
            }
    
    async def _run_agent_analysis(self, request: EnhancedLessonPlanRequest, context: Dict[str, Any]) -> Dict[str, Any]:
        """运行Agent分析"""
        try:
            # 构建Agent查询
            agent_query = f"""
            我需要为{request.grade}的{request.subject}课程生成关于"{request.topic}"的教案。
            课时长度: {request.duration}分钟
            学习目标: {', '.join(request.learning_objectives)}
            特殊要求: {request.special_requirements}
            
            请帮我：
            1. 分析相关的教案资料
            2. 了解学生学情
            3. 获取教学实践建议
            4. 检索相似的历史教案
            """
            
            # 在线程池中运行同步的Agent
            loop = asyncio.get_event_loop()
            agent_result = await loop.run_in_executor(
                None, 
                lambda: self.agent.run(agent_query)
            )
            
            return {'agent_analysis': agent_result}
            
        except Exception as e:
            logger.error(f"Agent分析失败: {e}")
            return {'agent_analysis': "Agent分析不可用"}
    
    async def _generate_lesson_with_chains(self, request: EnhancedLessonPlanRequest, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用链条生成教案"""
        try:
            # 准备输入数据
            chain_inputs = {
                'subject': request.subject,
                'grade': request.grade,
                'topic': request.topic,
                'duration': str(request.duration),
                'learning_objectives': ', '.join(request.learning_objectives),
                'special_requirements': request.special_requirements,
                'reference_materials': context.get('reference_materials', ''),
                'student_analysis': context.get('student_analysis', ''),
                'teaching_suggestions': context.get('teaching_suggestions', ''),
                'user_preferences': context.get('user_preferences', ''),
                'teaching_patterns': context.get('teaching_patterns', '')
            }
            
            # 在线程池中运行同步的链条
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.complete_chain(chain_inputs)
            )
            
            return result
            
        except Exception as e:
            logger.error(f"链条生成教案失败: {e}")
            return {
                'lesson_structure': "基础教案结构",
                'lesson_content': "基础教案内容",
                'optimized_lesson': "教案生成失败，请重试"
            }
    
    def _post_process_lesson(self, lesson_result: Dict[str, Any], request: EnhancedLessonPlanRequest) -> Dict[str, Any]:
        """后处理教案"""
        try:
            # 构建最终的教案数据结构
            final_lesson = {
                'id': f"lesson_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'timestamp': datetime.now().isoformat(),
                'basic_info': {
                    'subject': request.subject,
                    'grade': request.grade,
                    'topic': request.topic,
                    'duration': request.duration,
                    'learning_objectives': request.learning_objectives,
                    'special_requirements': request.special_requirements,
                    'difficulty_level': request.difficulty_level,
                    'teaching_style': request.teaching_style
                },
                'structure': lesson_result.get('lesson_structure', ''),
                'content': lesson_result.get('lesson_content', ''),
                'optimized_content': lesson_result.get('optimized_lesson', ''),
                'agent_analysis': lesson_result.get('agent_analysis', ''),
                'generation_method': 'langchain_enhanced',
                'confidence_score': self._calculate_confidence_score(lesson_result)
            }
            
            return final_lesson
            
        except Exception as e:
            logger.error(f"后处理教案失败: {e}")
            return {'error': str(e)}
    
    def _update_memory(self, request: EnhancedLessonPlanRequest, lesson_data: Dict[str, Any]):
        """更新记忆"""
        try:
            # 添加到教案历史
            memory_manager.add_lesson_plan_to_history(request.user_id, {
                'subject': request.subject,
                'grade': request.grade,
                'topic': request.topic,
                'duration': request.duration,
                'teaching_methods': [],  # 从生成的教案中提取
                'lesson_data': lesson_data
            })
            
            # 学习教学模式（暂时没有反馈）
            memory_manager.learn_teaching_patterns(request.user_id, {
                'subject': request.subject,
                'grade': request.grade,
                'topic': request.topic,
                'duration': request.duration,
                'teaching_methods': []
            })
            
            logger.info(f"为用户 {request.user_id} 更新了记忆")
            
        except Exception as e:
            logger.error(f"更新记忆失败: {e}")
    
    def _calculate_confidence_score(self, lesson_result: Dict[str, Any]) -> float:
        """计算置信度分数"""
        score = 0.5  # 基础分数
        
        # 根据生成内容的完整性调整分数
        if lesson_result.get('lesson_structure'):
            score += 0.2
        if lesson_result.get('lesson_content'):
            score += 0.2
        if lesson_result.get('optimized_lesson'):
            score += 0.1
        
        return min(score, 1.0)
    
    async def _generate_fallback_lesson(self, request: EnhancedLessonPlanRequest) -> Dict[str, Any]:
        """生成fallback教案"""
        return {
            'id': f"fallback_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'basic_info': {
                'subject': request.subject,
                'grade': request.grade,
                'topic': request.topic,
                'duration': request.duration
            },
            'content': f"关于{request.subject}《{request.topic}》的基础教案模板",
            'generation_method': 'fallback',
            'confidence_score': 0.3,
            'error': "使用fallback方式生成"
        }

# 创建全局实例
langchain_lesson_generator = LangChainLessonGenerator()

# 便利函数
async def generate_enhanced_lesson_plan(
    user_id: str,
    class_id: str, 
    subject: str, 
    grade: str, 
    topic: str,
    duration: int = 45,
    learning_objectives: List[str] = None,
    special_requirements: str = "",
    difficulty_level: str = "中等",
    teaching_style: str = "综合",
    use_memory: bool = True
) -> Dict[str, Any]:
    """
    便利函数：生成增强教案
    """
    request = EnhancedLessonPlanRequest(
        user_id=user_id,
        class_id=class_id,
        subject=subject,
        grade=grade,
        topic=topic,
        duration=duration,
        learning_objectives=learning_objectives or [],
        special_requirements=special_requirements,
        difficulty_level=difficulty_level,
        teaching_style=teaching_style,
        use_memory=use_memory
    )
    
    return await langchain_lesson_generator.generate_enhanced_lesson_plan(request)