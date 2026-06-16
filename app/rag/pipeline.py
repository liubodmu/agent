"""
RAG 管道 - 串联 检索 + LLM生成

类比：类似 Service 层，编排业务逻辑
流程：用户问题 → 检索知识 → 拼 Prompt → 调 LLM → 返回回答
"""
from openai import OpenAI

from app.config.settings import settings
from app.rag.retriever import KnowledgeRetriever


class RAGPipeline:
    """RAG 管道（核心业务逻辑）"""

    def __init__(self):
        # LLM 客户端（类似创建 HTTP Client 调第三方服务）
        self.llm_client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.model = settings.LLM_MODEL

        # 检索器（类似注入 DAO）
        self.retriever = KnowledgeRetriever()

    def answer(self, question: str, history: list[dict] = None) -> dict:
        """
        回答用户问题（核心方法）

        流程：
        1. 检索相关知识
        2. 拼装 Prompt（把知识 + 问题组合起来）
        3. 调 LLM 生成回答
        4. 返回结果

        Args:
            question: 用户问题
            history: 对话历史（可选）

        Returns:
            {"answer": "回答内容", "sources": [引用的知识片段]}
        """
        # 第1步：检索相关知识
        retrieved_docs = self.retriever.search(question, top_k=5)

        # 第2步：拼装上下文
        context = self._build_context(retrieved_docs)

        # 第3步：构建消息（Prompt）
        messages = self._build_messages(question, context, history)

        # 第4步：调 LLM
        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.7,
            max_tokens=2000,
        )

        answer = response.choices[0].message.content

        return {
            "answer": answer,
            "sources": [doc["content"][:100] for doc in retrieved_docs[:3]],
        }

    def _build_context(self, docs: list[dict]) -> str:
        """把检索到的文档拼成一段文本"""
        if not docs:
            return "（未找到相关知识）"

        context_parts = []
        for i, doc in enumerate(docs, 1):
            context_parts.append(f"[知识片段{i}]\n{doc['content']}")

        return "\n\n".join(context_parts)

    def _build_messages(
        self, question: str, context: str, history: list[dict] = None
    ) -> list[dict]:
        """
        构建发给 LLM 的消息

        类比：拼装 SQL 或者拼装请求体
        """
        system_prompt = """你是一位资深的技术面试辅导专家。请根据提供的知识内容回答用户的问题。

规则：
1. 优先基于提供的知识内容回答，确保准确性
2. 如果知识内容不足以回答，可以结合你的知识补充，但要注明
3. 回答要有条理，适当使用要点列表
4. 如果是概念类问题，先给出简洁定义，再展开详细解释
5. 适当给出实际应用场景或面试中的回答技巧"""

        messages = [{"role": "system", "content": system_prompt}]

        # 加入对话历史（最近5轮）
        if history:
            for msg in history[-10:]:
                messages.append(msg)

        # 当前问题 + 检索到的知识
        user_message = f"""参考知识：
{context}

用户问题：{question}"""

        messages.append({"role": "user", "content": user_message})

        return messages
