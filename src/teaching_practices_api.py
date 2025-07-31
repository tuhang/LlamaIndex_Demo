"""
教学实践方法API接口
提供RESTful API来访问教学实践方法服务
"""
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional, List, Dict, Any
import asyncio
from datetime import datetime
import logging

from teaching_practices import (
    TeachingPracticesService,
    TeachingPracticeQuery,
    TeachingPracticeResponse,
    SubjectType,
    GradeLevel,
    TeachingObjective,
    TeachingMethodType,
    teaching_practices_service
)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="教学实践方法API",
    description="基于Context7 MCP服务的教学实践方法获取API",
    version="1.0.0"
)


@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "教学实践方法API服务",
        "version": "1.0.0",
        "description": "集成Context7 MCP服务的教学实践方法获取系统",
        "endpoints": [
            "/teaching-practices",
            "/teaching-strategies", 
            "/classroom-activities",
            "/assessment-methods",
            "/cache-stats",
            "/health"
        ]
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 测试服务是否正常
        test_query = TeachingPracticeQuery(limit=1)
        response = await teaching_practices_service.get_teaching_practices(test_query)
        
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "service": "teaching_practices_api",
            "context7_available": bool(teaching_practices_service.context7_client.api_key)
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "timestamp": datetime.now(),
                "error": str(e)
            }
        )


@app.get("/teaching-practices", response_model=TeachingPracticeResponse)
async def get_teaching_practices(
    subject: Optional[str] = Query(None, description="学科类型"),
    grade: Optional[str] = Query(None, description="年级水平"),
    objective: Optional[str] = Query(None, description="教学目标"),
    method_type: Optional[str] = Query(None, description="教学方法类型"),
    keywords: Optional[str] = Query(None, description="关键词，用逗号分隔"),
    limit: int = Query(10, ge=1, le=50, description="返回结果数量限制")
):
    """
    获取综合教学实践方法
    
    Args:
        subject: 学科类型 (语文, 数学, 英语, 物理, 化学, 生物, 历史, 地理, 政治等)
        grade: 年级水平 (一年级-高三, 幼儿园, 大学)
        objective: 教学目标 (知识传授, 技能培养, 批判性思维, 创造力培养等)
        method_type: 教学方法类型 (互动式教学, 探究式学习, 项目式学习等)
        keywords: 关键词列表，用逗号分隔
        limit: 返回结果数量限制 (1-50)
    
    Returns:
        TeachingPracticeResponse: 包含教学策略、课堂活动、评估方法、管理技巧的综合响应
    """
    try:
        # 构建查询参数
        query_keywords = None
        if keywords:
            query_keywords = [k.strip() for k in keywords.split(',') if k.strip()]
        
        # 验证枚举值
        subject_enum = None
        if subject:
            try:
                subject_enum = SubjectType(subject)
            except ValueError:
                raise HTTPException(
                    status_code=400, 
                    detail=f"无效的学科类型: {subject}. 支持的类型: {[s.value for s in SubjectType]}"
                )
        
        grade_enum = None
        if grade:
            try:
                grade_enum = GradeLevel(grade)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的年级水平: {grade}. 支持的类型: {[g.value for g in GradeLevel]}"
                )
        
        objective_enum = None
        if objective:
            try:
                objective_enum = TeachingObjective(objective)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的教学目标: {objective}. 支持的类型: {[o.value for o in TeachingObjective]}"
                )
        
        method_type_enum = None
        if method_type:
            try:
                method_type_enum = TeachingMethodType(method_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的教学方法类型: {method_type}. 支持的类型: {[m.value for m in TeachingMethodType]}"
                )
        
        # 创建查询对象
        query = TeachingPracticeQuery(
            subject=subject_enum,
            grade=grade_enum,
            objective=objective_enum,
            method_type=method_type_enum,
            keywords=query_keywords,
            limit=limit
        )
        
        # 执行查询
        response = await teaching_practices_service.get_teaching_practices(query)
        
        logger.info(f"成功处理教学实践查询: {query}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取教学实践方法失败: {e}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@app.get("/teaching-strategies")
async def get_teaching_strategies_only(
    subject: Optional[str] = Query(None, description="学科类型"),
    grade: Optional[str] = Query(None, description="年级水平"),
    objective: Optional[str] = Query(None, description="教学目标"),
    method_type: Optional[str] = Query(None, description="教学方法类型"),
    keywords: Optional[str] = Query(None, description="关键词，用逗号分隔"),
    limit: int = Query(10, ge=1, le=50, description="返回结果数量限制")
):
    """
    仅获取教学策略
    
    返回教学策略列表，不包含其他类型的教学实践内容
    """
    try:
        # 获取完整响应
        full_response = await get_teaching_practices(
            subject=subject,
            grade=grade,
            objective=objective,
            method_type=method_type,
            keywords=keywords,
            limit=limit
        )
        
        return {
            "teaching_strategies": full_response.teaching_strategies,
            "query_info": full_response.query_info,
            "timestamp": full_response.timestamp
        }
        
    except Exception as e:
        logger.error(f"获取教学策略失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取教学策略失败: {str(e)}")


@app.get("/classroom-activities")
async def get_classroom_activities_only(
    subject: Optional[str] = Query(None, description="学科类型"),
    grade: Optional[str] = Query(None, description="年级水平"),
    duration: Optional[str] = Query(None, description="活动时长"),
    keywords: Optional[str] = Query(None, description="关键词，用逗号分隔"),
    limit: int = Query(10, ge=1, le=50, description="返回结果数量限制")
):
    """
    仅获取课堂活动
    
    返回课堂活动列表，针对特定学科和年级进行优化
    """
    try:
        # 获取完整响应
        full_response = await get_teaching_practices(
            subject=subject,
            grade=grade,
            keywords=keywords,
            limit=limit
        )
        
        # 过滤活动（如果指定了时长）
        activities = full_response.classroom_activities
        if duration:
            # 简单的时长过滤逻辑
            filtered_activities = []
            for activity in activities:
                if duration.lower() in activity.duration.lower():
                    filtered_activities.append(activity)
            activities = filtered_activities
        
        return {
            "classroom_activities": activities,
            "query_info": full_response.query_info,
            "timestamp": full_response.timestamp
        }
        
    except Exception as e:
        logger.error(f"获取课堂活动失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取课堂活动失败: {str(e)}")


@app.get("/assessment-methods")
async def get_assessment_methods_only(
    subject: Optional[str] = Query(None, description="学科类型"),
    assessment_type: Optional[str] = Query(None, description="评估类型"),
    keywords: Optional[str] = Query(None, description="关键词，用逗号分隔"),
    limit: int = Query(10, ge=1, le=50, description="返回结果数量限制")
):
    """
    仅获取评估方法
    
    返回评估方法列表，可根据评估类型进行筛选
    """
    try:
        # 获取完整响应
        full_response = await get_teaching_practices(
            subject=subject,
            keywords=keywords,
            limit=limit
        )
        
        # 过滤评估方法（如果指定了类型）
        methods = full_response.assessment_methods
        if assessment_type:
            filtered_methods = []
            for method in methods:
                if assessment_type.lower() in method.type.lower():
                    filtered_methods.append(method)
            methods = filtered_methods
        
        return {
            "assessment_methods": methods,
            "query_info": full_response.query_info,
            "timestamp": full_response.timestamp
        }
        
    except Exception as e:
        logger.error(f"获取评估方法失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取评估方法失败: {str(e)}")


@app.get("/classroom-management")
async def get_classroom_management_only(
    category: Optional[str] = Query(None, description="管理类别"),
    keywords: Optional[str] = Query(None, description="关键词，用逗号分隔"),
    limit: int = Query(5, ge=1, le=20, description="返回结果数量限制")
):
    """
    仅获取课堂管理技巧
    
    返回课堂管理技巧列表，可根据管理类别进行筛选
    """
    try:
        # 获取完整响应
        full_response = await get_teaching_practices(
            keywords=keywords,
            limit=limit
        )
        
        # 过滤管理技巧（如果指定了类别）
        management_tips = full_response.classroom_management
        if category:
            filtered_tips = []
            for tip in management_tips:
                if category.lower() in tip.category.lower():
                    filtered_tips.append(tip)
            management_tips = filtered_tips
        
        return {
            "classroom_management": management_tips,
            "query_info": full_response.query_info,
            "timestamp": full_response.timestamp
        }
        
    except Exception as e:
        logger.error(f"获取课堂管理技巧失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取课堂管理技巧失败: {str(e)}")


@app.get("/enums")
async def get_available_enums():
    """
    获取所有可用的枚举值
    
    返回系统支持的所有枚举类型和值，用于前端展示选项
    """
    return {
        "subjects": [s.value for s in SubjectType],
        "grades": [g.value for g in GradeLevel],
        "objectives": [o.value for o in TeachingObjective],
        "method_types": [m.value for m in TeachingMethodType]
    }


@app.get("/cache-stats")
async def get_cache_stats():
    """
    获取缓存统计信息
    
    返回当前缓存状态，用于监控和调试
    """
    try:
        stats = teaching_practices_service.get_cache_stats()
        return {
            "cache_stats": stats,
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"获取缓存统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取缓存统计失败: {str(e)}")


@app.delete("/cache")
async def clear_cache(background_tasks: BackgroundTasks):
    """
    清除缓存
    
    清除所有已缓存的教学实践数据，强制重新获取
    """
    try:
        background_tasks.add_task(teaching_practices_service.clear_cache)
        return {
            "message": "缓存清除任务已启动",
            "timestamp": datetime.now()
        }
    except Exception as e:
        logger.error(f"清除缓存失败: {e}")
        raise HTTPException(status_code=500, detail=f"清除缓存失败: {str(e)}")


@app.post("/batch-query")
async def batch_query(
    queries: List[Dict[str, Any]]
):
    """
    批量查询教学实践方法
    
    Args:
        queries: 查询参数列表
        
    Returns:
        批量查询结果
    """
    try:
        results = []
        
        for i, query_data in enumerate(queries):
            try:
                # 构建查询参数
                keywords = None
                if 'keywords' in query_data and query_data['keywords']:
                    if isinstance(query_data['keywords'], str):
                        keywords = [k.strip() for k in query_data['keywords'].split(',')]
                    else:
                        keywords = query_data['keywords']
                
                # 转换枚举值
                subject_enum = SubjectType(query_data['subject']) if query_data.get('subject') else None
                grade_enum = GradeLevel(query_data['grade']) if query_data.get('grade') else None
                objective_enum = TeachingObjective(query_data['objective']) if query_data.get('objective') else None
                method_type_enum = TeachingMethodType(query_data['method_type']) if query_data.get('method_type') else None
                
                query = TeachingPracticeQuery(
                    subject=subject_enum,
                    grade=grade_enum,
                    objective=objective_enum,
                    method_type=method_type_enum,
                    keywords=keywords,
                    limit=query_data.get('limit', 10)
                )
                
                response = await teaching_practices_service.get_teaching_practices(query)
                results.append({
                    "query_index": i,
                    "success": True,
                    "response": response
                })
                
            except Exception as e:
                results.append({
                    "query_index": i,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "batch_results": results,
            "total_queries": len(queries),
            "successful_queries": sum(1 for r in results if r["success"]),
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        logger.error(f"批量查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量查询失败: {str(e)}")


# 错误处理器
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "服务器内部错误",
            "detail": str(exc),
            "timestamp": datetime.now().isoformat()
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    # 启动API服务
    uvicorn.run(
        "teaching_practices_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )