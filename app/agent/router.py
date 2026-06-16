"""
意图路由器 - 识别用户意图并分发到对应处理逻辑

类比：Controller 层的路由分发，或者策略模式
"""
import json

from openai import OpenAI

from app.config.settings import settings
from app.agent.prompts import INTENT_PROMPT, QUESTION_PROMPT
from app.rag.pipeline import RAGPipeline


class AgentRouter:
    """Agent 路由器（核心调度）"""

    def __init__(self):
        self.llm_client = OpenAI(
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
        )
        self.model = settings.LLM_MODEL
        self.rag_pipeline = RAGPipeline()

    def handle(self, user_input: str, history: list[dict] = None) -> dict:
        """
        处理用户输入（主入口）

        流程：判断意图 → 走对应分支 → 返回结果

        Args:
            user_input: 用户输入
            history: 对话历史

        Returns:
            {"intent": "...", "answer": "...", "sources": [...]}
        """
        # 第1步：识别意图
        intent_result = self._classify_intent(user_input, history)
        intent = intent_result.get("intent", "ask_knowledge")
        topic = intent_result.get("topic", "")
        difficulty = intent_result.get("difficulty", "medium")

        # 第2步：根据意图分发（类似 switch-case）
        if intent == "request_question":
            return self._handle_question(topic, difficulty)
        elif intent == "chitchat":
            return self._handle_chitchat(user_input)
        else:
            # ask_knowledge 和 follow_up 都走 RAG
            return self._handle_knowledge(user_input, history)

    def _classify_intent(self, user_input: str, history: list[dict] = None) -> dict:
        """意图识别（用 LLM 做分类）"""
        history_text = ""
        if history:
            for msg in history[-6:]:
                role = "用户" if msg["role"] == "user" else "AI"
                history_text += f"{role}: {msg['content'][:100]}\n"

        prompt = INTENT_PROMPT.format(history=history_text or "无", user_input=user_input)

        try:
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                max_tokens=200,
            )
            result_text = response.choices[0].message.content.strip()
            # 提取 JSON
            if "{" in result_text:
                json_str = result_text[result_text.index("{") : result_text.rindex("}") + 1]
                return json.loads(json_str)
        except Exception:
            pass

        # 兜底：默认当知识问答
        return {"intent": "ask_knowledge", "topic": "", "difficulty": "medium"}

    def _handle_knowledge(self, question: str, history: list[dict] = None) -> dict:
        """处理知识问答"""
        result = self.rag_pipeline.answer(question, history)
        result["intent"] = "ask_knowledge"
        return result

    def _handle_question(self, topic: str, difficulty: str) -> dict:
        """处理出题请求"""
        # 先检索相关知识
        retrieved_docs = self.rag_pipeline.retriever.search(topic, top_k=3)
        context = "\n\n".join([doc["content"] for doc in retrieved_docs])

        prompt = QUESTION_PROMPT.format(
            context=context or "通用面试知识",
            difficulty=difficulty,
            topic=topic or "综合技术",
        )

        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=2000,
        )

        return {
            "intent": "request_question",
            "answer": response.choices[0].message.content,
            "sources": [],
        }

    def _handle_chitchat(self, user_input: str) -> dict:
        """处理闲聊"""
        response = self.llm_client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "你是一个友好的面试辅导助手。用户在闲聊时简短回应，并引导回面试学习。",
                },
                {"role": "user", "content": user_input},
            ],
            temperature=0.8,
            max_tokens=300,
        )

        return {
            "intent": "chitchat",
            "answer": response.choices[0].message.content,
            "sources": [],
        }
