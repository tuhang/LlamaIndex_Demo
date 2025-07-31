"""
教育RAG系统Web应用
提供用户友好的界面来生成和管理教案
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
from src.student_data import student_data_manager
from src.lesson_generator import lesson_generator, LessonPlanRequest

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 页面配置
st.set_page_config(
    page_title="智能教案生成系统",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

class RAGEducationApp:
    """教育RAG系统Web应用类"""
    
    def __init__(self):
        """初始化Web应用"""
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """初始化会话状态"""
        if 'generated_lesson_plans' not in st.session_state:
            st.session_state.generated_lesson_plans = []
        
        if 'knowledge_base_stats' not in st.session_state:
            st.session_state.knowledge_base_stats = {}
        
        if 'current_lesson_plan' not in st.session_state:
            st.session_state.current_lesson_plan = None
    
    def run(self):
        """运行Web应用"""
        # 侧边栏导航
        page = self.render_sidebar()
        
        # 主要内容区域
        if page == "📚 教案生成":
            self.render_lesson_generation_page()
        elif page == "📊 知识库管理":
            self.render_knowledge_base_page()
        elif page == "👥 学情分析":
            self.render_student_analysis_page()
        elif page == "📋 历史记录":
            self.render_history_page()
        elif page == "⚙️ 系统设置":
            self.render_settings_page()
    
    def render_sidebar(self) -> str:
        """渲染侧边栏"""
        st.sidebar.title("🎓 智能教案生成系统")
        st.sidebar.markdown("---")
        
        # 导航菜单
        page = st.sidebar.selectbox(
            "选择功能",
            ["📚 教案生成", "📊 知识库管理", "👥 学情分析", "📋 历史记录", "⚙️ 系统设置"]
        )
        
        st.sidebar.markdown("---")
        
        # 系统状态
        st.sidebar.subheader("系统状态")
        
        # 知识库状态
        try:
            stats = knowledge_base.get_knowledge_base_stats()
            st.sidebar.metric("知识库文档", stats.get('total_documents', 0))
            st.sidebar.metric("向量化片段", stats.get('indexed_chunks', 0))
        except:
            st.sidebar.error("知识库连接失败")
        
        # API状态
        api_status = "🟢 正常" if settings.openai_api_key else "🔴 未配置"
        st.sidebar.text(f"API状态: {api_status}")
        
        return page
    
    def render_lesson_generation_page(self):
        """渲染教案生成页面"""
        st.title("📚 智能教案生成")
        st.markdown("基于知识库检索、学情分析和最新教学实践方法生成个性化教案")
        
        # 输入表单
        with st.form("lesson_generation_form"):
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
            
            generate_button = st.form_submit_button("🚀 生成教案", type="primary")
        
        # 生成教案
        if generate_button:
            if not all([class_id, subject, grade, topic]):
                st.error("请填写所有必填字段")
                return
            
            with st.spinner("正在生成教案，请稍候..."):
                try:
                    # 创建请求
                    request = LessonPlanRequest(
                        class_id=class_id,
                        subject=subject,
                        grade=grade,
                        topic=topic,
                        duration=duration,
                        learning_objectives=learning_objectives,
                        special_requirements=special_requirements
                    )
                    
                    # 生成教案（使用异步包装器）
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
            self.render_lesson_plan_result(st.session_state.current_lesson_plan)
    
    def render_lesson_plan_result(self, response):
        """渲染教案生成结果"""
        st.markdown("---")
        st.subheader("📋 生成的教案")
        
        # 教案信息卡片
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("置信度", f"{response.confidence_score:.2%}")
        with col2:
            st.metric("参考教案", len(response.reference_materials))
        with col3:
            st.metric("生成时间", response.generated_at.strftime("%H:%M:%S"))
        with col4:
            if st.button("📥 下载教案"):
                self.download_lesson_plan(response)
        
        # 标签页显示详细内容
        tab1, tab2, tab3, tab4 = st.tabs(["📄 教案内容", "📚 参考材料", "👥 学情分析", "🎯 教学方法"])
        
        with tab1:
            self.render_lesson_content(response.lesson_plan)
        
        with tab2:
            self.render_reference_materials(response.reference_materials)
        
        with tab3:
            self.render_student_analysis(response.student_analysis)
        
        with tab4:
            self.render_teaching_practices(response.teaching_practices)
    
    def render_lesson_content(self, lesson_plan: Dict[str, Any]):
        """渲染教案内容"""
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
            
            if "教学目标" in lesson_plan:
                st.subheader("教学目标")
                objectives = lesson_plan["教学目标"]
                for obj_type, obj_list in objectives.items():
                    if obj_list:
                        st.write(f"**{obj_type}:**")
                        for obj in obj_list:
                            st.write(f"- {obj}")
    
    def render_reference_materials(self, materials: List[Dict[str, Any]]):
        """渲染参考材料"""
        if not materials:
            st.info("没有找到相关的参考教案")
            return
        
        st.subheader(f"参考教案 ({len(materials)}个)")
        
        for i, material in enumerate(materials, 1):
            with st.expander(f"参考教案 {i}: {material.get('file_name', '未知文件')} (相似度: {material.get('score', 0):.2%})"):
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.text_area(
                        "内容摘要",
                        material.get('content', '')[:500] + "...",
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
            
            # 难度分布图表
            if 'difficulty_distribution' in perf:
                st.subheader("难度掌握情况")
                diff_data = perf['difficulty_distribution']
                fig = px.bar(
                    x=list(diff_data.keys()),
                    y=list(diff_data.values()),
                    title="各难度题型掌握率"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # 知识薄弱点
        if 'knowledge_gaps' in analysis:
            st.subheader("知识薄弱点")
            gaps = analysis['knowledge_gaps']
            
            if gaps:
                gap_df = pd.DataFrame(gaps)
                fig = px.bar(
                    gap_df,
                    x='knowledge_point',
                    y='mastery_rate',
                    title="知识点掌握率",
                    color='difficulty_level'
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 详细列表
                for gap in gaps:
                    with st.expander(f"{gap['knowledge_point']} (掌握率: {gap['mastery_rate']:.1%})"):
                        st.write(f"**难度等级:** {gap['difficulty_level']}")
                        st.write(f"**前置技能:** {', '.join(gap.get('prerequisite_skills', []))}")
                        st.write(f"**常见错误:** {', '.join(gap.get('common_errors', []))}")
    
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
                        if 'benefits' in strategy:
                            st.write(f"**优势:** {', '.join(strategy['benefits'])}")
            
            if 'assessment_methods' in practices:
                st.subheader("评估方法")
                methods = practices['assessment_methods']
                for method in methods:
                    with st.expander(method.get('name', '未知方法')):
                        st.write(method.get('description', ''))
                        st.write(f"**类型:** {method.get('type', '未知')}")
        
        with col2:
            if 'classroom_activities' in practices:
                st.subheader("课堂活动")
                activities = practices['classroom_activities']
                for activity in activities:
                    with st.expander(activity.get('name', '未知活动')):
                        st.write(activity.get('description', ''))
                        st.write(f"**时长:** {activity.get('duration', '未知')}")
            
            if 'classroom_management' in practices:
                st.subheader("课堂管理")
                management = practices['classroom_management']
                for mgmt in management:
                    with st.expander(mgmt.get('category', '未知类别')):
                        st.write(f"**技巧:** {mgmt.get('technique', '')}")
                        st.write(f"**干预方法:** {mgmt.get('intervention', '')}")
    
    def render_knowledge_base_page(self):
        """渲染知识库管理页面"""
        st.title("📊 知识库管理")
        
        # 获取知识库统计信息
        try:
            stats = knowledge_base.get_knowledge_base_stats()
            st.session_state.knowledge_base_stats = stats
        except Exception as e:
            st.error(f"获取知识库信息失败: {e}")
            return
        
        # 统计信息卡片
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总文档数", stats.get('total_documents', 0))
        with col2:
            st.metric("向量化片段", stats.get('indexed_chunks', 0))
        with col3:
            subjects = stats.get('subjects', {})
            st.metric("学科数量", len(subjects))
        with col4:
            grades = stats.get('grades', {})
            st.metric("年级覆盖", len(grades))
        
        # 详细统计图表
        col1, col2 = st.columns(2)
        
        with col1:
            if subjects:
                st.subheader("学科分布")
                fig = px.pie(
                    values=list(subjects.values()),
                    names=list(subjects.keys()),
                    title="按学科分类的文档数量"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            if grades:
                st.subheader("年级分布")
                fig = px.bar(
                    x=list(grades.keys()),
                    y=list(grades.values()),
                    title="按年级分类的文档数量"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # 文档上传功能
        st.markdown("---")
        st.subheader("📤 上传新教案")
        
        uploaded_file = st.file_uploader(
            "选择教案文件",
            type=['docx', 'pdf', 'txt'],
            help="支持Word文档、PDF和文本文件"
        )
        
        if uploaded_file is not None:
            col1, col2 = st.columns(2)
            with col1:
                subject_meta = st.selectbox("学科", ["语文", "数学", "英语", "物理", "化学", "生物"])
                grade_meta = st.selectbox("年级", ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"])
            
            if st.button("上传并处理"):
                with st.spinner("正在处理文档..."):
                    try:
                        # 保存文件
                        file_path = Path(settings.knowledge_base_dir) / uploaded_file.name
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                        
                        # 添加到知识库
                        metadata = {"subject": subject_meta, "grade": grade_meta}
                        success = knowledge_base.add_lesson_plan(str(file_path), metadata)
                        
                        if success:
                            st.success("✅ 文档上传并处理成功！")
                            st.rerun()
                        else:
                            st.error("处理文档失败")
                    
                    except Exception as e:
                        st.error(f"上传失败: {e}")
    
    def render_student_analysis_page(self):
        """渲染学情分析页面"""
        st.title("👥 学情分析")
        
        # 输入参数
        col1, col2 = st.columns(2)
        with col1:
            class_id = st.text_input("班级ID", value="CLASS_001")
            subject = st.selectbox("分析学科", ["语文", "数学", "英语", "物理", "化学"])
        with col2:
            time_range = st.slider("时间范围（天）", 7, 90, 30)
        
        if st.button("📊 开始分析"):
            with st.spinner("正在分析学情数据..."):
                try:
                    # 获取班级表现
                    class_performance = asyncio.run(
                        student_data_manager.get_class_performance(class_id, subject, time_range)
                    )
                    
                    # 获取知识薄弱点
                    knowledge_gaps = asyncio.run(
                        student_data_manager.get_knowledge_gaps(class_id, subject)
                    )
                    
                    # 显示结果
                    self.render_student_analysis({
                        'class_performance': class_performance,
                        'knowledge_gaps': knowledge_gaps
                    })
                    
                except Exception as e:
                    st.error(f"分析失败: {e}")
    
    def render_history_page(self):
        """渲染历史记录页面"""
        st.title("📋 教案生成历史")
        
        if not st.session_state.generated_lesson_plans:
            st.info("还没有生成任何教案")
            return
        
        # 历史记录列表
        for i, response in enumerate(reversed(st.session_state.generated_lesson_plans)):
            lesson_plan = response.lesson_plan
            basic_info = lesson_plan.get("基本信息", {})
            
            with st.expander(
                f"#{len(st.session_state.generated_lesson_plans)-i} - "
                f"{basic_info.get('学科', '未知')} - {basic_info.get('课程名称', '未知')} "
                f"({response.generated_at.strftime('%Y-%m-%d %H:%M')})"
            ):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("置信度", f"{response.confidence_score:.2%}")
                with col2:
                    st.metric("参考教案", len(response.reference_materials))
                with col3:
                    if st.button("📋 查看详情", key=f"view_{i}"):
                        st.session_state.current_lesson_plan = response
                        st.rerun()
    
    def render_settings_page(self):
        """渲染系统设置页面"""
        st.title("⚙️ 系统设置")
        
        # API配置
        st.subheader("API 配置")
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
        st.subheader("RAG 参数")
        col1, col2 = st.columns(2)
        
        with col1:
            st.slider("文本块大小", 256, 1024, settings.chunk_size, disabled=True)
            st.slider("文本块重叠", 0, 100, settings.chunk_overlap, disabled=True)
        
        with col2:
            st.slider("相似度检索数量", 1, 10, settings.similarity_top_k, disabled=True)
            st.slider("最大参考教案数", 1, 5, settings.max_lesson_plans, disabled=True)
        
        # 系统信息
        st.subheader("系统信息")
        col1, col2 = st.columns(2)
        
        with col1:
            st.text(f"知识库目录: {settings.knowledge_base_dir}")
            st.text(f"向量数据库: {settings.chroma_persist_dir}")
        
        with col2:
            st.text(f"调试模式: {'开启' if settings.debug else '关闭'}")
            st.text(f"应用端口: {settings.app_port}")
    
    def download_lesson_plan(self, response):
        """下载教案"""
        # 这里可以实现教案下载功能
        st.info("下载功能开发中...")

def main():
    """主函数"""
    try:
        app = RAGEducationApp()
        app.run()
    except Exception as e:
        st.error(f"应用启动失败: {e}")
        logger.error(f"Web应用错误: {e}\n{traceback.format_exc()}")

if __name__ == "__main__":
    main()