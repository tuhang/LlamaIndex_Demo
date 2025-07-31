"""
LangChain与LlamaIndex混合RAG系统
结合两个框架的优势，提供更强大的检索增强生成能力
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass
import numpy as np

# LlamaIndex imports
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.core.response.pprint_utils import pprint_response

# LangChain imports
from langchain.schema import Document
from langchain.chains import RetrievalQA
from langchain.retrievers import EnsembleRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.retrievers import ContextualCompressionRetriever
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from config import settings
from src.knowledge_base import knowledge_base
from src.langchain_document_processor import langchain_processor
from src.memory_manager import memory_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class HybridQuery:
    """混合查询请求"""
    query: str
    user_id: Optional[str] = None
    subject: Optional[str] = None
    grade: Optional[str] = None
    top_k: int = 5
    use_memory: bool = True
    fusion_method: str = "weighted"  # weighted, rank, similarity
    llamaindex_weight: float = 0.6
    langchain_weight: float = 0.4

class HybridRAGSystem:
    """混合RAG系统"""
    
    def __init__(self):
        """初始化混合RAG系统"""
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_api_base,
            model=settings.embedding_model
        )
        
        self.llm = ChatOpenAI(
            openai_api_key=settings.openai_api_key,
            openai_api_base=settings.openai_api_base,
            model_name=settings.llm_model,
            temperature=0.7
        )
        
        # 初始化组件
        self.llamaindex_engine = None
        self.langchain_retriever = None
        self.ensemble_retriever = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """初始化系统组件"""
        try:
            # 初始化LlamaIndex组件
            self._initialize_llamaindex()
            
            # 初始化LangChain组件
            self._initialize_langchain()
            
            # 创建集成检索器
            self._create_ensemble_retriever()
            
            logger.info("混合RAG系统初始化完成")
            
        except Exception as e:
            logger.error(f"混合RAG系统初始化失败: {e}")
    
    def _initialize_llamaindex(self):
        """初始化LlamaIndex组件"""
        try:
            # 尝试加载现有的LlamaIndex
            if hasattr(knowledge_base, 'index') and knowledge_base.index:
                # 创建检索器
                retriever = VectorIndexRetriever(
                    index=knowledge_base.index,
                    similarity_top_k=settings.similarity_top_k
                )
                
                # 添加后处理器
                postprocessor = SimilarityPostprocessor(similarity_cutoff=0.7)
                
                # 创建查询引擎
                self.llamaindex_engine = RetrieverQueryEngine(
                    retriever=retriever,
                    node_postprocessors=[postprocessor]
                )
                
                logger.info("LlamaIndex组件初始化成功")
            else:
                logger.warning("LlamaIndex索引不可用")
                
        except Exception as e:
            logger.error(f"LlamaIndex组件初始化失败: {e}")
    
    def _initialize_langchain(self):
        """初始化LangChain组件"""
        try:
            # 使用LangChain的向量存储作为检索器
            if langchain_processor.vectorstore:
                # 基础检索器
                base_retriever = langchain_processor.vectorstore.as_retriever(
                    search_kwargs={"k": settings.similarity_top_k}
                )
                
                # 添加压缩器以提高检索质量
                compressor = LLMChainExtractor.from_llm(self.llm)
                self.langchain_retriever = ContextualCompressionRetriever(
                    base_compressor=compressor,
                    base_retriever=base_retriever
                )
                
                logger.info("LangChain组件初始化成功")
            else:
                logger.warning("LangChain向量存储不可用")
                
        except Exception as e:
            logger.error(f"LangChain组件初始化失败: {e}")
    
    def _create_ensemble_retriever(self):
        """创建集成检索器"""
        try:
            retrievers = []
            weights = []
            
            # 添加可用的检索器
            if self.langchain_retriever:
                retrievers.append(self.langchain_retriever)
                weights.append(0.6)  # LangChain权重
            
            # 注意：LlamaIndex的检索器需要适配LangChain的接口
            # 这里我们创建一个适配器
            if self.llamaindex_engine:
                llamaindex_adapter = self._create_llamaindex_adapter()
                if llamaindex_adapter:
                    retrievers.append(llamaindex_adapter)
                    weights.append(0.4)  # LlamaIndex权重
            
            # 创建集成检索器
            if len(retrievers) > 1:
                self.ensemble_retriever = EnsembleRetriever(
                    retrievers=retrievers,
                    weights=weights
                )
                logger.info("集成检索器创建成功")
            elif len(retrievers) == 1:
                self.ensemble_retriever = retrievers[0]
                logger.info("使用单一检索器")
            else:
                logger.warning("没有可用的检索器")
                
        except Exception as e:
            logger.error(f"创建集成检索器失败: {e}")
    
    def _create_llamaindex_adapter(self):
        """创建LlamaIndex到LangChain的适配器"""
        try:
            class LlamaIndexAdapter:
                def __init__(self, query_engine):
                    self.query_engine = query_engine
                
                def get_relevant_documents(self, query: str) -> List[Document]:
                    """适配LangChain的接口"""
                    try:
                        # 使用LlamaIndex查询
                        response = self.query_engine.query(query)
                        
                        # 转换为LangChain Document格式
                        documents = []
                        if hasattr(response, 'source_nodes'):
                            for node in response.source_nodes:
                                doc = Document(
                                    page_content=node.text,
                                    metadata=node.metadata or {}
                                )
                                documents.append(doc)
                        
                        return documents
                    except Exception as e:
                        logger.error(f"LlamaIndex适配器查询失败: {e}")
                        return []
                
                async def aget_relevant_documents(self, query: str) -> List[Document]:
                    """异步接口"""
                    return self.get_relevant_documents(query)
            
            return LlamaIndexAdapter(self.llamaindex_engine)
            
        except Exception as e:
            logger.error(f"创建LlamaIndex适配器失败: {e}")
            return None
    
    async def hybrid_retrieve(self, query: HybridQuery) -> Dict[str, Any]:
        """
        混合检索
        
        Args:
            query: 混合查询请求
            
        Returns:
            检索结果
        """
        try:
            results = {
                'query': query.query,
                'timestamp': datetime.now().isoformat(),
                'llamaindex_results': [],
                'langchain_results': [],
                'fused_results': [],
                'metadata': {}
            }
            
            # 并行执行两个检索系统
            tasks = []
            
            # LlamaIndex检索
            if self.llamaindex_engine:
                tasks.append(self._llamaindex_retrieve(query))
            
            # LangChain检索
            if self.langchain_retriever:
                tasks.append(self._langchain_retrieve(query))
            
            if tasks:
                retrieve_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 处理结果
                for i, result in enumerate(retrieve_results):
                    if isinstance(result, Exception):
                        logger.error(f"检索任务 {i} 失败: {result}")
                        continue
                    
                    if i == 0 and self.llamaindex_engine:  # LlamaIndex结果
                        results['llamaindex_results'] = result
                    elif (i == 1 and self.langchain_retriever) or (i == 0 and not self.llamaindex_engine):  # LangChain结果
                        results['langchain_results'] = result
            
            # 融合结果
            results['fused_results'] = self._fuse_results(
                results['llamaindex_results'],
                results['langchain_results'],
                query
            )
            
            # 添加记忆信息（如果启用）
            if query.use_memory and query.user_id:
                memory_info = self._get_memory_context(query)
                results['memory_context'] = memory_info
            
            logger.info(f"混合检索完成，返回 {len(results['fused_results'])} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"混合检索失败: {e}")
            return {
                'query': query.query,
                'error': str(e),
                'fused_results': []
            }
    
    async def _llamaindex_retrieve(self, query: HybridQuery) -> List[Dict[str, Any]]:
        """LlamaIndex检索"""
        try:
            # 在线程池中运行同步操作
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.llamaindex_engine.query(query.query)
            )
            
            results = []
            if hasattr(response, 'source_nodes'):
                for node in response.source_nodes:
                    results.append({
                        'content': node.text,
                        'metadata': node.metadata or {},
                        'score': getattr(node, 'score', 0.0),
                        'source': 'llamaindex'
                    })
            
            return results[:query.top_k]
            
        except Exception as e:
            logger.error(f"LlamaIndex检索失败: {e}")
            return []
    
    async def _langchain_retrieve(self, query: HybridQuery) -> List[Dict[str, Any]]:
        """LangChain检索"""
        try:
            # 使用异步接口
            if hasattr(self.langchain_retriever, 'aget_relevant_documents'):
                documents = await self.langchain_retriever.aget_relevant_documents(query.query)
            else:
                # 在线程池中运行同步操作
                loop = asyncio.get_event_loop()
                documents = await loop.run_in_executor(
                    None,
                    lambda: self.langchain_retriever.get_relevant_documents(query.query)
                )
            
            results = []
            for doc in documents[:query.top_k]:
                results.append({
                    'content': doc.page_content,
                    'metadata': doc.metadata,
                    'score': doc.metadata.get('score', 0.0),
                    'source': 'langchain'
                })
            
            return results
            
        except Exception as e:
            logger.error(f"LangChain检索失败: {e}")
            return []
    
    def _fuse_results(self, llamaindex_results: List[Dict[str, Any]], 
                     langchain_results: List[Dict[str, Any]], 
                     query: HybridQuery) -> List[Dict[str, Any]]:
        """融合检索结果"""
        try:
            if query.fusion_method == "weighted":
                return self._weighted_fusion(
                    llamaindex_results, langchain_results, 
                    query.llamaindex_weight, query.langchain_weight
                )
            elif query.fusion_method == "rank":
                return self._rank_fusion(llamaindex_results, langchain_results)
            elif query.fusion_method == "similarity":
                return self._similarity_fusion(llamaindex_results, langchain_results)
            else:
                # 默认简单合并
                return self._simple_merge(llamaindex_results, langchain_results, query.top_k)
                
        except Exception as e:
            logger.error(f"结果融合失败: {e}")
            return self._simple_merge(llamaindex_results, langchain_results, query.top_k)
    
    def _weighted_fusion(self, llamaindex_results: List[Dict[str, Any]], 
                        langchain_results: List[Dict[str, Any]], 
                        ll_weight: float, lc_weight: float) -> List[Dict[str, Any]]:
        """加权融合"""
        all_results = []
        
        # 为LlamaIndex结果加权
        for result in llamaindex_results:
            result = result.copy()
            result['weighted_score'] = result.get('score', 0.5) * ll_weight
            all_results.append(result)
        
        # 为LangChain结果加权
        for result in langchain_results:
            result = result.copy()
            result['weighted_score'] = result.get('score', 0.5) * lc_weight
            all_results.append(result)
        
        # 按加权分数排序
        all_results.sort(key=lambda x: x.get('weighted_score', 0), reverse=True)
        
        # 去重（基于内容相似度）
        deduplicated = self._deduplicate_results(all_results)
        
        return deduplicated
    
    def _rank_fusion(self, llamaindex_results: List[Dict[str, Any]], 
                    langchain_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """排名融合（RRF - Reciprocal Rank Fusion）"""
        k = 60  # RRF参数
        score_dict = {}
        
        # 处理LlamaIndex结果
        for rank, result in enumerate(llamaindex_results, 1):
            content_hash = hash(result['content'][:100])  # 简单的内容哈希
            if content_hash not in score_dict:
                score_dict[content_hash] = {
                    'result': result,
                    'rrf_score': 0
                }
            score_dict[content_hash]['rrf_score'] += 1 / (k + rank)
        
        # 处理LangChain结果
        for rank, result in enumerate(langchain_results, 1):
            content_hash = hash(result['content'][:100])
            if content_hash not in score_dict:
                score_dict[content_hash] = {
                    'result': result,
                    'rrf_score': 0
                }
            score_dict[content_hash]['rrf_score'] += 1 / (k + rank)
        
        # 按RRF分数排序
        sorted_results = sorted(
            score_dict.values(),
            key=lambda x: x['rrf_score'],
            reverse=True
        )
        
        return [item['result'] for item in sorted_results]
    
    def _similarity_fusion(self, llamaindex_results: List[Dict[str, Any]], 
                          langchain_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """基于相似度的融合"""
        # 简化实现：合并结果并按原始分数排序
        all_results = llamaindex_results + langchain_results
        all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return self._deduplicate_results(all_results)
    
    def _simple_merge(self, llamaindex_results: List[Dict[str, Any]], 
                     langchain_results: List[Dict[str, Any]], 
                     top_k: int) -> List[Dict[str, Any]]:
        """简单合并"""
        all_results = llamaindex_results + langchain_results
        return all_results[:top_k]
    
    def _deduplicate_results(self, results: List[Dict[str, Any]], 
                           similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """去重结果"""
        if not results:
            return []
        
        deduplicated = [results[0]]
        
        for result in results[1:]:
            is_duplicate = False
            current_content = result['content'].lower()
            
            for existing in deduplicated:
                existing_content = existing['content'].lower()
                
                # 简单的相似度计算（基于公共词汇）
                current_words = set(current_content.split())
                existing_words = set(existing_content.split())
                
                if current_words and existing_words:
                    similarity = len(current_words & existing_words) / len(current_words | existing_words)
                    if similarity > similarity_threshold:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                deduplicated.append(result)
        
        return deduplicated
    
    def _get_memory_context(self, query: HybridQuery) -> Dict[str, Any]:
        """获取记忆上下文"""
        try:
            if not query.user_id:
                return {}
            
            # 获取相关的历史教案
            similar_plans = memory_manager.find_similar_lesson_plans(
                query.user_id, 
                {
                    'subject': query.subject,
                    'grade': query.grade,
                    'topic': query.query
                },
                limit=3
            )
            
            # 获取用户偏好
            preferences = memory_manager.get_user_preferences(query.user_id)
            
            # 获取教学建议
            recommendations = memory_manager.get_teaching_recommendations(
                query.user_id,
                {
                    'subject': query.subject,
                    'grade': query.grade
                }
            )
            
            return {
                'similar_plans': similar_plans,
                'user_preferences': preferences,
                'teaching_recommendations': recommendations
            }
            
        except Exception as e:
            logger.error(f"获取记忆上下文失败: {e}")
            return {}
    
    async def hybrid_qa(self, query: HybridQuery, include_sources: bool = True) -> Dict[str, Any]:
        """
        混合问答
        
        Args:
            query: 查询请求
            include_sources: 是否包含来源信息
            
        Returns:
            问答结果
        """
        try:
            # 首先进行混合检索
            retrieve_results = await self.hybrid_retrieve(query)
            
            # 构建上下文
            context_docs = []
            for result in retrieve_results['fused_results'][:query.top_k]:
                doc = Document(
                    page_content=result['content'],
                    metadata=result['metadata']
                )
                context_docs.append(doc)
            
            if not context_docs:
                return {
                    'query': query.query,
                    'answer': "抱歉，没有找到相关的教案资料来回答您的问题。",
                    'source_documents': [],
                    'timestamp': datetime.now().isoformat()
                }
            
            # 使用LLM生成答案
            context_text = "\n\n".join([doc.page_content for doc in context_docs])
            
            prompt = f"""
基于以下教案资料，请回答用户的问题：

教案资料：
{context_text}

用户问题：{query.query}

请提供详细、准确的答案，并确保答案与教育教学相关。如果资料中没有直接的答案，请基于教学经验给出建议。

答案：
"""
            
            # 在线程池中运行LLM
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.llm.invoke(prompt)
            )
            
            result = {
                'query': query.query,
                'answer': response.content,
                'timestamp': datetime.now().isoformat(),
                'retrieval_stats': {
                    'llamaindex_count': len(retrieve_results['llamaindex_results']),
                    'langchain_count': len(retrieve_results['langchain_results']),
                    'fused_count': len(retrieve_results['fused_results'])
                }
            }
            
            if include_sources:
                result['source_documents'] = context_docs
                result['retrieval_details'] = retrieve_results
            
            return result
            
        except Exception as e:
            logger.error(f"混合问答失败: {e}")
            return {
                'query': query.query,
                'error': str(e),
                'answer': "问答处理失败，请重试。",
                'timestamp': datetime.now().isoformat()
            }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            stats = {
                'llamaindex_available': self.llamaindex_engine is not None,
                'langchain_available': self.langchain_retriever is not None,
                'ensemble_available': self.ensemble_retriever is not None,
                'embedding_model': settings.embedding_model,
                'llm_model': settings.llm_model,
                'timestamp': datetime.now().isoformat()
            }
            
            # LlamaIndex统计
            if hasattr(knowledge_base, 'get_knowledge_base_stats'):
                stats['llamaindex_stats'] = knowledge_base.get_knowledge_base_stats()
            
            # LangChain统计
            if hasattr(langchain_processor, 'get_document_stats'):
                stats['langchain_stats'] = langchain_processor.get_document_stats()
            
            # 记忆统计
            if hasattr(memory_manager, 'get_memory_stats'):
                stats['memory_stats'] = memory_manager.get_memory_stats()
            
            return stats
            
        except Exception as e:
            logger.error(f"获取系统统计失败: {e}")
            return {'error': str(e)}

# 创建全局实例
hybrid_rag = HybridRAGSystem()

# 便利函数
async def hybrid_search(query: str, user_id: Optional[str] = None, 
                       subject: Optional[str] = None, grade: Optional[str] = None,
                       top_k: int = 5, fusion_method: str = "weighted") -> Dict[str, Any]:
    """便利函数：混合搜索"""
    hybrid_query = HybridQuery(
        query=query,
        user_id=user_id,
        subject=subject,
        grade=grade,
        top_k=top_k,
        fusion_method=fusion_method
    )
    
    return await hybrid_rag.hybrid_retrieve(hybrid_query)

async def hybrid_ask(question: str, user_id: Optional[str] = None,
                    subject: Optional[str] = None, grade: Optional[str] = None,
                    include_sources: bool = True) -> Dict[str, Any]:
    """便利函数：混合问答"""
    hybrid_query = HybridQuery(
        query=question,
        user_id=user_id,
        subject=subject,
        grade=grade
    )
    
    return await hybrid_rag.hybrid_qa(hybrid_query, include_sources)