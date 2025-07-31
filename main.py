"""
教育RAG系统主入口
"""
import asyncio
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from config import settings

def run_web_app(enhanced=True):
    """运行Streamlit Web应用"""
    import streamlit.web.cli as stcli
    
    # 选择Web应用版本
    if enhanced:
        web_app_path = Path(__file__).parent / "src" / "enhanced_web_app.py"
        print("🚀 启动增强版Web界面...")
    else:
        web_app_path = Path(__file__).parent / "src" / "web_app.py"
        print("📝 启动基础版Web界面...")
    
    sys.argv = [
        "streamlit",
        "run",
        str(web_app_path),
        "--server.port", str(settings.app_port),
        "--server.address", settings.app_host,
        "--theme.base", "light",
        "--theme.primaryColor", "#FF6B6B",
        "--theme.backgroundColor", "#FFFFFF",
        "--theme.secondaryBackgroundColor", "#F0F2F6",
    ]
    
    stcli.main()

async def initialize_system():
    """初始化系统"""
    print("🚀 正在初始化教育RAG系统...")
    
    try:
        # 检查配置
        if not settings.openai_api_key:
            print("⚠️  警告: OpenAI API Key未配置，请在.env文件中设置")
        
        # 初始化知识库
        from src.knowledge_base import knowledge_base
        
        # 尝试加载现有索引
        index = knowledge_base.load_existing_index()
        if index is None:
            print("📚 正在构建知识库索引...")
            # 如果没有现有索引，构建新的
            try:
                knowledge_base.build_index()
                print("✅ 知识库索引构建完成")
            except Exception as e:
                print(f"⚠️  知识库索引构建失败（可能是没有教案文档）: {e}")
        else:
            print("✅ 已加载现有知识库索引")
        
        # 获取统计信息
        stats = knowledge_base.get_knowledge_base_stats()
        print(f"📊 知识库统计: {stats.get('total_documents', 0)} 个文档, {stats.get('indexed_chunks', 0)} 个向量片段")
        
        print("✅ 系统初始化完成!")
        
    except Exception as e:
        print(f"❌ 系统初始化失败: {e}")
        return False
    
    return True

async def run_demo():
    """运行命令行演示"""
    print("\n" + "=" * 50)
    print("📚 命令行演示 - 智能教案生成")
    print("=" * 50)
    
    try:
        from src.lesson_generator import generate_lesson_plan
        
        # 演示数据
        class_id = "DEMO_CLASS"
        subject = "数学"
        grade = "五年级"
        topic = "小数的加法和减法"
        learning_objectives = [
            "掌握小数加法的计算方法",
            "掌握小数减法的计算方法",
            "能够解决实际问题中的小数运算"
        ]
        
        print(f"📝 生成教案参数:")
        print(f"   班级: {class_id}")
        print(f"   学科: {subject}")
        print(f"   年级: {grade}")
        print(f"   课题: {topic}")
        print(f"   学习目标: {', '.join(learning_objectives)}")
        
        print(f"\n🔄 正在生成教案...")
        
        response = await generate_lesson_plan(
            class_id=class_id,
            subject=subject,
            grade=grade,
            topic=topic,
            learning_objectives=learning_objectives
        )
        
        print(f"\n✅ 教案生成完成!")
        print(f"📊 置信度: {response.confidence_score:.2%}")
        print(f"📚 参考教案数量: {len(response.reference_materials)}")
        print(f"⏰ 生成时间: {response.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 显示教案内容摘要
        lesson_plan = response.lesson_plan
        if "生成内容" in lesson_plan:
            print(f"\n📄 教案内容摘要:")
            content = lesson_plan["生成内容"]
            # 显示前500字符
            print(content[:500] + "..." if len(content) > 500 else content)
        
        # 显示参考材料
        if response.reference_materials:
            print(f"\n📚 参考教案:")
            for i, material in enumerate(response.reference_materials[:3], 1):
                print(f"   {i}. {material.get('file_name', '未知文件')} (相似度: {material.get('score', 0):.2%})")
        
        # 显示学情分析
        if response.student_analysis.get('class_performance'):
            perf = response.student_analysis['class_performance']
            print(f"\n👥 班级表现:")
            print(f"   平均成绩: {perf.get('average_score', 0):.1f}")
            print(f"   及格率: {perf.get('pass_rate', 0):.1%}")
            print(f"   优秀率: {perf.get('excellence_rate', 0):.1%}")
        
        print(f"\n" + "=" * 50)
        print("✅ 演示完成!")
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("=" * 60)
    print("🎓 教育行业智能教案生成系统")
    print("基于LlamaIndex + LangChain混合架构")
    print("=" * 60)
    
    # 初始化系统
    success = asyncio.run(initialize_system())
    if not success:
        return
    
    print("\n选择运行模式:")
    print("1. 增强版Web界面 (LangChain + LlamaIndex)")
    print("2. 基础版Web界面 (LlamaIndex)")
    print("3. 命令行演示")
    print("4. 退出")
    
    while True:
        try:
            choice = input("\n请选择 (1-4): ").strip()
            
            if choice == "1":
                print("🚀 启动增强版Web界面...")
                run_web_app(enhanced=True)
                break
                
            elif choice == "2":
                print("📝 启动基础版Web界面...")
                run_web_app(enhanced=False)
                break
                
            elif choice == "3":
                print("💻 运行命令行演示...")
                asyncio.run(run_demo())
                break
                
            elif choice == "4":
                print("👋 再见!")
                break
                
            else:
                print("❌ 无效选择，请输入1-4")
                
        except KeyboardInterrupt:
            print("\n👋 程序已退出")
            break
        except Exception as e:
            print(f"❌ 运行出错: {e}")
            break

if __name__ == "__main__":
    main()
