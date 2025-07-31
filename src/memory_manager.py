"""
基于LangChain的记忆管理模块
提供对话历史、教案生成历史和个性化偏好管理
"""
import logging
import json
import pickle
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime, timedelta
import hashlib

# LangChain imports
from langchain.memory import (
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
    ConversationSummaryMemory,
    ConversationSummaryBufferMemory,
    ConversationEntityMemory
)
from langchain.memory.chat_message_histories import (
    ChatMessageHistory,
    FileChatMessageHistory
)
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EducationMemoryManager:
    """教育系统记忆管理器"""
    
    def __init__(self):
        """初始化记忆管理器"""
        self.memory_dir = Path(settings.student_data_dir) / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        
        # LLM for memory operations
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_api_base,
            model_name=settings.llm_model,
            temperature=0.3
        )
        
        # 不同类型的记忆存储
        self.conversation_memories = {}  # 对话记忆
        self.lesson_plan_history = {}    # 教案生成历史
        self.user_preferences = {}       # 用户偏好
        self.teaching_patterns = {}      # 教学模式记忆
        
        self._load_persistent_memories()
    
    def create_conversation_memory(self, user_id: str, 
                                 memory_type: str = "buffer_window",
                                 **kwargs) -> Union[ConversationBufferMemory, 
                                                  ConversationBufferWindowMemory,
                                                  ConversationSummaryMemory,
                                                  ConversationSummaryBufferMemory]:
        """
        创建对话记忆
        
        Args:
            user_id: 用户ID
            memory_type: 记忆类型
            **kwargs: 额外参数
            
        Returns:
            记忆实例
        """
        try:
            # 创建持久化聊天历史
            history_file = self.memory_dir / f"chat_history_{user_id}.json"
            chat_history = FileChatMessageHistory(str(history_file))
            
            # 根据类型创建不同的记忆
            if memory_type == "buffer":
                memory = ConversationBufferMemory(
                    chat_memory=chat_history,
                    return_messages=True,
                    **kwargs
                )
            elif memory_type == "buffer_window":
                memory = ConversationBufferWindowMemory(
                    chat_memory=chat_history,
                    k=kwargs.get('k', 10),  # 保留最近10轮对话
                    return_messages=True
                )
            elif memory_type == "summary":
                memory = ConversationSummaryMemory(
                    llm=self.llm,
                    chat_memory=chat_history,
                    return_messages=True,
                    **kwargs
                )
            elif memory_type == "summary_buffer":
                memory = ConversationSummaryBufferMemory(
                    llm=self.llm,
                    chat_memory=chat_history,
                    max_token_limit=kwargs.get('max_token_limit', 2000),
                    return_messages=True
                )
            elif memory_type == "entity":
                memory = ConversationEntityMemory(
                    llm=self.llm,
                    chat_memory=chat_history,
                    return_messages=True,
                    **kwargs
                )
            else:
                # 默认使用buffer_window
                memory = ConversationBufferWindowMemory(
                    chat_memory=chat_history,
                    k=10,
                    return_messages=True
                )
            
            self.conversation_memories[user_id] = memory
            logger.info(f"为用户 {user_id} 创建了 {memory_type} 类型的对话记忆")
            return memory
            
        except Exception as e:
            logger.error(f"创建对话记忆失败: {e}")
            # 返回简单的buffer记忆作为fallback
            return ConversationBufferMemory(return_messages=True)
    
    def get_conversation_memory(self, user_id: str) -> Optional[ConversationBufferMemory]:
        """获取用户的对话记忆"""
        if user_id not in self.conversation_memories:
            return self.create_conversation_memory(user_id)
        
        return self.conversation_memories[user_id]
    
    def add_lesson_plan_to_history(self, user_id: str, lesson_plan_data: Dict[str, Any]):
        """
        添加教案到历史记录
        
        Args:
            user_id: 用户ID
            lesson_plan_data: 教案数据
        """
        try:
            if user_id not in self.lesson_plan_history:
                self.lesson_plan_history[user_id] = []
            
            # 添加时间戳和唯一ID
            lesson_entry = {
                "id": self._generate_lesson_id(lesson_plan_data),
                "timestamp": datetime.now().isoformat(),
                "data": lesson_plan_data,
                "usage_count": 1,
                "rating": None,
                "feedback": None
            }
            
            self.lesson_plan_history[user_id].append(lesson_entry)
            
            # 保持历史记录在合理范围内（最多100个）
            if len(self.lesson_plan_history[user_id]) > 100:
                self.lesson_plan_history[user_id] = self.lesson_plan_history[user_id][-100:]
            
            # 持久化保存
            self._save_lesson_plan_history(user_id)
            
            logger.info(f"为用户 {user_id} 添加了教案历史记录")
            
        except Exception as e:
            logger.error(f"添加教案历史失败: {e}")
    
    def get_lesson_plan_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        获取教案历史记录
        
        Args:
            user_id: 用户ID
            limit: 返回数量限制
            
        Returns:
            教案历史列表
        """
        if user_id not in self.lesson_plan_history:
            return []
        
        # 按时间倒序返回
        history = sorted(
            self.lesson_plan_history[user_id],
            key=lambda x: x['timestamp'],
            reverse=True
        )
        
        return history[:limit]
    
    def find_similar_lesson_plans(self, user_id: str, current_request: Dict[str, Any], 
                                limit: int = 5) -> List[Dict[str, Any]]:
        """
        查找相似的历史教案
        
        Args:
            user_id: 用户ID
            current_request: 当前教案请求
            limit: 返回数量限制
            
        Returns:
            相似教案列表
        """
        if user_id not in self.lesson_plan_history:
            return []
        
        similar_plans = []
        current_subject = current_request.get('subject', '')
        current_grade = current_request.get('grade', '')
        current_topic = current_request.get('topic', '')
        
        for plan_entry in self.lesson_plan_history[user_id]:
            plan_data = plan_entry['data']
            
            # 计算相似度分数
            similarity_score = 0
            
            # 学科匹配
            if plan_data.get('subject') == current_subject:
                similarity_score += 0.4
            
            # 年级匹配
            if plan_data.get('grade') == current_grade:
                similarity_score += 0.3
            
            # 主题相似性（简单的关键词匹配）
            if current_topic and plan_data.get('topic'):
                topic_keywords = set(current_topic.split())
                plan_keywords = set(plan_data.get('topic', '').split())
                if topic_keywords & plan_keywords:
                    similarity_score += 0.3
            
            # 只返回有一定相似度的教案
            if similarity_score >= 0.3:
                plan_entry_with_score = plan_entry.copy()
                plan_entry_with_score['similarity_score'] = similarity_score
                similar_plans.append(plan_entry_with_score)
        
        # 按相似度排序
        similar_plans.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        return similar_plans[:limit]
    
    def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]):
        """
        更新用户偏好设置
        
        Args:
            user_id: 用户ID
            preferences: 偏好设置
        """
        try:
            if user_id not in self.user_preferences:
                self.user_preferences[user_id] = {}
            
            # 合并偏好设置
            self.user_preferences[user_id].update(preferences)
            self.user_preferences[user_id]['updated_at'] = datetime.now().isoformat()
            
            # 持久化保存
            self._save_user_preferences(user_id)
            
            logger.info(f"更新了用户 {user_id} 的偏好设置")
            
        except Exception as e:
            logger.error(f"更新用户偏好失败: {e}")
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """获取用户偏好设置"""
        return self.user_preferences.get(user_id, {})
    
    def learn_teaching_patterns(self, user_id: str, lesson_data: Dict[str, Any], 
                              feedback: Optional[Dict[str, Any]] = None):
        """
        学习教学模式
        
        Args:
            user_id: 用户ID
            lesson_data: 教案数据
            feedback: 用户反馈
        """
        try:
            if user_id not in self.teaching_patterns:
                self.teaching_patterns[user_id] = {
                    'preferred_methods': {},
                    'successful_patterns': [],
                    'subject_preferences': {},
                    'time_patterns': {}
                }
            
            patterns = self.teaching_patterns[user_id]
            
            # 学习偏好的教学方法
            teaching_methods = lesson_data.get('teaching_methods', [])
            for method in teaching_methods:
                if method not in patterns['preferred_methods']:
                    patterns['preferred_methods'][method] = 0
                patterns['preferred_methods'][method] += 1
            
            # 记录成功的模式（基于反馈）
            if feedback and feedback.get('rating', 0) >= 4:
                success_pattern = {
                    'subject': lesson_data.get('subject'),
                    'grade': lesson_data.get('grade'),
                    'methods': teaching_methods,
                    'duration': lesson_data.get('duration'),
                    'rating': feedback.get('rating'),
                    'timestamp': datetime.now().isoformat()
                }
                patterns['successful_patterns'].append(success_pattern)
                
                # 保持成功模式在合理数量内
                if len(patterns['successful_patterns']) > 50:
                    patterns['successful_patterns'] = patterns['successful_patterns'][-50:]
            
            # 学习学科偏好
            subject = lesson_data.get('subject')
            if subject:
                if subject not in patterns['subject_preferences']:
                    patterns['subject_preferences'][subject] = {'count': 0, 'avg_rating': 0}
                
                patterns['subject_preferences'][subject]['count'] += 1
                if feedback and 'rating' in feedback:
                    current_avg = patterns['subject_preferences'][subject]['avg_rating']
                    count = patterns['subject_preferences'][subject]['count']
                    new_avg = (current_avg * (count - 1) + feedback['rating']) / count
                    patterns['subject_preferences'][subject]['avg_rating'] = new_avg
            
            # 持久化保存
            self._save_teaching_patterns(user_id)
            
            logger.info(f"为用户 {user_id} 学习了教学模式")
            
        except Exception as e:
            logger.error(f"学习教学模式失败: {e}")
    
    def get_teaching_recommendations(self, user_id: str, 
                                   current_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于历史模式获取教学建议
        
        Args:
            user_id: 用户ID
            current_request: 当前请求
            
        Returns:
            教学建议
        """
        if user_id not in self.teaching_patterns:
            return {}
        
        patterns = self.teaching_patterns[user_id]
        recommendations = {}
        
        try:
            # 推荐教学方法
            preferred_methods = patterns.get('preferred_methods', {})
            if preferred_methods:
                sorted_methods = sorted(
                    preferred_methods.items(),
                    key=lambda x: x[1],
                    reverse=True
                )
                recommendations['preferred_teaching_methods'] = [
                    method for method, count in sorted_methods[:5]
                ]
            
            # 基于成功模式的建议
            successful_patterns = patterns.get('successful_patterns', [])
            subject = current_request.get('subject')
            grade = current_request.get('grade')
            
            relevant_patterns = [
                p for p in successful_patterns
                if p.get('subject') == subject and p.get('grade') == grade
            ]
            
            if relevant_patterns:
                # 获取最高评分的模式
                best_pattern = max(relevant_patterns, key=lambda x: x.get('rating', 0))
                recommendations['suggested_methods'] = best_pattern.get('methods', [])
                recommendations['suggested_duration'] = best_pattern.get('duration')
            
            # 学科特定建议
            subject_prefs = patterns.get('subject_preferences', {})
            if subject in subject_prefs:
                recommendations['subject_expertise'] = subject_prefs[subject]
            
            return recommendations
            
        except Exception as e:
            logger.error(f"获取教学建议失败: {e}")
            return {}
    
    def cleanup_old_memories(self, days_to_keep: int = 30):
        """
        清理旧的记忆数据
        
        Args:
            days_to_keep: 保留天数
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # 清理教案历史
            for user_id in self.lesson_plan_history:
                original_count = len(self.lesson_plan_history[user_id])
                self.lesson_plan_history[user_id] = [
                    entry for entry in self.lesson_plan_history[user_id]
                    if datetime.fromisoformat(entry['timestamp']) > cutoff_date
                ]
                cleaned_count = original_count - len(self.lesson_plan_history[user_id])
                if cleaned_count > 0:
                    logger.info(f"为用户 {user_id} 清理了 {cleaned_count} 条教案历史")
            
            # 清理对话历史文件
            for history_file in self.memory_dir.glob("chat_history_*.json"):
                try:
                    if history_file.stat().st_mtime < cutoff_date.timestamp():
                        history_file.unlink()
                        logger.info(f"删除了过期的对话历史文件: {history_file.name}")
                except Exception:
                    continue
            
            logger.info(f"记忆清理完成，保留了最近 {days_to_keep} 天的数据")
            
        except Exception as e:
            logger.error(f"清理记忆数据失败: {e}")
    
    def _generate_lesson_id(self, lesson_data: Dict[str, Any]) -> str:
        """生成教案唯一ID"""
        content = f"{lesson_data.get('subject', '')}{lesson_data.get('grade', '')}{lesson_data.get('topic', '')}{datetime.now().date()}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    def _load_persistent_memories(self):
        """加载持久化的记忆数据"""
        try:
            # 加载教案历史
            history_file = self.memory_dir / "lesson_plan_history.json"
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.lesson_plan_history = json.load(f)
            
            # 加载用户偏好
            prefs_file = self.memory_dir / "user_preferences.json"
            if prefs_file.exists():
                with open(prefs_file, 'r', encoding='utf-8') as f:
                    self.user_preferences = json.load(f)
            
            # 加载教学模式
            patterns_file = self.memory_dir / "teaching_patterns.json"
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    self.teaching_patterns = json.load(f)
            
            logger.info("持久化记忆数据加载完成")
            
        except Exception as e:
            logger.error(f"加载持久化记忆失败: {e}")
    
    def _save_lesson_plan_history(self, user_id: str):
        """保存教案历史"""
        try:
            history_file = self.memory_dir / "lesson_plan_history.json"
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(self.lesson_plan_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存教案历史失败: {e}")
    
    def _save_user_preferences(self, user_id: str):
        """保存用户偏好"""
        try:
            prefs_file = self.memory_dir / "user_preferences.json"
            with open(prefs_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_preferences, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存用户偏好失败: {e}")
    
    def _save_teaching_patterns(self, user_id: str):
        """保存教学模式"""
        try:
            patterns_file = self.memory_dir / "teaching_patterns.json"
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(self.teaching_patterns, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存教学模式失败: {e}")
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        try:
            stats = {
                "total_users": len(set(
                    list(self.conversation_memories.keys()) +
                    list(self.lesson_plan_history.keys()) +
                    list(self.user_preferences.keys()) +
                    list(self.teaching_patterns.keys())
                )),
                "conversation_memories": len(self.conversation_memories),
                "lesson_plan_histories": len(self.lesson_plan_history),
                "user_preferences": len(self.user_preferences),
                "teaching_patterns": len(self.teaching_patterns),
                "total_lesson_plans": sum(
                    len(history) for history in self.lesson_plan_history.values()
                ),
                "memory_dir": str(self.memory_dir)
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"获取记忆统计失败: {e}")
            return {}

# 创建全局实例
memory_manager = EducationMemoryManager()