"""
教学实践方法获取模块演示
展示如何使用Context7集成的教学实践服务
"""
import asyncio
import json
from pathlib import Path
import sys

# 添加父目录到路径
sys.path.append(str(Path(__file__).parent.parent))

from src.teaching_practices import (
    TeachingPracticesService,
    TeachingPracticeQuery,
    SubjectType,
    GradeLevel,
    TeachingObjective,
    TeachingMethodType,
    get_teaching_strategies,
    get_classroom_activities,
    get_assessment_methods
)


async def demo_basic_query():
    """演示基本查询功能"""
    print("=" * 60)
    print("演示1: 基本教学实践查询")
    print("=" * 60)
    
    service = TeachingPracticesService()
    
    # 创建查询
    query = TeachingPracticeQuery(
        subject=SubjectType.MATH,
        grade=GradeLevel.GRADE_5,
        objective=TeachingObjective.PROBLEM_SOLVING,
        method_type=TeachingMethodType.INTERACTIVE,
        keywords=["数学", "互动", "解决问题"],
        limit=3
    )
    
    print(f"查询参数:")
    print(f"- 学科: {query.subject.value if query.subject else '无'}")
    print(f"- 年级: {query.grade.value if query.grade else '无'}")
    print(f"- 教学目标: {query.objective.value if query.objective else '无'}")
    print(f"- 方法类型: {query.method_type.value if query.method_type else '无'}")
    print(f"- 关键词: {query.keywords}")
    print(f"- 限制数量: {query.limit}")
    
    try:
        response = await service.get_teaching_practices(query)
        
        print(f"\n查询结果:")
        print(f"- 教学策略: {len(response.teaching_strategies)}个")
        print(f"- 课堂活动: {len(response.classroom_activities)}个")
        print(f"- 评估方法: {len(response.assessment_methods)}个")
        print(f"- 管理技巧: {len(response.classroom_management)}个")
        
        # 显示详细的教学策略
        print(f"\n📚 教学策略详情:")
        for i, strategy in enumerate(response.teaching_strategies, 1):
            print(f"\n{i}. {strategy.name}")
            print(f"   描述: {strategy.description}")
            print(f"   适用学科: {', '.join(strategy.subject_areas)}")
            print(f"   适用年级: {', '.join(strategy.grade_levels)}")
            print(f"   实施步骤:")
            for step in strategy.implementation_steps:
                print(f"   - {step}")
            print(f"   优势: {', '.join(strategy.benefits)}")
        
        # 显示课堂活动
        print(f"\n🎯 课堂活动详情:")
        for i, activity in enumerate(response.classroom_activities, 1):
            print(f"\n{i}. {activity.name}")
            print(f"   描述: {activity.description}")
            print(f"   时长: {activity.duration}")
            print(f"   所需材料: {', '.join(activity.materials)}")
            print(f"   学习成果: {', '.join(activity.learning_outcomes)}")
        
        # 显示评估方法
        print(f"\n📊 评估方法详情:")
        for i, method in enumerate(response.assessment_methods, 1):
            print(f"\n{i}. {method.name}")
            print(f"   类型: {method.type}")
            print(f"   描述: {method.description}")
            print(f"   使用时机: {method.when_to_use}")
            print(f"   实施方法: {', '.join(method.implementation)}")
        
    except Exception as e:
        print(f"查询失败: {e}")


async def demo_subject_specific_query():
    """演示学科特定查询"""
    print("\n" + "=" * 60)
    print("演示2: 学科特定教学方法查询")
    print("=" * 60)
    
    subjects = [
        (SubjectType.ENGLISH, GradeLevel.GRADE_8),
        (SubjectType.PHYSICS, GradeLevel.GRADE_11),
        (SubjectType.CHINESE, GradeLevel.GRADE_3)
    ]
    
    for subject, grade in subjects:
        print(f"\n🔍 查询 {subject.value} - {grade.value} 教学方法:")
        
        try:
            strategies = await get_teaching_strategies(
                subject=subject.value,
                grade=grade.value,
                limit=2
            )
            
            print(f"找到 {len(strategies)} 个教学策略:")
            for strategy in strategies:
                print(f"- {strategy.name}: {strategy.description}")
                
        except Exception as e:
            print(f"查询失败: {e}")


async def demo_activity_search():
    """演示活动搜索功能"""
    print("\n" + "=" * 60)
    print("演示3: 课堂活动搜索")
    print("=" * 60)
    
    search_params = [
        {"subject": SubjectType.MATH.value, "grade": GradeLevel.GRADE_6.value},
        {"subject": SubjectType.PHYSICS.value, "grade": GradeLevel.GRADE_9.value},
        {"subject": None, "grade": GradeLevel.GRADE_1.value}  # 通用活动
    ]
    
    for params in search_params:
        subject_str = params["subject"] or "通用"
        grade_str = params["grade"]
        print(f"\n🎲 搜索 {subject_str} - {grade_str} 课堂活动:")
        
        try:
            activities = await get_classroom_activities(
                subject=params["subject"],
                grade=params["grade"],
                limit=2
            )
            
            print(f"找到 {len(activities)} 个课堂活动:")
            for activity in activities:
                print(f"- {activity.name} ({activity.duration})")
                print(f"  {activity.description}")
                
        except Exception as e:
            print(f"搜索失败: {e}")


async def demo_assessment_methods():
    """演示评估方法查询"""
    print("\n" + "=" * 60)
    print("演示4: 评估方法查询")
    print("=" * 60)
    
    subjects = [SubjectType.MATH.value, SubjectType.ENGLISH.value, None]
    
    for subject in subjects:
        subject_str = subject or "通用"
        print(f"\n📋 查询 {subject_str} 评估方法:")
        
        try:
            methods = await get_assessment_methods(
                subject=subject,
                limit=2
            )
            
            print(f"找到 {len(methods)} 个评估方法:")
            for method in methods:
                print(f"- {method.name} ({method.type})")
                print(f"  {method.description}")
                print(f"  使用时机: {method.when_to_use}")
                
        except Exception as e:
            print(f"查询失败: {e}")


async def demo_cache_functionality():
    """演示缓存功能"""
    print("\n" + "=" * 60)
    print("演示5: 缓存功能测试")
    print("=" * 60)
    
    service = TeachingPracticesService()
    
    # 获取缓存统计
    stats = service.get_cache_stats()
    print(f"初始缓存状态: {stats}")
    
    # 执行查询（应该缓存结果）
    query = TeachingPracticeQuery(
        subject=SubjectType.CHINESE,
        grade=GradeLevel.GRADE_4,
        limit=2
    )
    
    print(f"\n执行第一次查询...")
    import time
    start_time = time.time()
    response1 = await service.get_teaching_practices(query)
    first_query_time = time.time() - start_time
    
    stats = service.get_cache_stats()
    print(f"第一次查询后缓存状态: {stats}")
    print(f"查询时间: {first_query_time:.2f}秒")
    
    print(f"\n执行第二次相同查询（应该使用缓存）...")
    start_time = time.time()
    response2 = await service.get_teaching_practices(query)
    second_query_time = time.time() - start_time
    
    print(f"第二次查询时间: {second_query_time:.2f}秒")
    print(f"时间差: {first_query_time - second_query_time:.2f}秒")
    
    # 验证结果一致性
    same_results = (len(response1.teaching_strategies) == len(response2.teaching_strategies))
    print(f"结果一致性: {same_results}")
    
    # 清除缓存
    service.clear_cache()
    stats = service.get_cache_stats()
    print(f"清除缓存后状态: {stats}")


async def demo_error_handling():
    """演示错误处理"""
    print("\n" + "=" * 60)
    print("演示6: 错误处理和降级方案")
    print("=" * 60)
    
    service = TeachingPracticesService()
    
    # 测试无效API密钥情况（模拟Context7服务不可用）
    print("模拟Context7服务不可用情况...")
    
    # 临时禁用API密钥
    original_api_key = service.context7_client.api_key
    service.context7_client.api_key = "invalid_key"
    
    try:
        query = TeachingPracticeQuery(
            subject=SubjectType.BIOLOGY,
            grade=GradeLevel.GRADE_7,
            limit=2
        )
        
        response = await service.get_teaching_practices(query)
        
        print(f"降级响应结果:")
        print(f"- 教学策略: {len(response.teaching_strategies)}个")
        print(f"- 课堂活动: {len(response.classroom_activities)}个")
        print(f"- 评估方法: {len(response.assessment_methods)}个")
        print(f"- 管理技巧: {len(response.classroom_management)}个")
        
        print(f"\n即使Context7不可用，系统仍能提供默认的教学实践建议")
        
        if response.teaching_strategies:
            strategy = response.teaching_strategies[0]
            print(f"示例策略: {strategy.name}")
            print(f"描述: {strategy.description}")
        
    except Exception as e:
        print(f"错误处理测试失败: {e}")
    finally:
        # 恢复API密钥
        service.context7_client.api_key = original_api_key


async def demo_comprehensive_search():
    """演示综合搜索功能"""
    print("\n" + "=" * 60)
    print("演示7: 综合教学实践搜索")
    print("=" * 60)
    
    # 模拟真实的教学场景查询
    scenarios = [
        {
            "name": "小学数学应用题教学",
            "query": TeachingPracticeQuery(
                subject=SubjectType.MATH,
                grade=GradeLevel.GRADE_3,
                objective=TeachingObjective.PROBLEM_SOLVING,
                method_type=TeachingMethodType.INQUIRY_BASED,
                keywords=["应用题", "解题策略", "数学思维"],
                limit=2
            )
        },
        {
            "name": "中学英语口语交际",
            "query": TeachingPracticeQuery(
                subject=SubjectType.ENGLISH,
                grade=GradeLevel.GRADE_8,
                objective=TeachingObjective.COMMUNICATION,
                method_type=TeachingMethodType.COLLABORATIVE,
                keywords=["口语", "交际", "对话"],
                limit=2
            )
        },
        {
            "name": "高中物理实验教学",
            "query": TeachingPracticeQuery(
                subject=SubjectType.PHYSICS,
                grade=GradeLevel.GRADE_11,
                objective=TeachingObjective.SKILL_DEVELOPMENT,
                method_type=TeachingMethodType.EXPERIENTIAL,
                keywords=["实验", "动手操作", "科学探究"],
                limit=2
            )
        }
    ]
    
    service = TeachingPracticesService()
    
    for scenario in scenarios:
        print(f"\n📖 场景: {scenario['name']}")
        print("-" * 40)
        
        try:
            response = await service.get_teaching_practices(scenario['query'])
            
            print(f"获得 {len(response.teaching_strategies)} 个教学策略和 {len(response.classroom_activities)} 个课堂活动")
            
            # 显示最相关的策略
            if response.teaching_strategies:
                strategy = response.teaching_strategies[0]
                print(f"\n💡 推荐策略: {strategy.name}")
                print(f"   {strategy.description}")
                print(f"   实施步骤: {' → '.join(strategy.implementation_steps[:3])}...")
            
            # 显示最相关的活动
            if response.classroom_activities:
                activity = response.classroom_activities[0]
                print(f"\n🎯 推荐活动: {activity.name}")
                print(f"   {activity.description}")
                print(f"   时长: {activity.duration}")
            
            # 显示管理建议
            if response.classroom_management:
                management = response.classroom_management[0]
                print(f"\n📋 管理建议: {management.category}")
                print(f"   技巧: {', '.join(management.techniques[:2])}...")
            
        except Exception as e:
            print(f"场景查询失败: {e}")


async def generate_teaching_report():
    """生成教学实践报告"""
    print("\n" + "=" * 60)
    print("演示8: 生成教学实践报告")
    print("=" * 60)
    
    service = TeachingPracticesService()
    
    # 为特定学科和年级生成综合报告
    query = TeachingPracticeQuery(
        subject=SubjectType.CHINESE,
        grade=GradeLevel.GRADE_5,
        limit=5
    )
    
    try:
        response = await service.get_teaching_practices(query)
        
        # 生成报告
        report = {
            "report_title": f"{query.subject.value} {query.grade.value} 教学实践指南",
            "generated_at": response.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "summary": {
                "teaching_strategies_count": len(response.teaching_strategies),
                "classroom_activities_count": len(response.classroom_activities),
                "assessment_methods_count": len(response.assessment_methods),
                "management_tips_count": len(response.classroom_management)
            },
            "content": {
                "strategies": [
                    {
                        "name": s.name,
                        "description": s.description,
                        "benefits": s.benefits
                    }
                    for s in response.teaching_strategies
                ],
                "activities": [
                    {
                        "name": a.name,
                        "description": a.description,
                        "duration": a.duration
                    }
                    for a in response.classroom_activities
                ],
                "assessment": [
                    {
                        "name": m.name,
                        "type": m.type,
                        "description": m.description
                    }
                    for m in response.assessment_methods
                ]
            }
        }
        
        # 保存报告到文件
        report_file = Path(__file__).parent / "teaching_practices_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 教学实践报告已生成: {report_file}")
        print(f"📊 报告摘要:")
        print(f"   - 教学策略: {report['summary']['teaching_strategies_count']}个")
        print(f"   - 课堂活动: {report['summary']['classroom_activities_count']}个")
        print(f"   - 评估方法: {report['summary']['assessment_methods_count']}个")
        print(f"   - 管理技巧: {report['summary']['management_tips_count']}个")
        
    except Exception as e:
        print(f"生成报告失败: {e}")


async def main():
    """主演示函数"""
    print("🎓 教学实践方法获取模块演示")
    print("集成Context7 MCP服务，获取最新教育教学实践")
    print("=" * 80)
    
    # 运行所有演示
    demos = [
        demo_basic_query,
        demo_subject_specific_query,
        demo_activity_search,
        demo_assessment_methods,
        demo_cache_functionality,
        demo_error_handling,
        demo_comprehensive_search,
        generate_teaching_report
    ]
    
    for demo in demos:
        try:
            await demo()
            await asyncio.sleep(1)  # 短暂暂停，避免请求过快
        except KeyboardInterrupt:
            print("\n演示被用户中断")
            break
        except Exception as e:
            print(f"\n演示 {demo.__name__} 出现错误: {e}")
            continue
    
    print("\n" + "=" * 80)
    print("🎉 教学实践方法获取模块演示完成！")
    print("=" * 80)


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())