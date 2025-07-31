"""
基于LangChain的文档处理模块
增强文档加载、分割和处理能力
"""
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import asyncio

# LangChain imports
from langchain.schema import Document
from langchain_community.document_loaders import (
    DirectoryLoader,
    TextLoader,
    PyPDFLoader,
    Docx2txtLoader,
    UnstructuredPDFLoader,
    UnstructuredWordDocumentLoader
)
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    TokenTextSplitter
)
from langchain_community.vectorstores import Chroma, FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

from config import settings

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LangChainDocumentProcessor:
    """基于LangChain的文档处理器"""
    
    def __init__(self):
        """初始化文档处理器"""
        self.knowledge_base_dir = Path(settings.knowledge_base_dir)
        self.chroma_persist_dir = Path(settings.chroma_persist_dir)
        
        # 初始化OpenAI组件
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
        
        # 文档分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        # 向量存储
        self.vectorstore = None
        
    def load_documents_from_directory(self, directory: Optional[Path] = None) -> List[Document]:
        """
        从目录加载文档
        
        Args:
            directory: 文档目录路径，默认使用知识库目录
            
        Returns:
            加载的文档列表
        """
        if directory is None:
            directory = self.knowledge_base_dir
        
        documents = []
        
        try:
            # 定义文件类型和对应的加载器
            loaders_config = {
                "**/*.txt": (TextLoader, {"encoding": "utf-8"}),
                "**/*.pdf": (UnstructuredPDFLoader, {}),
                "**/*.docx": (UnstructuredWordDocumentLoader, {}),
                "**/*.doc": (UnstructuredWordDocumentLoader, {})
            }
            
            for pattern, (loader_class, loader_kwargs) in loaders_config.items():
                try:
                    # 使用DirectoryLoader批量加载
                    directory_loader = DirectoryLoader(
                        str(directory),
                        glob=pattern,
                        loader_cls=loader_class,
                        loader_kwargs=loader_kwargs,
                        show_progress=True
                    )
                    
                    docs = directory_loader.load()
                    
                    # 添加元数据
                    for doc in docs:
                        self._enhance_document_metadata(doc)
                    
                    documents.extend(docs)
                    logger.info(f"加载了 {len(docs)} 个 {pattern} 格式的文档")
                    
                except Exception as e:
                    logger.error(f"加载 {pattern} 格式文档失败: {e}")
                    continue
            
            logger.info(f"总共加载了 {len(documents)} 个文档")
            return documents
            
        except Exception as e:
            logger.error(f"从目录加载文档失败: {e}")
            return []
    
    def load_single_document(self, file_path: Union[str, Path]) -> Optional[Document]:
        """
        加载单个文档
        
        Args:
            file_path: 文档文件路径
            
        Returns:
            加载的文档对象
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"文件不存在: {file_path}")
            return None
        
        try:
            # 根据文件扩展名选择加载器
            loader = self._get_loader_for_file(file_path)
            if loader is None:
                return None
            
            documents = loader.load()
            if documents:
                doc = documents[0]
                self._enhance_document_metadata(doc)
                logger.info(f"成功加载文档: {file_path.name}")
                return doc
            
        except Exception as e:
            logger.error(f"加载文档失败 {file_path}: {e}")
        
        return None
    
    def _get_loader_for_file(self, file_path: Path):
        """根据文件类型获取对应的加载器"""
        extension = file_path.suffix.lower()
        
        loaders = {
            '.txt': lambda: TextLoader(str(file_path), encoding='utf-8'),
            '.pdf': lambda: UnstructuredPDFLoader(str(file_path)),
            '.docx': lambda: UnstructuredWordDocumentLoader(str(file_path)),
            '.doc': lambda: UnstructuredWordDocumentLoader(str(file_path))
        }
        
        if extension in loaders:
            try:
                return loaders[extension]()
            except Exception as e:
                logger.error(f"创建加载器失败 {extension}: {e}")
        else:
            logger.warning(f"不支持的文件类型: {extension}")
        
        return None
    
    def _enhance_document_metadata(self, document: Document):
        """增强文档元数据"""
        if 'source' in document.metadata:
            file_path = Path(document.metadata['source'])
            
            # 基础元数据
            document.metadata.update({
                'file_name': file_path.name,
                'file_extension': file_path.suffix,
                'file_size': file_path.stat().st_size if file_path.exists() else 0,
            })
            
            # 从文件名推断学科和年级
            filename = file_path.stem
            document.metadata.update({
                'subject': self._extract_subject_from_filename(filename),
                'grade': self._extract_grade_from_filename(filename),
                'topic': self._extract_topic_from_filename(filename)
            })
    
    def _extract_subject_from_filename(self, filename: str) -> str:
        """从文件名提取学科"""
        subjects = {
            '语文': ['语文', '中文', '汉语'],
            '数学': ['数学', '算术'],
            '英语': ['英语', '英文', 'English'],
            '物理': ['物理'],
            '化学': ['化学'],
            '生物': ['生物'],
            '历史': ['历史'],
            '地理': ['地理'],
            '政治': ['政治', '思想品德'],
            '音乐': ['音乐'],
            '美术': ['美术', '绘画'],
            '体育': ['体育', '运动'],
        }
        
        filename_lower = filename.lower()
        for subject, keywords in subjects.items():
            if any(keyword.lower() in filename_lower for keyword in keywords):
                return subject
        
        return "通用"
    
    def _extract_grade_from_filename(self, filename: str) -> str:
        """从文件名提取年级"""
        grades = [
            '一年级', '二年级', '三年级', '四年级', '五年级', '六年级',
            '七年级', '八年级', '九年级', '初一', '初二', '初三',
            '高一', '高二', '高三', '高中'
        ]
        
        for grade in grades:
            if grade in filename:
                return grade
        
        return "未知年级"
    
    def _extract_topic_from_filename(self, filename: str) -> str:
        """从文件名提取主题"""
        # 移除学科和年级信息后的剩余部分作为主题
        subject = self._extract_subject_from_filename(filename)
        grade = self._extract_grade_from_filename(filename)
        
        topic = filename
        for remove_item in [subject, grade]:
            if remove_item != "通用" and remove_item != "未知年级":
                topic = topic.replace(remove_item, "")
        
        # 清理多余的符号
        topic = topic.strip("_-. ")
        return topic if topic else "未知主题"
    
    def split_documents(self, documents: List[Document], 
                       splitter_type: str = "recursive") -> List[Document]:
        """
        分割文档
        
        Args:
            documents: 待分割的文档列表
            splitter_type: 分割器类型 ("recursive", "character", "token")
            
        Returns:
            分割后的文档片段列表
        """
        if not documents:
            return []
        
        try:
            # 选择分割器
            if splitter_type == "recursive":
                splitter = self.text_splitter
            elif splitter_type == "character":
                splitter = CharacterTextSplitter(
                    chunk_size=settings.chunk_size,
                    chunk_overlap=settings.chunk_overlap
                )
            elif splitter_type == "token":
                splitter = TokenTextSplitter(
                    chunk_size=settings.chunk_size,
                    chunk_overlap=settings.chunk_overlap
                )
            else:
                splitter = self.text_splitter
            
            # 执行分割
            split_docs = splitter.split_documents(documents)
            
            # 为每个片段添加chunk编号
            for i, doc in enumerate(split_docs):
                doc.metadata['chunk_id'] = i
                doc.metadata['chunk_total'] = len(split_docs)
            
            logger.info(f"文档分割完成: {len(documents)} -> {len(split_docs)} 个片段")
            return split_docs
            
        except Exception as e:
            logger.error(f"文档分割失败: {e}")
            return documents
    
    def create_vectorstore(self, documents: List[Document], 
                          store_type: str = "chroma") -> Optional[Union[Chroma, FAISS]]:
        """
        创建向量存储
        
        Args:
            documents: 文档列表
            store_type: 存储类型 ("chroma", "faiss")
            
        Returns:
            向量存储实例
        """
        if not documents:
            logger.error("没有文档可用于创建向量存储")
            return None
        
        try:
            if store_type == "chroma":
                # 使用Chroma向量存储
                self.vectorstore = Chroma.from_documents(
                    documents=documents,
                    embedding=self.embeddings,
                    persist_directory=str(self.chroma_persist_dir)
                )
                
                # 持久化存储
                self.vectorstore.persist()
                logger.info(f"Chroma向量存储创建成功，包含 {len(documents)} 个文档")
                
            elif store_type == "faiss":
                # 使用FAISS向量存储
                self.vectorstore = FAISS.from_documents(
                    documents=documents,
                    embedding=self.embeddings
                )
                
                # 保存FAISS索引
                faiss_path = self.chroma_persist_dir / "faiss_index"
                faiss_path.mkdir(exist_ok=True)
                self.vectorstore.save_local(str(faiss_path))
                logger.info(f"FAISS向量存储创建成功，包含 {len(documents)} 个文档")
            
            return self.vectorstore
            
        except Exception as e:
            logger.error(f"创建向量存储失败: {e}")
            return None
    
    def load_existing_vectorstore(self, store_type: str = "chroma") -> Optional[Union[Chroma, FAISS]]:
        """
        加载已存在的向量存储
        
        Args:
            store_type: 存储类型 ("chroma", "faiss")
            
        Returns:
            向量存储实例
        """
        try:
            if store_type == "chroma" and self.chroma_persist_dir.exists():
                self.vectorstore = Chroma(
                    persist_directory=str(self.chroma_persist_dir),
                    embedding_function=self.embeddings
                )
                logger.info("成功加载已存在的Chroma向量存储")
                
            elif store_type == "faiss":
                faiss_path = self.chroma_persist_dir / "faiss_index"
                if faiss_path.exists():
                    self.vectorstore = FAISS.load_local(
                        str(faiss_path),
                        self.embeddings
                    )
                    logger.info("成功加载已存在的FAISS向量存储")
            
            return self.vectorstore
            
        except Exception as e:
            logger.error(f"加载向量存储失败: {e}")
            return None
    
    def similarity_search(self, query: str, k: int = 5, 
                         filter_dict: Optional[Dict] = None) -> List[Document]:
        """
        相似度搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            filter_dict: 过滤条件
            
        Returns:
            相似文档列表
        """
        if not self.vectorstore:
            logger.error("向量存储未初始化")
            return []
        
        try:
            if filter_dict:
                # 带过滤条件的搜索
                docs = self.vectorstore.similarity_search(
                    query, k=k, filter=filter_dict
                )
            else:
                # 普通相似度搜索
                docs = self.vectorstore.similarity_search(query, k=k)
            
            logger.info(f"相似度搜索完成，返回 {len(docs)} 个结果")
            return docs
            
        except Exception as e:
            logger.error(f"相似度搜索失败: {e}")
            return []
    
    def similarity_search_with_score(self, query: str, k: int = 5) -> List[tuple]:
        """
        带分数的相似度搜索
        
        Args:
            query: 查询文本
            k: 返回结果数量
            
        Returns:
            (文档, 分数) 元组列表
        """
        if not self.vectorstore:
            logger.error("向量存储未初始化")
            return []
        
        try:
            results = self.vectorstore.similarity_search_with_score(query, k=k)
            logger.info(f"带分数搜索完成，返回 {len(results)} 个结果")
            return results
            
        except Exception as e:
            logger.error(f"带分数搜索失败: {e}")
            return []
    
    def create_retrieval_qa_chain(self, chain_type: str = "stuff") -> Optional[RetrievalQA]:
        """
        创建检索问答链
        
        Args:
            chain_type: 链类型 ("stuff", "map_reduce", "refine", "map_rerank")
            
        Returns:
            问答链实例
        """
        if not self.vectorstore:
            logger.error("向量存储未初始化，无法创建问答链")
            return None
        
        try:
            # 创建检索器
            retriever = self.vectorstore.as_retriever(
                search_kwargs={"k": settings.similarity_top_k}
            )
            
            # 创建问答链
            qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type=chain_type,
                retriever=retriever,
                return_source_documents=True,
                verbose=True
            )
            
            logger.info(f"检索问答链创建成功，类型: {chain_type}")
            return qa_chain
            
        except Exception as e:
            logger.error(f"创建问答链失败: {e}")
            return None
    
    async def aprocess_query(self, query: str, qa_chain: RetrievalQA) -> Dict[str, Any]:
        """
        异步处理查询
        
        Args:
            query: 查询文本
            qa_chain: 问答链
            
        Returns:
            查询结果
        """
        try:
            # 在线程池中运行同步的问答链
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: qa_chain({"query": query})
            )
            
            return {
                "answer": result["result"],
                "source_documents": result["source_documents"],
                "query": query
            }
            
        except Exception as e:
            logger.error(f"异步查询处理失败: {e}")
            return {
                "answer": "查询处理失败",
                "source_documents": [],
                "query": query,
                "error": str(e)
            }
    
    def get_document_stats(self) -> Dict[str, Any]:
        """获取文档统计信息"""
        try:
            stats = {
                "knowledge_base_dir": str(self.knowledge_base_dir),
                "vectorstore_type": type(self.vectorstore).__name__ if self.vectorstore else "None",
                "vectorstore_dir": str(self.chroma_persist_dir)
            }
            
            # 统计文件系统中的文档
            file_counts = {}
            total_files = 0
            
            for pattern in ["*.txt", "*.pdf", "*.docx", "*.doc"]:
                files = list(self.knowledge_base_dir.glob(pattern))
                file_counts[pattern] = len(files)
                total_files += len(files)
            
            stats.update({
                "total_files": total_files,
                "file_types": file_counts
            })
            
            # 向量存储统计
            if self.vectorstore:
                if hasattr(self.vectorstore, '_collection'):
                    # Chroma
                    stats["indexed_documents"] = self.vectorstore._collection.count()
                elif hasattr(self.vectorstore, 'index'):
                    # FAISS
                    stats["indexed_documents"] = self.vectorstore.index.ntotal
            
            return stats
            
        except Exception as e:
            logger.error(f"获取文档统计失败: {e}")
            return {}

# 创建全局实例
langchain_processor = LangChainDocumentProcessor()