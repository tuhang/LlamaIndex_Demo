"""
教学实践方法获取模块简单演示
"""
import asyncio
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent.parent / "src"))

from teaching_practices import (
    TeachingPracticesService,
    TeachingPracticeQuery,
    SubjectType,
    GradeLevel,
    TeachingObjective,
    TeachingMethodType
)


async def simple_demo():
    """简单演示"""
    print("=" * 60)
    print("教学实践方法获取模块演示")
    print("=" * 60)
    
    # 创建服务实例
    service = TeachingPracticesService()
    
    # 创建查询
    query = TeachingPracticeQuery(
        subject=SubjectType.MATH,
        grade=GradeLevel.GRADE_5,
        objective=TeachingObjective.PROBLEM_SOLVING,
        method_type=TeachingMethodType.INTERACTIVE,
        keywords=["math", "interactive"],
        limit=3
    )
    
    print(f"Query Parameters:")
    print(f"- Subject: {query.subject.value if query.subject else 'None'}")
    print(f"- Grade: {query.grade.value if query.grade else 'None'}")
    print(f"- Objective: {query.objective.value if query.objective else 'None'}")
    print(f"- Method Type: {query.method_type.value if query.method_type else 'None'}")
    print(f"- Keywords: {query.keywords}")
    print(f"- Limit: {query.limit}")
    
    try:
        # 执行查询
        response = await service.get_teaching_practices(query)
        
        print(f"\nResults:")
        print(f"- Teaching Strategies: {len(response.teaching_strategies)}")
        print(f"- Classroom Activities: {len(response.classroom_activities)}")
        print(f"- Assessment Methods: {len(response.assessment_methods)}")
        print(f"- Classroom Management: {len(response.classroom_management)}")
        
        # 显示第一个教学策略
        if response.teaching_strategies:
            strategy = response.teaching_strategies[0]
            print(f"\nFirst Teaching Strategy:")
            print(f"Name: {strategy.name}")
            print(f"Description: {strategy.description}")
            print(f"Benefits: {', '.join(strategy.benefits[:3])}")
            
        # 显示第一个课堂活动
        if response.classroom_activities:
            activity = response.classroom_activities[0]
            print(f"\nFirst Classroom Activity:")
            print(f"Name: {activity.name}")
            print(f"Description: {activity.description}")
            print(f"Duration: {activity.duration}")
            
        # 显示缓存统计
        stats = service.get_cache_stats()
        print(f"\nCache Statistics:")
        print(f"- Total Entries: {stats['total_entries']}")
        print(f"- Valid Entries: {stats['valid_entries']}")
        
        print(f"\nDemo completed successfully!")
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(simple_demo())