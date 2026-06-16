"""
应用入口 - 类似 Java 的 SpringBootApplication 启动类

启动方式：python app/main.py
访问文档：http://localhost:8000/docs
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import router as chat_router

# 创建应用（类似 SpringApplication）
app = FastAPI(
    title="面试知识 RAG Agent",
    description="基于 RAG 的面试知识问答系统，支持八股文问答和出题功能",
    version="0.1.0",
)

# 跨域配置（类似 Spring 的 @CrossOrigin）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由（类似 @ComponentScan 扫描 Controller）
app.include_router(chat_router)


@app.get("/")
async def root():
    """健康检查接口"""
    return {"status": "running", "message": "面试知识 RAG Agent 已启动"}


if __name__ == "__main__":
    # 启动服务（类似 SpringBoot 的 server.port=8000）
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
