"""
增强的教育RAG系统Web应用
集成LangChain功能，提供更强大的教案生成和管理能力
"""
import logging
import asyncio
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import traceback

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

from config import settings
from src.knowledge_base import knowledge_base
from src.langchain_document_processor import langchain_processor
from src.memory_manager import memory_manager
from src.student_data import student_data_manager
from src.lesson_generator import lesson_generator, LessonPlanRequest
from src.langchain_lesson_generator import langchain_lesson_generator, EnhancedLessonPlanRequest
from src.hybrid_rag_system import hybrid_rag, HybridQuery

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 页面配置
st.set_page_config(
    page_title="智能教案生成系统 - LangChain增强版",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

class EnhancedRAGEducationApp:
    """增强的教育RAG系统Web应用类"""
    
    def __init__(self):
        """初始化Web应用"""
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """初始化会话状态"""
        if 'user_id' not in st.session_state:
            st.session_state.user_id = f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        if 'generated_lesson_plans' not in st.session_state:
            st.session_state.generated_lesson_plans = []
        
        if 'knowledge_base_stats' not in st.session_state:
            st.session_state.knowledge_base_stats = {}
        
        if 'current_lesson_plan' not in st.session_state:
            st.session_state.current_lesson_plan = None
        
        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        if 'user_preferences' not in st.session_state:
            st.session_state.user_preferences = {}
        
        if 'generation_mode' not in st.session_state:
            st.session_state.generation_mode = "enhanced"  # enhanced or basic
    
    def run(self):
        """运行Web应用"""
        # 侧边栏导航
        page = self.render_sidebar()
        
        # 主要内容区域
        if page == "🎓 智能教案生成":
            self.render_enhanced_lesson_generation_page()
        elif page == "🔍 智能问答":
            self.render_intelligent_qa_page()
        elif page == "📚 知识库管理":
            self.render_enhanced_knowledge_base_page()
        elif page == "👥 学情分析":
            self.render_student_analysis_page()
        elif page == "🧠 记忆管理":
            self.render_memory_management_page()
        elif page == "📊 系统监控":
            self.render_system_monitoring_page()
        elif page == "📋 历史记录":
            self.render_history_page()
        elif page == "⚙️ 系统设置":
            self.render_settings_page()
    
    def render_sidebar(self) -> str:
        """渲染侧边栏"""
        st.sidebar.title("🎓 智能教案生成系统")
        st.sidebar.markdown("*LangChain + LlamaIndex 增强版*")
        st.sidebar.markdown("---")
        
        # 用户信息
        st.sidebar.subheader("👤 用户信息")
        st.sidebar.text(f"用户ID: {st.session_state.user_id[-12:]}")
        
        # 导航菜单
        page = st.sidebar.selectbox(
            "选择功能",
            [
                "🎓 智能教案生成", 
                "🔍 智能问答",
                "📚 知识库管理", 
                "👥 学情分析", 
                "🧠 记忆管理",
                "📊 系统监控",
                "📋 历史记录", 
                "⚙️ 系统设置"
            ]
        )
        
        st.sidebar.markdown("---")
        
        # 系统状态
        st.sidebar.subheader("🔧 系统状态")
        
        # 混合RAG系统状态
        try:
            system_stats = hybrid_rag.get_system_stats()
            st.sidebar.text(f"LlamaIndex: {'✅' if system_stats.get('llamaindex_available') else '❌'}")
            st.sidebar.text(f"LangChain: {'✅' if system_stats.get('langchain_available') else '❌'}")
            st.sidebar.text(f"混合检索: {'✅' if system_stats.get('ensemble_available') else '❌'}")
        except:
            st.sidebar.error("系统状态检查失败")
        
        # API状态
        api_status = "🟢 正常" if settings.openai_api_key else "🔴 未配置"
        st.sidebar.text(f"API状态: {api_status}")
        
        # 记忆统计
        try:
            memory_stats = memory_manager.get_memory_stats()
            st.sidebar.text(f"用户记忆: {memory_stats.get('total_users', 0)}")
            st.sidebar.text(f"教案历史: {memory_stats.get('total_lesson_plans', 0)}")
        except:
            pass
        
        return page
    
    def render_enhanced_lesson_generation_page(self):
        """渲染增强的教案生成页面"""
        st.title("🎓 智能教案生成")
        st.markdown("基于LangChain + LlamaIndex混合架构的智能教案生成系统")
        
        # 生成模式选择
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("📝 教案生成")
        with col2:
            generation_mode = st.selectbox(
                "生成模式",
                ["enhanced", "basic"],
                format_func=lambda x: "🚀 增强模式" if x == "enhanced" else "📝 基础模式",
                index=0 if st.session_state.generation_mode == "enhanced" else 1
            )
            st.session_state.generation_mode = generation_mode
        
        # 输入表单
        with st.form("enhanced_lesson_generation_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                class_id = st.text_input("班级ID", value="CLASS_001", help="输入班级标识符")
                subject = st.selectbox(
                    "学科",
                    ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]
                )
                grade = st.selectbox(
                    "年级",
                    ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级",
                     "七年级", "八年级", "九年级", "高一", "高二", "高三"]
                )
            
            with col2:
                topic = st.text_input("课题", help="输入具体的教学课题")
                duration = st.slider("课时长度（分钟）", 20, 90, 45, step=5)
                
                # 增强模式的额外选项
                if generation_mode == "enhanced":
                    difficulty_level = st.selectbox(
                        "难度等级",
                        ["简单", "中等", "困难"],
                        index=1
                    )
                    teaching_style = st.selectbox(
                        "教学风格",
                        ["传统", "互动", "探究", "综合"],
                        index=3
                    )
            
            # 学习目标
            learning_objectives = st.text_area(
                "学习目标（每行一个）",
                help="输入具体的学习目标，每行一个"
            ).strip().split('\n') if st.text_area(
                "学习目标（每行一个）",
                help="输入具体的学习目标，每行一个"
            ).strip() else []
            
            special_requirements = st.text_area(
                "特殊要求",
                help="输入任何特殊的教学要求或注意事项"
            )
            
            # 增强选项
            if generation_mode == "enhanced":
                col3, col4 = st.columns(2)
                with col3:
                    use_memory = st.checkbox("使用个人记忆", value=True, help="利用历史教案和偏好")
                with col4:
                    use_agent = st.checkbox("启用智能分析", value=True, help="使用AI Agent进行深度分析")
            
            generate_button = st.form_submit_button("🚀 生成教案", type="primary")
        
        # 生成教案
        if generate_button:
            if not all([class_id, subject, grade, topic]):
                st.error("请填写所有必填字段")
                return
            
            with st.spinner("正在生成教案，请稍候..."):
                try:
                    if generation_mode == "enhanced":
                        # 使用增强模式
                        request = EnhancedLessonPlanRequest(
                            user_id=st.session_state.user_id,
                            class_id=class_id,
                            subject=subject,
                            grade=grade,
                            topic=topic,
                            duration=duration,
                            learning_objectives=learning_objectives,
                            special_requirements=special_requirements,
                            difficulty_level=difficulty_level,
                            teaching_style=teaching_style,
                            use_memory=use_memory
                        )
                        
                        response = asyncio.run(
                            langchain_lesson_generator.generate_enhanced_lesson_plan(request)
                        )
                    else:
                        # 使用基础模式
                        request = LessonPlanRequest(
                            class_id=class_id,
                            subject=subject,
                            grade=grade,
                            topic=topic,
                            duration=duration,
                            learning_objectives=learning_objectives,
                            special_requirements=special_requirements
                        )
                        
                        response = asyncio.run(lesson_generator.generate_lesson_plan(request))
                    
                    # 保存到会话状态
                    st.session_state.current_lesson_plan = response
                    st.session_state.generated_lesson_plans.append(response)
                    
                    st.success("✅ 教案生成成功！")
                    
                except Exception as e:
                    st.error(f"生成教案失败: {str(e)}")
                    logger.error(f"教案生成失败: {e}\n{traceback.format_exc()}")
        
        # 显示生成的教案
        if st.session_state.current_lesson_plan:
            self.render_enhanced_lesson_plan_result(st.session_state.current_lesson_plan)
    
    def render_enhanced_lesson_plan_result(self, response):
        """渲染增强的教案生成结果"""
        st.markdown("---")
        st.subheader("📋 生成的教案")
        
        # 教案信息卡片
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            confidence = response.get('confidence_score', 0)
            st.metric("置信度", f"{confidence:.2%}")
        with col2:
            generation_method = response.get('generation_method', 'unknown')
            method_display = "🚀 增强" if generation_method.startswith('langchain') else "📝 基础"
            st.metric("生成方式", method_display)
        with col3:
            timestamp = response.get('timestamp', datetime.now().isoformat())
            time_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime("%H:%M:%S")
            st.metric("生成时间", time_str)
        with col4:
            if st.button("📥 下载教案"):
                self.download_lesson_plan(response)
        with col5:
            if st.button("⭐ 评价教案"):
                self.show_lesson_rating(response)
        
        # 标签页显示详细内容
        if response.get('generation_method', '').startswith('langchain'):
            # 增强模式的标签页
            tab1, tab2, tab3, tab4, tab5 = st.tabs([
                "📄 教案内容", 
                "🔍 智能分析", 
                "📚 参考材料", 
                "👥 学情分析", 
                "🧠 记忆信息"
            ])
            
            with tab1:
                self.render_enhanced_lesson_content(response)
            
            with tab2:
                self.render_agent_analysis(response)
            
            with tab3:
                self.render_reference_materials(response.get('reference_materials', []))
            
            with tab4:
                self.render_student_analysis(response.get('student_analysis', {}))
            
            with tab5:
                self.render_memory_information(response)
        else:
            # 基础模式的标签页
            tab1, tab2, tab3, tab4 = st.tabs([
                "📄 教案内容", 
                "📚 参考材料", 
                "👥 学情分析", 
                "🎯 教学方法"
            ])
            
            with tab1:
                self.render_lesson_content(response.get('lesson_plan', {}))
            
            with tab2:
                self.render_reference_materials(response.get('reference_materials', []))
            
            with tab3:
                self.render_student_analysis(response.get('student_analysis', {}))
            
            with tab4:
                self.render_teaching_practices(response.get('teaching_practices', {}))
    
    def render_enhanced_lesson_content(self, response):
        """渲染增强的教案内容"""
        basic_info = response.get('basic_info', {})
        
        # 基本信息
        st.subheader("基本信息")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.text(f"学科: {basic_info.get('subject', '')}")
            st.text(f"年级: {basic_info.get('grade', '')}")
        with col2:
            st.text(f"课题: {basic_info.get('topic', '')}")
            st.text(f"课时: {basic_info.get('duration', '')}分钟")
        with col3:
            st.text(f"难度: {basic_info.get('difficulty_level', '')}")
            st.text(f"风格: {basic_info.get('teaching_style', '')}")
        
        # 教案结构
        if response.get('structure'):
            st.subheader("教案结构")
            st.markdown(response['structure'])
        
        # 详细内容
        if response.get('optimized_content'):
            st.subheader("优化后的教案内容")
            st.markdown(response['optimized_content'])
        elif response.get('content'):
            st.subheader("教案内容")
            st.markdown(response['content'])
    
    def render_agent_analysis(self, response):
        """渲染智能体分析结果"""
        agent_analysis = response.get('agent_analysis', '')
        
        if agent_analysis and agent_analysis != "Agent分析不可用":
            st.subheader("🤖 智能分析结果")
            st.markdown(agent_analysis)
        else:
            st.info("智能分析功能暂时不可用")
    
    def render_memory_information(self, response):
        """渲染记忆信息"""
        st.subheader("🧠 个人记忆信息")
        
        # 显示相似历史教案
        similar_plans = memory_manager.find_similar_lesson_plans(
            st.session_state.user_id,
            response.get('basic_info', {}),
            limit=3
        )
        
        if similar_plans:
            st.write("**相似的历史教案:**")
            for i, plan in enumerate(similar_plans, 1):
                data = plan['data']
                with st.expander(f"历史教案 {i}: {data.get('subject')} - {data.get('topic')} (相似度: {plan['similarity_score']:.2%})"):
                    st.write(f"年级: {data.get('grade')}")
                    st.write(f"时间: {plan['timestamp']}")
                    if 'lesson_data' in data:
                        st.write("内容预览:", data['lesson_data'].get('content', '')[:200] + "...")
        else:
            st.info("暂无相似的历史教案")
        
        # 显示用户偏好
        preferences = memory_manager.get_user_preferences(st.session_state.user_id)
        if preferences:
            st.write("**用户偏好:**")
            st.json(preferences)
        
        # 显示教学建议
        recommendations = memory_manager.get_teaching_recommendations(
            st.session_state.user_id,
            response.get('basic_info', {})
        )
        if recommendations:
            st.write("**个性化建议:**")
            st.json(recommendations)
    
    def render_intelligent_qa_page(self):
        """渲染智能问答页面"""
        st.title("🔍 智能问答")
        st.markdown("基于混合RAG系统的智能教学问答")
        
        # 查询输入
        col1, col2 = st.columns([4, 1])
        with col1:
            query = st.text_input(
                "请输入您的问题",
                placeholder="例如：如何设计小学数学分数教学的课堂活动？",
                help="输入与教学相关的问题"
            )
        with col2:
            ask_button = st.button("🔍 提问", type="primary")
        
        # 高级选项
        with st.expander("🔧 高级选项"):
            col1, col2, col3 = st.columns(3)
            with col1:
                subject_filter = st.selectbox(
                    "学科筛选",
                    ["全部"] + ["语文", "数学", "英语", "物理", "化学", "生物", "历史", "地理", "政治"]
                )
            with col2:
                grade_filter = st.selectbox(
                    "年级筛选",
                    ["全部"] + ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级",
                     "七年级", "八年级", "九年级", "高一", "高二", "高三"]
                )
            with col3:
                fusion_method = st.selectbox(
                    "检索方法",
                    ["weighted", "rank", "similarity"],
                    format_func=lambda x: {"weighted": "加权融合", "rank": "排名融合", "similarity": "相似度融合"}[x]
                )
        
        # 处理问答
        if ask_button and query:
            with st.spinner("正在分析和检索相关信息..."):
                try:
                    # 创建混合查询
                    hybrid_query = HybridQuery(
                        query=query,
                        user_id=st.session_state.user_id,
                        subject=subject_filter if subject_filter != "全部" else None,
                        grade=grade_filter if grade_filter != "全部" else None,
                        fusion_method=fusion_method,
                        use_memory=True
                    )
                    
                    # 执行混合问答
                    result = asyncio.run(hybrid_rag.hybrid_qa(hybrid_query, include_sources=True))
                    
                    # 显示答案
                    st.subheader("💡 智能回答")
                    st.markdown(result['answer'])
                    
                    # 显示检索统计
                    if 'retrieval_stats' in result:
                        stats = result['retrieval_stats']
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("LlamaIndex结果", stats['llamaindex_count'])
                        with col2:
                            st.metric("LangChain结果", stats['langchain_count'])
                        with col3:
                            st.metric("融合结果", stats['fused_count'])
                    
                    # 显示来源文档
                    if result.get('source_documents'):
                        with st.expander(f"📚 参考来源 ({len(result['source_documents'])}个)"):
                            for i, doc in enumerate(result['source_documents'], 1):
                                st.write(f"**来源 {i}:**")
                                st.write(doc.page_content[:300] + "...")
                                if doc.metadata:
                                    st.write(f"*元数据: {doc.metadata}*")
                                st.markdown("---")
                    
                    # 保存到聊天历史
                    st.session_state.chat_history.append({
                        'query': query,
                        'answer': result['answer'],
                        'timestamp': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    st.error(f"问答处理失败: {str(e)}")
                    logger.error(f"智能问答失败: {e}\n{traceback.format_exc()}")
        
        # 显示聊天历史
        if st.session_state.chat_history:
            st.subheader("💬 聊天历史")
            for i, chat in enumerate(reversed(st.session_state.chat_history[-5:]), 1):
                with st.expander(f"对话 {i}: {chat['query'][:50]}..."):
                    st.write(f"**问题:** {chat['query']}")
                    st.write(f"**回答:** {chat['answer']}")
                    st.write(f"*时间: {chat['timestamp']}*")
    
    def render_enhanced_knowledge_base_page(self):
        """渲染增强的知识库管理页面"""
        st.title("📚 知识库管理")
        st.markdown("LangChain + LlamaIndex 双引擎知识库")
        
        # 获取统计信息
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 LlamaIndex 统计")
            try:
                llamaindex_stats = knowledge_base.get_knowledge_base_stats()
                st.metric("文档数量", llamaindex_stats.get('total_documents', 0))
                st.metric("向量片段", llamaindex_stats.get('indexed_chunks', 0))
                
                # 学科分布图
                subjects = llamaindex_stats.get('subjects', {})
                if subjects:
                    fig = px.pie(
                        values=list(subjects.values()),
                        names=list(subjects.keys()),
                        title="LlamaIndex - 学科分布"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"获取LlamaIndex统计失败: {e}")
        
        with col2:
            st.subheader("📊 LangChain 统计")
            try:
                langchain_stats = langchain_processor.get_document_stats()
                st.metric("文档数量", langchain_stats.get('total_files', 0))
                st.metric("索引文档", langchain_stats.get('indexed_documents', 0))
                
                # 文件类型分布
                file_types = langchain_stats.get('file_types', {})
                if file_types:
                    fig = px.bar(
                        x=list(file_types.keys()),
                        y=list(file_types.values()),
                        title="LangChain - 文件类型分布"
                    )
                    st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.error(f"获取LangChain统计失败: {e}")
        
        # 文档上传和处理
        st.markdown("---")
        st.subheader("📤 文档上传和处理")
        
        col1, col2 = st.columns(2)
        with col1:
            processing_engine = st.selectbox(
                "选择处理引擎",
                ["LangChain", "LlamaIndex", "双引擎"],
                help="选择用于处理文档的引擎"
            )
        
        uploaded_file = st.file_uploader(
            "选择教案文件",
            type=['docx', 'pdf', 'txt'],
            help="支持Word文档、PDF和文本文件"
        )
        
        if uploaded_file is not None:
            col1, col2, col3 = st.columns(3)
            with col1:
                subject_meta = st.selectbox("学科", ["语文", "数学", "英语", "物理", "化学", "生物"])
            with col2:
                grade_meta = st.selectbox("年级", ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"])
            with col3:
                splitter_type = st.selectbox("分割方式", ["recursive", "character", "token"])
            
            if st.button("📤 上传并处理"):
                with st.spinner("正在处理文档..."):
                    try:
                        # 保存文件
                        file_path = Path(settings.knowledge_base_dir) / uploaded_file.name
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        success_count = 0
                        
                        # 根据选择的引擎处理文档
                        if processing_engine in ["LangChain", "双引擎"]:
                            # LangChain处理
                            document = langchain_processor.load_single_document(file_path)
                            if document:
                                documents = langchain_processor.split_documents([document], splitter_type)
                                if documents:
                                    vectorstore = langchain_processor.create_vectorstore(documents)
                                    if vectorstore:
                                        success_count += 1
                                        st.success("✅ LangChain引擎处理成功！")
                        
                        if processing_engine in ["LlamaIndex", "双引擎"]:
                            # LlamaIndex处理
                            metadata = {"subject": subject_meta, "grade": grade_meta}
                            success = knowledge_base.add_lesson_plan(str(file_path), metadata)
                            if success:
                                success_count += 1
                                st.success("✅ LlamaIndex引擎处理成功！")
                        
                        if success_count > 0:
                            st.success(f"文档已成功处理（{success_count}个引擎）")
                            st.rerun()
                        else:
                            st.error("文档处理失败")
                    
                    except Exception as e:
                        st.error(f"处理失败: {e}")
        
        # 知识库搜索测试
        st.markdown("---")
        st.subheader("🔍 知识库搜索测试")
        
        test_query = st.text_input("测试查询", placeholder="输入搜索关键词")
        if st.button("🔍 搜索测试") and test_query:
            with st.spinner("搜索中..."):
                try:
                    # 执行混合搜索
                    from src.hybrid_rag_system import hybrid_search
                    results = asyncio.run(hybrid_search(
                        test_query,
                        user_id=st.session_state.user_id,
                        top_k=5
                    ))
                    
                    st.subheader("搜索结果")
                    
                    # 显示融合结果
                    if results.get('fused_results'):
                        for i, result in enumerate(results['fused_results'], 1):
                            with st.expander(f"结果 {i} - {result.get('source', 'unknown')} (分数: {result.get('score', 0):.3f})"):
                                st.write(result.get('content', '')[:500] + "...")
                                if result.get('metadata'):
                                    st.write(f"元数据: {result['metadata']}")
                    else:
                        st.info("没有找到相关结果")
                
                except Exception as e:
                    st.error(f"搜索失败: {e}")
    
    def render_memory_management_page(self):
        """渲染记忆管理页面"""
        st.title("🧠 记忆管理")
        st.markdown("个人学习偏好和教学模式记忆")
        
        # 记忆统计
        try:
            memory_stats = memory_manager.get_memory_stats()
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("总用户数", memory_stats.get('total_users', 0))
            with col2:
                st.metric("对话记忆", memory_stats.get('conversation_memories', 0))
            with col3:
                st.metric("教案历史", memory_stats.get('total_lesson_plans', 0))
            with col4:
                st.metric("用户偏好", memory_stats.get('user_preferences', 0))
        
        except Exception as e:
            st.error(f"获取记忆统计失败: {e}")
        
        st.markdown("---")
        
        # 个人记忆信息
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📚 教案生成历史")
            try:
                history = memory_manager.get_lesson_plan_history(st.session_state.user_id, limit=10)
                if history:
                    for i, entry in enumerate(history, 1):
                        data = entry['data']
                        with st.expander(f"教案 {i}: {data.get('subject')} - {data.get('topic')}"):
                            st.write(f"年级: {data.get('grade')}")
                            st.write(f"时间: {entry['timestamp']}")
                            st.write(f"使用次数: {entry.get('usage_count', 1)}")
                            if entry.get('rating'):
                                st.write(f"评分: {entry['rating']} ⭐")
                else:
                    st.info("暂无教案历史")
            except Exception as e:
                st.error(f"获取教案历史失败: {e}")
        
        with col2:
            st.subheader("⚙️ 个人偏好设置")
            
            # 偏好设置表单
            with st.form("preferences_form"):
                preferred_methods = st.multiselect(
                    "偏好的教学方法",
                    ["互动式教学", "探究式学习", "项目式学习", "合作学习", "翻转课堂", "游戏化教学"]
                )
                
                preferred_duration = st.selectbox(
                    "偏好课时长度",
                    ["40分钟", "45分钟", "50分钟", "90分钟(双课时)"]
                )
                
                teaching_style = st.selectbox(
                    "教学风格",
                    ["严谨型", "活泼型", "启发型", "实践型"]
                )
                
                difficulty_preference = st.selectbox(
                    "难度偏好",
                    ["偏简单", "中等", "偏难", "因材施教"]
                )
                
                if st.form_submit_button("💾 保存偏好"):
                    preferences = {
                        'preferred_methods': preferred_methods,
                        'preferred_duration': preferred_duration,
                        'teaching_style': teaching_style,
                        'difficulty_preference': difficulty_preference,
                        'updated_by': 'user'
                    }
                    
                    memory_manager.update_user_preferences(st.session_state.user_id, preferences)
                    st.success("偏好设置已保存！")
                    st.rerun()
            
            # 显示当前偏好
            current_prefs = memory_manager.get_user_preferences(st.session_state.user_id)
            if current_prefs:
                st.subheader("当前偏好")
                st.json(current_prefs)
        
        # 记忆清理
        st.markdown("---")
        st.subheader("🗑️ 记忆清理")
        
        col1, col2 = st.columns(2)
        with col1:
            cleanup_days = st.slider("保留天数", 1, 90, 30)
        with col2:
            if st.button("🗑️ 清理旧记忆", type="secondary"):
                with st.spinner("清理中..."):
                    try:
                        memory_manager.cleanup_old_memories(cleanup_days)
                        st.success(f"已清理超过{cleanup_days}天的旧记忆")
                        st.rerun()
                    except Exception as e:
                        st.error(f"清理失败: {e}")
    
    def render_system_monitoring_page(self):
        """渲染系统监控页面"""
        st.title("📊 系统监控")
        st.markdown("系统状态和性能监控")
        
        # 获取系统统计
        try:
            system_stats = hybrid_rag.get_system_stats()
            
            # 系统可用性
            st.subheader("🔧 系统可用性")
            col1, col2, col3 = st.columns(3)
            with col1:
                status = "✅ 正常" if system_stats.get('llamaindex_available') else "❌ 不可用"
                st.metric("LlamaIndex", status)
            with col2:
                status = "✅ 正常" if system_stats.get('langchain_available') else "❌ 不可用"
                st.metric("LangChain", status)
            with col3:
                status = "✅ 正常" if system_stats.get('ensemble_available') else "❌ 不可用"
                st.metric("混合检索", status)
            
            # 详细统计
            st.subheader("📈 详细统计")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if 'llamaindex_stats' in system_stats:
                    st.write("**LlamaIndex统计:**")
                    st.json(system_stats['llamaindex_stats'])
            
            with col2:
                if 'langchain_stats' in system_stats:
                    st.write("**LangChain统计:**")
                    st.json(system_stats['langchain_stats'])
            
            # 记忆统计
            if 'memory_stats' in system_stats:
                st.subheader("🧠 记忆统计")
                memory_stats = system_stats['memory_stats']
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("总用户", memory_stats.get('total_users', 0))
                with col2:
                    st.metric("教案历史", memory_stats.get('total_lesson_plans', 0))
                with col3:
                    st.metric("对话记忆", memory_stats.get('conversation_memories', 0))
                with col4:
                    st.metric("用户偏好", memory_stats.get('user_preferences', 0))
        
        except Exception as e:
            st.error(f"获取系统统计失败: {e}")
        
        # 实时状态检查
        st.markdown("---")
        st.subheader("🔄 实时状态检查")
        
        if st.button("🔄 刷新状态"):
            with st.spinner("检查系统状态..."):
                try:
                    # 测试各个组件
                    tests = []
                    
                    # 测试LlamaIndex
                    try:
                        if hasattr(knowledge_base, 'get_knowledge_base_stats'):
                            knowledge_base.get_knowledge_base_stats()
                            tests.append(("LlamaIndex", "✅ 正常", ""))
                        else:
                            tests.append(("LlamaIndex", "⚠️ 部分功能", "统计功能不可用"))
                    except Exception as e:
                        tests.append(("LlamaIndex", "❌ 异常", str(e)))
                    
                    # 测试LangChain
                    try:
                        if hasattr(langchain_processor, 'get_document_stats'):
                            langchain_processor.get_document_stats()
                            tests.append(("LangChain", "✅ 正常", ""))
                        else:
                            tests.append(("LangChain", "⚠️ 部分功能", "统计功能不可用"))
                    except Exception as e:
                        tests.append(("LangChain", "❌ 异常", str(e)))
                    
                    # 测试记忆管理
                    try:
                        memory_manager.get_memory_stats()
                        tests.append(("记忆管理", "✅ 正常", ""))
                    except Exception as e:
                        tests.append(("记忆管理", "❌ 异常", str(e)))
                    
                    # 显示测试结果
                    test_df = pd.DataFrame(tests, columns=['组件', '状态', '备注'])
                    st.dataframe(test_df, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"状态检查失败: {e}")
    
    def render_lesson_content(self, lesson_plan: Dict[str, Any]):
        """渲染基础教案内容"""
        if "生成内容" in lesson_plan:
            st.markdown(lesson_plan["生成内容"])
        else:
            # 结构化显示
            if "基本信息" in lesson_plan:
                st.subheader("基本信息")
                basic_info = lesson_plan["基本信息"]
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.text(f"课程: {basic_info.get('课程名称', '')}")
                    st.text(f"学科: {basic_info.get('学科', '')}")
                with col2:
                    st.text(f"年级: {basic_info.get('年级', '')}")
                    st.text(f"课时: {basic_info.get('课时', '')}")
                with col3:
                    st.text(f"日期: {basic_info.get('授课时间', '')}")
    
    def render_reference_materials(self, materials: List[Dict[str, Any]]):
        """渲染参考材料"""
        if not materials:
            st.info("没有找到相关的参考教案")
            return
        
        st.subheader(f"参考教案 ({len(materials)}个)")
        
        for i, material in enumerate(materials, 1):
            score = material.get('score', 0)
            file_name = material.get('file_name', '未知文件')
            with st.expander(f"参考教案 {i}: {file_name} (相似度: {score:.2%})"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    content = material.get('content', '')[:500] + "..."
                    st.text_area(
                        "内容摘要",
                        content,
                        height=100,
                        key=f"material_{i}"
                    )
                with col2:
                    metadata = material.get('metadata', {})
                    st.write("**元数据**")
                    st.write(f"学科: {metadata.get('subject', '未知')}")
                    st.write(f"年级: {metadata.get('grade', '未知')}")
                    st.write(f"文件类型: {metadata.get('file_type', '未知')}")
    
    def render_student_analysis(self, analysis: Dict[str, Any]):
        """渲染学情分析"""
        if not analysis:
            st.info("没有可用的学情数据")
            return
        
        # 班级表现
        if 'class_performance' in analysis:
            st.subheader("班级表现")
            perf = analysis['class_performance']
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("平均成绩", f"{perf.get('average_score', 0):.1f}")
            with col2:
                st.metric("及格率", f"{perf.get('pass_rate', 0):.1%}")
            with col3:
                st.metric("优秀率", f"{perf.get('excellence_rate', 0):.1%}")
    
    def render_teaching_practices(self, practices: Dict[str, Any]):
        """渲染教学实践方法"""
        if not practices:
            st.info("没有可用的教学实践数据")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'teaching_strategies' in practices:
                st.subheader("教学策略")
                strategies = practices['teaching_strategies']
                for strategy in strategies:
                    with st.expander(strategy.get('name', '未知策略')):
                        st.write(strategy.get('description', ''))
        
        with col2:
            if 'classroom_activities' in practices:
                st.subheader("课堂活动")
                activities = practices['classroom_activities']
                for activity in activities:
                    with st.expander(activity.get('name', '未知活动')):
                        st.write(activity.get('description', ''))
    
    def render_history_page(self):
        """渲染历史记录页面"""
        st.title("📋 教案生成历史")
        
        if not st.session_state.generated_lesson_plans:
            st.info("还没有生成任何教案")
            return
        
        # 历史记录列表
        for i, response in enumerate(reversed(st.session_state.generated_lesson_plans)):
            basic_info = response.get('basic_info', {})
            if not basic_info:
                # 兼容旧格式
                lesson_plan = response.get("lesson_plan", {})
                basic_info = lesson_plan.get("基本信息", {})
            
            timestamp = response.get('timestamp', datetime.now().isoformat())
            time_str = datetime.fromisoformat(timestamp.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
            
            with st.expander(
                f"#{len(st.session_state.generated_lesson_plans)-i} - "
                f"{basic_info.get('subject', '未知')} - {basic_info.get('topic', '未知')} "
                f"({time_str})"
            ):
                col1, col2, col3 = st.columns(3)
                with col1:
                    confidence = response.get('confidence_score', 0)
                    st.metric("置信度", f"{confidence:.2%}")
                with col2:
                    method = response.get('generation_method', 'unknown')
                    method_display = "🚀 增强" if method.startswith('langchain') else "📝 基础"
                    st.metric("生成方式", method_display)
                with col3:
                    if st.button("📋 查看详情", key=f"view_{i}"):
                        st.session_state.current_lesson_plan = response
                        st.rerun()
    
    def render_settings_page(self):
        """渲染系统设置页面"""
        st.title("⚙️ 系统设置")
        
        # API配置
        st.subheader("🔗 API 配置")
        col1, col2 = st.columns(2)
        
        with col1:
            api_key_status = "已配置" if settings.openai_api_key else "未配置"
            st.text_input("OpenAI API Key", value="●●●●●●●●" if settings.openai_api_key else "", 
                         type="password", help=f"当前状态: {api_key_status}")
            
            st.text_input("API Base URL", value=settings.openai_api_base)
        
        with col2:
            st.selectbox("嵌入模型", [settings.embedding_model], disabled=True)
            st.selectbox("生成模型", [settings.llm_model], disabled=True)
        
        # RAG参数
        st.subheader("🔧 RAG 参数")
        col1, col2 = st.columns(2)
        
        with col1:
            st.slider("文本块大小", 256, 1024, settings.chunk_size, disabled=True)
            st.slider("文本块重叠", 0, 100, settings.chunk_overlap, disabled=True)
        
        with col2:
            st.slider("相似度检索数量", 1, 10, settings.similarity_top_k, disabled=True)
            st.slider("最大参考教案数", 1, 5, settings.max_lesson_plans, disabled=True)
        
        # 系统信息
        st.subheader("ℹ️ 系统信息")
        col1, col2 = st.columns(2)
        
        with col1:
            st.text(f"知识库目录: {settings.knowledge_base_dir}")
            st.text(f"向量数据库: {settings.chroma_persist_dir}")
            st.text(f"记忆目录: {settings.student_data_dir}/memory")
        
        with col2:
            st.text(f"调试模式: {'开启' if settings.debug else '关闭'}")
            st.text(f"应用端口: {settings.app_port}")
            st.text(f"用户ID: {st.session_state.user_id}")
    
    def show_lesson_rating(self, response):
        """显示教案评分"""
        with st.form("rating_form"):
            st.subheader("⭐ 教案评价")
            rating = st.slider("请为这份教案打分", 1, 5, 3)
            feedback = st.text_area("反馈意见（可选）")
            
            if st.form_submit_button("提交评价"):
                # 保存评价到记忆系统
                try:
                    lesson_data = {
                        'subject': response.get('basic_info', {}).get('subject'),
                        'grade': response.get('basic_info', {}).get('grade'),
                        'topic': response.get('basic_info', {}).get('topic'),
                        'teaching_methods': []  # 从教案中提取
                    }
                    
                    feedback_data = {
                        'rating': rating,
                        'feedback': feedback,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    memory_manager.learn_teaching_patterns(
                        st.session_state.user_id,
                        lesson_data,
                        feedback_data
                    )
                    
                    st.success("感谢您的评价！这将帮助改进教案生成质量。")
                except Exception as e:
                    st.error(f"保存评价失败: {e}")
    
    def download_lesson_plan(self, response):
        """下载教案"""
        st.info("下载功能开发中...")

def main():
    """主函数"""
    try:
        app = EnhancedRAGEducationApp()
        app.run()
    except Exception as e:
        st.error(f"应用启动失败: {e}")
        logger.error(f"Web应用错误: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()