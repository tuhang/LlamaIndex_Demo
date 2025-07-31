#!/usr/bin/env python3
"""
系统功能测试脚本
"""
import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_config():
    """测试配置模块"""
    try:
        from config import settings
        print("OK 配置模块加载成功")
        print(f"   - 知识库目录: {settings.knowledge_base_dir}")
        print(f"   - 向量数据库目录: {settings.chroma_persist_dir}")
        print(f"   - OpenAI API Key: {'已配置' if settings.openai_api_key else '未配置'}")
        return True
    except Exception as e:
        print(f"FAIL 配置模块加载失败: {e}")
        return False

def test_basic_imports():
    """测试基础模块导入"""
    modules_to_test = [
        ("src.knowledge_base", "知识库模块"),
        ("src.student_data", "学生数据模块"), 
        ("src.lesson_generator", "教案生成模块"),
        ("src.web_app", "Web应用模块")
    ]
    
    success_count = 0
    for module_name, display_name in modules_to_test:
        try:
            __import__(module_name)
            print(f"OK {display_name}导入成功")
            success_count += 1
        except Exception as e:
            print(f"FAIL {display_name}导入失败: {e}")
    
    return success_count == len(modules_to_test)

def test_teaching_practices():
    """测试教学实践模块"""
    try:
        from src.teaching_practices import TeachingPracticesService
        
        service = TeachingPracticesService()
        print("OK 教学实践服务初始化成功")
        
        # 测试默认数据
        strategies = service._get_default_teaching_strategies()
        print(f"   - 默认教学策略数量: {len(strategies)}")
        
        activities = service._get_default_classroom_activities()
        print(f"   - 默认课堂活动数量: {len(activities)}")
        
        return True
    except Exception as e:
        print(f"FAIL 教学实践模块测试失败: {e}")
        return False

def test_directory_structure():
    """测试目录结构"""
    required_dirs = [
        "data",
        "data/knowledge_base", 
        "data/chroma_db",
        "data/student_data",
        "src"
    ]
    
    success_count = 0
    for dir_path in required_dirs:
        full_path = Path(__file__).parent / dir_path
        if full_path.exists():
            print(f"OK 目录存在: {dir_path}")
            success_count += 1
        else:
            print(f"FAIL 目录缺失: {dir_path}")
    
    return success_count == len(required_dirs)

def main():
    """主测试函数"""
    print("=" * 60)
    print("教育RAG系统功能测试")
    print("=" * 60)
    
    tests = [
        ("配置测试", test_config),
        ("目录结构测试", test_directory_structure),
        ("基础模块导入测试", test_basic_imports),
        ("教学实践模块测试", test_teaching_practices)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n测试: {test_name}")
        try:
            if test_func():
                passed_tests += 1
                print(f"PASS {test_name}")
            else:
                print(f"FAIL {test_name}")
        except Exception as e:
            print(f"ERROR {test_name}: {e}")
    
    print("\n" + "=" * 60)
    print(f"测试结果: {passed_tests}/{total_tests} 通过")
    
    if passed_tests == total_tests:
        print("所有测试通过！系统准备就绪。")
        print("\n接下来你可以：")
        print("   1. 运行 'python main.py' 启动系统")
        print("   2. 将教案文档放入 data/knowledge_base/ 目录")
        print("   3. 配置 .env 文件中的 OpenAI API Key") 
    else:
        print("部分测试失败，请检查配置和依赖。")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)