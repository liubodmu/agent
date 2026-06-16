# 面试知识 RAG Agent

基于 RAG 的面试知识问答 Agent，支持八股文问答和出题功能。

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
# Windows 激活
venv\Scripts\activate
# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制配置模板
copy .env.example .env
# 编辑 .env，填入你的 API Key
```

### 3. 准备知识库

将面试文档（.md/.txt/.pdf）放入 `data/knowledge/` 目录。

### 4. 构建知识库索引

```bash
python scripts/index_knowledge.py
```

### 5. 启动服务

```bash
python app/main.py
```

访问 http://localhost:8000/docs 查看 API 文档。

## 项目结构

```
agent/
├── app/
│   ├── main.py              # 应用入口
│   ├── api/
│   │   └── chat.py          # 聊天接口
│   ├── agent/
│   │   ├── router.py        # 意图路由
│   │   └── prompts.py       # Prompt 模板
│   ├── rag/
│   │   ├── retriever.py     # 检索逻辑
│   │   └── pipeline.py      # RAG 管道
│   └── config/
│       └── settings.py      # 配置管理
├── scripts/
│   └── index_knowledge.py   # 知识库建索引脚本
├── data/
│   └── knowledge/           # 原始知识文档
├── requirements.txt
├── .env.example
└── README.md
```

## 技术栈

- Python 3.10+
- FastAPI（Web框架）
- LangChain（RAG框架）
- ChromaDB（向量数据库）
- DeepSeek/OpenAI（LLM）
