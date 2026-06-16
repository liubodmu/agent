"""
聊天接口 - 类似 Java 的 Controller

提供 HTTP API，接收用户消息，返回 AI 回答
"""
from fastapi import APIRouter
from pydantic import BaseModel

from app.agent.router import AgentRouter

# 创建路由（类似 @RequestMapping）
router = APIRouter(prefix="/api", tags=["chat"])

# Agent 路由器实例（类似 @Autowired Service）
agent_router = AgentRouter()

# 对话历史（简单实现，生产环境应该存数据库）
conversation_history: list[dict] = []


class ChatRequest(BaseModel):
    """请求体（类似 Java 的 RequestDTO）"""
    message: str


class ChatResponse(BaseModel):
    """响应体（类似 Java 的 ResponseDTO）"""
    intent: str
    answer: str
    sources: list[str] = []


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    聊天接口

    类比 Java：
    @PostMapping("/chat")
    public ChatResponse chat(@RequestBody ChatRequest request) { ... }
    """
    # 调用 Agent 处理
    result = agent_router.handle(request.message, conversation_history)

    # 记录对话历史
    conversation_history.append({"role": "user", "content": request.message})
    conversation_history.append({"role": "assistant", "content": result["answer"]})

    # 只保留最近20条
    if len(conversation_history) > 20:
        conversation_history[:] = conversation_history[-20:]

    return ChatResponse(
        intent=result.get("intent", ""),
        answer=result.get("answer", ""),
        sources=result.get("sources", []),
    )


@router.post("/clear")
async def clear_history():
    """清空对话历史"""
    conversation_history.clear()
    return {"message": "对话历史已清空"}
