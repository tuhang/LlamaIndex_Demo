"""
教学实践方法模块测试
"""
import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent.parent / "src"))

from teaching_practices import (
    TeachingPracticesService,
    TeachingPracticeQuery,
    SubjectType,
    GradeLevel,
    TeachingObjective,
    TeachingMethodType,
    Context7Client,
    TeachingStrategy,
    ClassroomActivity,
    AssessmentMethod,
    ClassroomManagement
)


class TestTeachingPracticeQuery:
    """测试教学实践查询参数"""
    
    def test_query_creation(self):
        """测试查询对象创建"""
        query = TeachingPracticeQuery(
            subject=SubjectType.MATH,
            grade=GradeLevel.GRADE_5,
            objective=TeachingObjective.PROBLEM_SOLVING,
            method_type=TeachingMethodType.INTERACTIVE,
            keywords=["数学", "互动"],
            limit=10
        )
        
        assert query.subject == SubjectType.MATH
        assert query.grade == GradeLevel.GRADE_5
        assert query.objective == TeachingObjective.PROBLEM_SOLVING
        assert query.method_type == TeachingMethodType.INTERACTIVE
        assert query.keywords == ["数学", "互动"]
        assert query.limit == 10
        assert query.language == "zh-CN"
    
    def test_query_defaults(self):
        """测试查询默认值"""
        query = TeachingPracticeQuery()
        
        assert query.subject is None
        assert query.grade is None
        assert query.objective is None
        assert query.method_type is None
        assert query.keywords is None
        assert query.language == "zh-CN"
        assert query.limit == 10


class TestContext7Client:
    """测试Context7客户端"""
    
    def test_client_initialization(self):
        """测试客户端初始化"""
        client = Context7Client(api_key="test_key")
        
        assert client.api_key == "test_key"
        assert client.base_url == "https://api.context7.dev/v1"
        assert client.timeout == 30.0
    
    def test_client_no_api_key(self):
        """测试无API密钥初始化"""
        with patch('teaching_practices.settings.context7_api_key', None):
            client = Context7Client()
            assert client.api_key is None
    
    @pytest.mark.asyncio
    async def test_resolve_library_id_success(self):
        """测试解析库ID成功"""
        client = Context7Client(api_key="test_key")
        
        # 模拟成功响应
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"library_id": "education_lib_123"}
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            library_id = await client.resolve_library_id("教学方法")
            
            assert library_id == "education_lib_123"
    
    @pytest.mark.asyncio
    async def test_resolve_library_id_failure(self):
        """测试解析库ID失败"""
        client = Context7Client(api_key="test_key")
        
        # 模拟失败响应
        mock_response = AsyncMock()
        mock_response.status_code = 404
        mock_response.text = "Not found"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            library_id = await client.resolve_library_id("不存在的库")
            
            assert library_id is None
    
    @pytest.mark.asyncio
    async def test_get_library_docs_success(self):
        """测试获取库文档成功"""
        client = Context7Client(api_key="test_key")
        
        # 模拟成功响应
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "content": "教学策略内容...",
            "metadata": {"source": "education_lib"}
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            docs = await client.get_library_docs("lib_123", "教学策略")
            
            assert docs is not None
            assert "content" in docs
            assert docs["content"] == "教学策略内容..."
    
    @pytest.mark.asyncio
    async def test_get_library_docs_failure(self):
        """测试获取库文档失败"""
        client = Context7Client(api_key="test_key")
        
        # 模拟失败响应
        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Internal server error"
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.return_value = mock_response
            
            docs = await client.get_library_docs("lib_123", "教学策略")
            
            assert docs is None


class TestTeachingPracticesService:
    """测试教学实践服务"""
    
    def test_service_initialization(self):
        """测试服务初始化"""
        service = TeachingPracticesService()
        
        assert service.context7_client is not None
        assert service.cache == {}
        assert service.cache_ttl == 3600
    
    def test_cache_key_generation(self):
        """测试缓存键生成"""
        service = TeachingPracticesService()
        
        query1 = TeachingPracticeQuery(subject=SubjectType.MATH, limit=5)
        query2 = TeachingPracticeQuery(subject=SubjectType.MATH, limit=5)
        query3 = TeachingPracticeQuery(subject=SubjectType.ENGLISH, limit=5)
        
        key1 = service._generate_cache_key(query1)
        key2 = service._generate_cache_key(query2)
        key3 = service._generate_cache_key(query3)
        
        # 相同查询应该产生相同的键
        assert key1 == key2
        # 不同查询应该产生不同的键
        assert key1 != key3
    
    def test_cache_validity(self):
        """测试缓存有效性检查"""
        service = TeachingPracticesService()
        
        # 无时间戳的缓存条目
        invalid_entry = {"data": "test"}
        assert not service._is_cache_valid(invalid_entry)
        
        # 过期的缓存条目
        from datetime import datetime, timedelta
        expired_time = datetime.now() - timedelta(seconds=service.cache_ttl + 100)
        expired_entry = {"timestamp": expired_time.isoformat(), "data": "test"}
        assert not service._is_cache_valid(expired_entry)
        
        # 有效的缓存条目
        valid_time = datetime.now()
        valid_entry = {"timestamp": valid_time.isoformat(), "data": "test"}
        assert service._is_cache_valid(valid_entry)
    
    def test_get_default_teaching_strategies(self):
        """测试获取默认教学策略"""
        service = TeachingPracticesService()
        query = TeachingPracticeQuery(subject=SubjectType.MATH)
        
        strategies = service._get_default_teaching_strategies(query)
        
        assert len(strategies) > 0
        assert all(isinstance(s, TeachingStrategy) for s in strategies)
        assert all(s.name and s.description for s in strategies)
    
    def test_get_default_classroom_activities(self):
        """测试获取默认课堂活动"""
        service = TeachingPracticesService()
        query = TeachingPracticeQuery(grade=GradeLevel.GRADE_3)
        
        activities = service._get_default_classroom_activities(query)
        
        assert len(activities) > 0
        assert all(isinstance(a, ClassroomActivity) for a in activities)
        assert all(a.name and a.description and a.duration for a in activities)
    
    def test_get_default_assessment_methods(self):
        """测试获取默认评估方法"""
        service = TeachingPracticesService()
        query = TeachingPracticeQuery()
        
        methods = service._get_default_assessment_methods(query)
        
        assert len(methods) > 0
        assert all(isinstance(m, AssessmentMethod) for m in methods)
        assert all(m.name and m.type and m.description for m in methods)
    
    def test_get_default_classroom_management(self):
        """测试获取默认课堂管理技巧"""
        service = TeachingPracticesService()
        query = TeachingPracticeQuery()
        
        management_tips = service._get_default_classroom_management(query)
        
        assert len(management_tips) > 0
        assert all(isinstance(m, ClassroomManagement) for m in management_tips)
        assert all(m.category and m.techniques for m in management_tips)
    
    @pytest.mark.asyncio
    async def test_get_teaching_practices_with_cache(self):
        """测试带缓存的教学实践获取"""
        service = TeachingPracticesService()
        query = TeachingPracticeQuery(subject=SubjectType.MATH, limit=2)
        
        # 第一次调用
        response1 = await service.get_teaching_practices(query)
        
        assert response1 is not None
        assert len(response1.teaching_strategies) <= 2
        
        # 检查缓存
        cache_key = service._generate_cache_key(query)
        assert cache_key in service.cache
        
        # 第二次调用（应该使用缓存）
        response2 = await service.get_teaching_practices(query)
        
        # 结果应该一致
        assert len(response1.teaching_strategies) == len(response2.teaching_strategies)
        assert response1.query_info == response2.query_info
    
    @pytest.mark.asyncio
    async def test_get_teaching_practices_fallback(self):
        """测试教学实践获取降级方案"""
        service = TeachingPracticesService()
        
        # 模拟Context7服务不可用
        service.context7_client.api_key = "invalid_key"
        
        query = TeachingPracticeQuery(subject=SubjectType.ENGLISH, limit=3)
        
        # 应该能够获取默认响应
        response = await service.get_teaching_practices(query)
        
        assert response is not None
        assert len(response.teaching_strategies) > 0
        assert len(response.classroom_activities) > 0
        assert len(response.assessment_methods) > 0
        assert len(response.classroom_management) > 0
    
    def test_clear_cache(self):
        """测试清除缓存"""
        service = TeachingPracticesService()
        
        # 添加一些缓存数据
        service.cache["test_key"] = {"data": "test_data"}
        assert len(service.cache) > 0
        
        # 清除缓存
        service.clear_cache()
        assert len(service.cache) == 0
    
    def test_get_cache_stats(self):
        """测试获取缓存统计"""
        service = TeachingPracticesService()
        
        # 添加有效和过期的缓存条目
        from datetime import datetime, timedelta
        
        valid_time = datetime.now()
        expired_time = datetime.now() - timedelta(seconds=service.cache_ttl + 100)
        
        service.cache["valid_key"] = {
            "timestamp": valid_time.isoformat(),
            "data": "valid_data"
        }
        service.cache["expired_key"] = {
            "timestamp": expired_time.isoformat(),
            "data": "expired_data"
        }
        
        stats = service.get_cache_stats()
        
        assert stats["total_entries"] == 2
        assert stats["valid_entries"] == 1
        assert stats["expired_entries"] == 1
        assert stats["cache_ttl"] == service.cache_ttl


class TestModels:
    """测试数据模型"""
    
    def test_teaching_strategy_model(self):
        """测试教学策略模型"""
        strategy = TeachingStrategy(
            name="测试策略",
            description="测试描述",
            subject_areas=["数学"],
            grade_levels=["五年级"],
            objectives=["提高理解"],
            implementation_steps=["步骤1", "步骤2"],
            benefits=["优势1", "优势2"],
            considerations=["注意事项1"],
            resources_needed=["资源1"],
            assessment_methods=["评估1"]
        )
        
        assert strategy.name == "测试策略"
        assert strategy.description == "测试描述"
        assert len(strategy.subject_areas) == 1
        assert len(strategy.implementation_steps) == 2
    
    def test_classroom_activity_model(self):
        """测试课堂活动模型"""
        activity = ClassroomActivity(
            name="测试活动",
            description="测试描述",
            duration="20分钟",
            materials=["材料1", "材料2"],
            instructions=["指导1", "指导2"],
            learning_outcomes=["成果1"],
            differentiation_tips=["建议1"],
            extension_activities=["拓展1"]
        )
        
        assert activity.name == "测试活动"
        assert activity.duration == "20分钟"
        assert len(activity.materials) == 2
        assert len(activity.instructions) == 2
    
    def test_assessment_method_model(self):
        """测试评估方法模型"""
        method = AssessmentMethod(
            name="测试评估",
            type="形成性评估",
            description="测试描述",
            when_to_use="课堂中",
            implementation=["实施1", "实施2"],
            rubric_criteria=["标准1"],
            data_collection=["收集1"],
            feedback_strategies=["反馈1"]
        )
        
        assert method.name == "测试评估"
        assert method.type == "形成性评估"
        assert method.when_to_use == "课堂中"
        assert len(method.implementation) == 2
    
    def test_classroom_management_model(self):
        """测试课堂管理模型"""
        management = ClassroomManagement(
            category="纪律管理",
            techniques=["技巧1", "技巧2"],
            preventive_strategies=["预防1"],
            intervention_methods=["干预1"],
            positive_reinforcement=["激励1"],
            environment_setup=["环境1"]
        )
        
        assert management.category == "纪律管理"
        assert len(management.techniques) == 2
        assert len(management.preventive_strategies) == 1


class TestEnums:
    """测试枚举类型"""
    
    def test_subject_type_enum(self):
        """测试学科类型枚举"""
        assert SubjectType.CHINESE.value == "语文"
        assert SubjectType.MATH.value == "数学"
        assert SubjectType.ENGLISH.value == "英语"
        
        # 测试所有枚举值都有对应的中文名称
        for subject in SubjectType:
            assert isinstance(subject.value, str)
            assert len(subject.value) > 0
    
    def test_grade_level_enum(self):
        """测试年级水平枚举"""
        assert GradeLevel.GRADE_1.value == "一年级"
        assert GradeLevel.GRADE_12.value == "高三"
        assert GradeLevel.KINDERGARTEN.value == "幼儿园"
        
        # 测试所有枚举值
        for grade in GradeLevel:
            assert isinstance(grade.value, str)
            assert len(grade.value) > 0
    
    def test_teaching_objective_enum(self):
        """测试教学目标枚举"""
        assert TeachingObjective.KNOWLEDGE_TRANSFER.value == "知识传授"
        assert TeachingObjective.CRITICAL_THINKING.value == "批判性思维"
        
        for objective in TeachingObjective:
            assert isinstance(objective.value, str)
            assert len(objective.value) > 0
    
    def test_teaching_method_type_enum(self):
        """测试教学方法类型枚举"""
        assert TeachingMethodType.INTERACTIVE.value == "互动式教学"
        assert TeachingMethodType.PROJECT_BASED.value == "项目式学习"
        
        for method_type in TeachingMethodType:
            assert isinstance(method_type.value, str)
            assert len(method_type.value) > 0


# 便利函数测试
class TestConvenienceFunctions:
    """测试便利函数"""
    
    @pytest.mark.asyncio
    async def test_get_teaching_strategies_function(self):
        """测试获取教学策略便利函数"""
        from teaching_practices import get_teaching_strategies
        
        strategies = await get_teaching_strategies(
            subject="数学",
            grade="五年级",
            limit=3
        )
        
        assert isinstance(strategies, list)
        assert len(strategies) <= 3
        assert all(isinstance(s, TeachingStrategy) for s in strategies)
    
    @pytest.mark.asyncio
    async def test_get_classroom_activities_function(self):
        """测试获取课堂活动便利函数"""
        from teaching_practices import get_classroom_activities
        
        activities = await get_classroom_activities(
            subject="英语",
            grade="八年级",
            limit=2
        )
        
        assert isinstance(activities, list)
        assert len(activities) <= 2
        assert all(isinstance(a, ClassroomActivity) for a in activities)
    
    @pytest.mark.asyncio
    async def test_get_assessment_methods_function(self):
        """测试获取评估方法便利函数"""
        from teaching_practices import get_assessment_methods
        
        methods = await get_assessment_methods(
            subject="科学",
            limit=2
        )
        
        assert isinstance(methods, list)
        assert len(methods) <= 2
        assert all(isinstance(m, AssessmentMethod) for m in methods)


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])