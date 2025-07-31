# 🎓 教育行业智能教案生成系统

基于LlamaIndex + LangChain混合架构的RAG（检索增强生成）系统，专为教育行业设计，能够根据优秀教案知识库、学生学情数据和最新教学实践方法，智能生成个性化教案。

## ✨ 系统特性

### 🏗️ 核心架构
- **🔄 混合RAG引擎**: LlamaIndex + LangChain双引擎架构，优势互补
- **📚 智能知识库**: 双重向量化存储，支持多种文档格式和检索策略
- **🧠 记忆管理**: LangChain记忆系统，个性化学习偏好和教学模式
- **⚙️ 工具链增强**: LangChain Agents和Tools，智能分析和决策
- **👥 学情分析**: 通过MCP服务获取学生学习情况数据
- **🌐 增强界面**: 支持双模式生成的直观Web界面
- **🔧 教学实践**: Context7集成获取最新教学方法

### 🚀 主要功能
- **🎓 双模式教案生成**: 基础模式 + LangChain增强模式，满足不同需求
- **🔍 智能问答系统**: 基于混合RAG的教学知识问答和咨询
- **📚 双引擎知识库**: LlamaIndex + LangChain并行处理和检索
- **🧠 智能记忆管理**: 个人偏好学习、教学模式优化、对话历史
- **👥 深度学情分析**: 班级表现分析和个性化教学建议
- **🔧 教学实践集成**: Context7最新教学方法和策略推荐
- **📊 系统监控面板**: 实时系统状态和性能监控
- **📋 完整历史记录**: 教案生成历史和评价反馈系统

## 🛠️ 技术栈

### 🔄 混合RAG架构
- **LlamaIndex 0.9.48**: 高性能向量检索和索引
- **LangChain 0.1.0+**: 智能Agent、记忆管理、工具链
- **混合检索**: 加权融合、排名融合、相似度融合多种策略

### 🗄️ 存储和数据处理  
- **向量数据库**: ChromaDB + FAISS双引擎支持
- **文档处理**: Unstructured + python-docx + PyPDF2
- **数据分析**: Pandas, NumPy, Plotly可视化

### 🤖 AI和模型
- **LLM模型**: OpenAI GPT-3.5/4 + 流式输出
- **嵌入模型**: OpenAI text-embedding-3-small
- **智能体**: LangChain Agents + Tools工具链

### 🌐 Web和服务
- **Web框架**: Streamlit增强版界面
- **MCP集成**: Context7, Sequential服务
- **记忆系统**: 持久化对话历史和偏好管理

## 📦 安装和使用

### 环境要求
- Python 3.10+
- uv包管理器

### 快速开始

1. **克隆项目**
```bash
git clone <repository-url>
cd LlamaIndex_Demo
```

2. **环境配置**
```bash
# 使用uv安装依赖
uv sync

# 复制环境配置文件
cp .env.example .env
```

3. **配置环境变量**
编辑 `.env` 文件，填入必要的配置：
```env
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=https://api.openai.com/v1
CHROMA_PERSIST_DIR=./data/chroma_db
```

4. **运行系统**
```bash
# 启动主程序（推荐）
python main.py

# 或直接启动增强版Web界面
streamlit run src/enhanced_web_app.py

# 或启动基础版Web界面
streamlit run src/web_app.py
```

## 📁 项目结构

```
LlamaIndex_Demo/
├── src/                               # 核心源代码
│   ├── knowledge_base.py              # LlamaIndex知识库管理
│   ├── langchain_document_processor.py # LangChain文档处理
│   ├── memory_manager.py              # LangChain记忆管理
│   ├── lesson_generator.py            # 基础教案生成(LlamaIndex)
│   ├── langchain_lesson_generator.py  # 增强教案生成(LangChain)
│   ├── hybrid_rag_system.py           # 混合RAG系统
│   ├── student_data.py                # 学生数据管理
│   ├── teaching_practices.py          # 教学实践方法
│   ├── web_app.py                     # 基础Web界面
│   └── enhanced_web_app.py            # 增强Web界面
├── data/                              # 数据存储目录
│   ├── knowledge_base/                # 教案文档存储
│   ├── chroma_db/                     # 向量数据库
│   └── student_data/                  # 学生数据和记忆
│       └── memory/                    # 记忆管理数据
├── examples/                          # 示例和演示
├── tests/                             # 单元测试
├── docs/                              # 文档说明  
├── config.py                          # 系统配置
├── main.py                            # 主入口程序
├── pyproject.toml                     # uv项目配置
└── README.md                          # 项目说明
```

## 🎯 使用场景

### 教案生成流程
1. **输入基本信息**: 班级ID、学科、年级、课题等
2. **系统分析**: 自动检索相关教案、分析学情、获取教学方法
3. **智能生成**: 基于多维度数据生成个性化教案
4. **结果展示**: 提供详细的教案内容和参考资料

### 支持的学科
- 语文、数学、英语、物理、化学、生物
- 历史、地理、政治等各主要学科

### 支持的年级
- 小学一年级到高中三年级全覆盖

## 🔧 核心模块详解

### 知识库管理 (`knowledge_base.py`)
- 支持 Word (.docx)、PDF (.pdf)、文本 (.txt) 格式
- 自动提取文档内容并进行向量化
- 基于语义相似度的教案检索
- 支持按学科、年级分类管理

### 学情分析 (`student_data.py`)
- 通过MCP服务获取班级表现数据
- 识别知识薄弱点和学习困难
- 提供个性化教学建议
- 支持学习趋势分析

### 教案生成 (`lesson_generator.py`)
- 整合知识库检索结果
- 结合学情分析数据
- 融入最新教学实践方法
- 生成结构化教案内容

### Web界面 (`web_app.py`)
- 直观的教案生成界面
- 知识库管理功能
- 学情分析可视化
- 历史记录查看

## 📊 系统性能

- **检索速度**: 毫秒级向量检索
- **生成质量**: 基于优质教案和学情的个性化内容
- **扩展性**: 支持大规模教案库和用户并发
- **准确性**: 多维度数据验证确保教案质量

## 🤝 贡献指南

欢迎贡献代码、提出建议或报告问题！

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🙏 致谢

- [LlamaIndex](https://github.com/run-llama/llama_index) - 强大的RAG框架
- [ChromaDB](https://github.com/chroma-core/chroma) - 高效的向量数据库
- [Streamlit](https://streamlit.io/) - 简洁的Web应用框架

---

**让AI赋能教育，让每一份教案都充满智慧！** 🚀