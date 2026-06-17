"""
阶段6：MCP 协议

核心思想：
  Function Calling 是各家AI的私有协议（OpenAI有一套、Anthropic有一套）
  MCP 是一个开放标准，让AI工具"写一次，处处可用"

  类比：
  Function Calling = 每个手机有不同的充电口（Lightning、USB-C、Micro-USB）
  MCP = 统一用USB-C，一根线充所有手机

  你的MCP网关项目就是：
  把你的"充电口"（REST API）转成"USB-C"（MCP），让所有AI都能用

注意：这个练习文件主要是阅读理解 + 代码示例
      MCP Server需要通过Claude Desktop调用，不能单独运行完整测试
      但你可以运行本文件来理解概念

运行方式：python learn/06_mcp.py
"""


def lesson_1():
    """
    课程1：MCP 协议基本概念
    """
    print("=" * 50)
    print("课程1：MCP 协议是什么")
    print("=" * 50)

    print("""
【MCP = Model Context Protocol（模型上下文协议）】

一句话：AI客户端和工具之间通信的标准协议。

类比HTTP协议：
  HTTP协议定义了"浏览器怎么和服务器通信"
  MCP协议定义了"AI怎么和工具通信"

  浏览器 ←── HTTP ──→ Web服务器
  AI客户端 ←── MCP ──→ MCP Server（工具服务）

MCP的三个核心操作：
  1. list_tools    → AI问"你有什么工具？"
  2. call_tool     → AI说"帮我调XXX工具，参数是YYY"
  3. 返回结果      → 工具返回执行结果

是不是和Function Calling很像？
  对！MCP本质就是标准化的Function Calling。
  区别是：FC是各家AI私有的格式，MCP是开放标准。
""")


def lesson_2():
    """
    课程2：MCP Server 代码示例
    """
    print("=" * 50)
    print("课程2：MCP Server 长什么样")
    print("=" * 50)

    print("""
【一个最简单的MCP Server】

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 创建MCP Server（类似创建一个Flask/FastAPI应用）
app = Server("my-tools")

# 注册工具列表（类似注册路由）
@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="query_order",
            description="查询订单信息",
            inputSchema={
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单ID"
                    }
                },
                "required": ["order_id"]
            }
        )
    ]

# 处理工具调用（类似Controller的处理方法）
@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "query_order":
        order_id = arguments["order_id"]
        # 这里调你的业务逻辑
        result = f"订单{order_id}：已发货"
        return [TextContent(type="text", text=result)]

# 启动（类似app.run()）
async def main():
    async with stdio_server() as (read, write):
        await app.run(read, write)
```

【对比你熟悉的后端框架】

  FastAPI:                          MCP Server:
  app = FastAPI()                   app = Server("name")
  @app.get("/orders/{id}")          @app.list_tools() → 注册工具
  async def get_order(id):          @app.call_tool() → 处理调用
  uvicorn.run(app)                  app.run()

  本质上就是换了个协议，代码结构几乎一样。
""")


def lesson_3():
    """
    课程3：MCP 和 Function Calling 的区别
    """
    print("=" * 50)
    print("课程3：MCP vs Function Calling")
    print("=" * 50)

    print("""
【核心区别】

                Function Calling              MCP
  标准       各家AI私有格式               开放标准
  绑定       绑定单个AI（如GPT）          任何支持MCP的AI都能用
  工具运行   在你的代码里                 独立的MCP Server进程
  通信方式   API调用的一部分              独立的协议（stdio/SSE）
  复用性     换AI就要重写                 写一次，处处可用

【类比】

  Function Calling = 你家的门锁只配了一把钥匙
  MCP = 你家装了标准锁，所有标准钥匙都能开

【实际影响】

  用Function Calling：
    你为GPT写了一套工具 → 想换成Claude → 全部重写
    
  用MCP：
    你写了一个MCP Server → GPT能用，Claude能用，Cursor能用
    换AI不用改工具代码

【你的项目的价值】

  现状：每接入一个AI客户端，都要为它适配一套工具
  你的网关：REST API → MCP → 所有AI客户端自动可用
""")


def lesson_4():
    """
    课程4：MCP 的传输方式
    """
    print("=" * 50)
    print("课程4：MCP 传输方式")
    print("=" * 50)

    print("""
【两种传输方式】

1. stdio（标准输入输出）
   · AI客户端直接启动你的MCP Server进程
   · 通过stdin/stdout通信
   · 类似：命令行管道 echo "hello" | python server.py
   · 适用：本地使用，Claude Desktop就是这种

   配置示例（Claude Desktop的配置文件）：
   {
     "mcpServers": {
       "my-gateway": {
         "command": "python",
         "args": ["C:/path/to/server.py"]
       }
     }
   }

2. SSE（Server-Sent Events）
   · MCP Server以HTTP服务运行
   · AI客户端通过网络连接
   · 类似：WebSocket，但更简单
   · 适用：远程/多客户端/生产环境

   URL示例：http://localhost:3000/sse

【你的项目先用stdio（简单），后期可以加SSE支持】
""")


def lesson_5():
    """
    课程5：你的MCP网关项目 — 把所有知识串起来
    """
    print("=" * 50)
    print("课程5：你的MCP网关项目全局理解")
    print("=" * 50)

    print("""
【你学过的所有知识在项目中的位置】

  阶段1 LLM基础
    → AI客户端（Claude）调用LLM来理解用户意图、生成回答
    → 你不需要写这部分，Claude自己做
    
  阶段2 Prompt工程
    → Tool的description要写好，AI才能正确选择工具
    → 你的网关自动从Swagger的summary/description生成
    
  阶段3 RAG
    → 可选扩展：给每个API加上使用说明的知识库
    → 核心功能不需要

  阶段4 Function Calling
    → MCP就是标准化的Function Calling
    → 你理解了FC，MCP就是换个协议格式

  阶段5 Agent
    → AI客户端就是一个Agent
    → 它通过MCP调用你网关提供的工具
    → Agent的Think-Act-Observe循环：
      Think: "用户要查订单" 
      Act: 调你网关的query_order工具
      Observe: 拿到订单数据
      Think: "信息够了"
      回答: "订单10086已发货..."

  阶段6 MCP（本阶段）
    → 你的网关核心：把REST API转成MCP Tool

【完整数据流】

  用户对Claude说："帮我查订单10086"
      │
      ▼
  Claude（Agent）Think：需要调query_order工具
      │
      ▼  MCP协议
  你的网关收到：call_tool("query_order", {"order_id": "10086"})
      │
      ▼  网关内部
  查注册表 → query_order对应 GET /api/orders/{order_id}
      │
      ▼  HTTP请求
  转发到后端 → GET http://localhost:5000/api/orders/10086
      │
      ▼  HTTP响应
  后端返回 → {"id": "10086", "status": "已发货"}
      │
      ▼  MCP响应
  网关返回给Claude → TextContent("订单10086已发货...")
      │
      ▼
  Claude生成最终回答给用户

【你做的就是中间那个"网关"】
  输入：MCP请求（AI发来的）
  输出：MCP响应（工具执行结果）
  核心：MCP ←→ HTTP 的协议转换
""")


def lesson_6():
    """
    课程6：动手准备 — 安装MCP SDK
    """
    print("=" * 50)
    print("课程6：动手准备")
    print("=" * 50)

    print("""
【下一步：开始做MCP网关项目】

准备工作：
  1. 安装 MCP SDK
     pip install mcp

  2. 安装 Claude Desktop（用来测试）
     下载：https://claude.ai/download

  3. 安装其他依赖
     pip install httpx pyyaml prance

然后按照 MCP网关详细开发方案.md 的 Phase 1 开始：
  写一个最小MCP Server → 让Claude Desktop连上 → 调用成功

加油！你已经理解了所有基础概念，剩下的就是写代码了。
""")


if __name__ == "__main__":
    print("MCP 协议学习")
    print("6个课程，理解MCP协议和你的项目\n")

    lesson_1()
    input("\n按回车继续...")

    lesson_2()
    input("\n按回车继续...")

    lesson_3()
    input("\n按回车继续...")

    lesson_4()
    input("\n按回车继续...")

    lesson_5()
    input("\n按回车继续...")

    lesson_6()

    print("\n" + "=" * 50)
    print("全部6个阶段完成！")
    print("=" * 50)
    print("""
恭喜！你已经系统学习了Agent开发的全部基础知识：

  ✅ 阶段1：LLM基础 — 调API、messages、temperature
  ✅ 阶段2：Prompt工程 — JSON输出、Few-shot、CoT、约束
  ✅ 阶段3：RAG — Embedding、分块、检索增强生成
  ✅ 阶段4：Function Calling — AI调用工具
  ✅ 阶段5：Agent — Think-Act-Observe循环
  ✅ 阶段6：MCP — 标准化工具协议

接下来：开始做MCP网关项目！
参考：桌面上的 "MCP网关详细开发方案.md"
""")
