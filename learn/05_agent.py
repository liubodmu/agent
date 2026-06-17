"""
阶段5：Agent 原理

核心思想：
  Function Calling：用户问 → AI调一次工具 → 回答（一步到位）
  Agent：用户问 → AI思考 → 调工具 → 看结果 → 再思考 → 可能再调工具 → ... → 最终回答

  类比：
  Function Calling = 你问同事一个简单问题，他查一下就告诉你
  Agent = 你给同事一个复杂任务，他要查多个系统、分析、再做决定

  Agent核心循环：Think → Act → Observe → Think → Act → Observe → ... → 回答

运行方式：python learn/05_agent.py
"""
import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)
model = os.getenv("LLM_MODEL", "deepseek-chat")


# ========== 模拟工具 ==========

def query_order(order_id: str) -> str:
    """查询订单"""
    orders = {
        "10086": {"id": "10086", "user_id": "u001", "product": "iPhone 16", "status": "已发货", "amount": 6999},
        "10087": {"id": "10087", "user_id": "u002", "product": "MacBook Pro", "status": "待付款", "amount": 14999},
    }
    if order_id in orders:
        return json.dumps(orders[order_id], ensure_ascii=False)
    return f"订单{order_id}不存在"


def query_user(user_id: str) -> str:
    """查询用户信息"""
    users = {
        "u001": {"id": "u001", "name": "张三", "level": "VIP", "points": 1500, "phone": "138****1234"},
        "u002": {"id": "u002", "name": "李四", "level": "普通", "points": 300, "phone": "139****5678"},
    }
    if user_id in users:
        return json.dumps(users[user_id], ensure_ascii=False)
    return f"用户{user_id}不存在"


def query_logistics(tracking_no: str) -> str:
    """查询物流"""
    logistics = {
        "SF123456": {"tracking_no": "SF123456", "status": "运输中", "location": "深圳分拣中心", "eta": "明天到达"},
    }
    if tracking_no in logistics:
        return json.dumps(logistics[tracking_no], ensure_ascii=False)
    return f"物流单号{tracking_no}暂无信息"


TOOL_FUNCTIONS = {
    "query_order": query_order,
    "query_user": query_user,
    "query_logistics": query_logistics,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "query_order",
            "description": "根据订单ID查询订单信息，包括商品、状态、金额、用户ID等",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {"type": "string", "description": "订单ID"}
                },
                "required": ["order_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_user",
            "description": "根据用户ID查询用户信息，包括姓名、等级、积分等",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "用户ID"}
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_logistics",
            "description": "根据物流单号查询物流状态",
            "parameters": {
                "type": "object",
                "properties": {
                    "tracking_no": {"type": "string", "description": "物流单号"}
                },
                "required": ["tracking_no"]
            }
        }
    },
]


def exercise_1():
    """
    练习1：Agent循环 — 一个问题需要多次工具调用

    场景：用户问"订单10086是谁买的？他是什么等级的会员？"
    AI需要：
      第1步：查订单 → 拿到 user_id
      第2步：用 user_id 查用户 → 拿到会员等级
    这就是Agent的多步推理。
    """
    print("=" * 50)
    print("练习1：Agent 多步推理")
    print("=" * 50)

    user_input = "订单10086是谁买的？他是什么等级的会员？"
    print(f"用户：{user_input}\n")

    messages = [
        {"role": "system", "content": "你是一个客服助手，帮用户查询信息。需要时使用提供的工具。"},
        {"role": "user", "content": user_input},
    ]

    # Agent循环（最多5轮，防止无限循环）
    for step in range(5):
        print(f"--- 第{step + 1}轮 ---")

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOLS,
        )
        message = response.choices[0].message

        # AI要调工具
        if message.tool_calls:
            messages.append(message)

            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)
                print(f"  [Think] AI决定调用：{func_name}({func_args})")

                # 执行工具
                result = TOOL_FUNCTIONS[func_name](**func_args)
                print(f"  [Act]   执行工具")
                print(f"  [Observe] 结果：{result}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })
        else:
            # AI不再调工具，给出最终回答
            print(f"\n最终回答：{message.content}")
            break

        print()

    print("""
【Agent循环总结】
  Think  → AI分析"我需要什么信息"
  Act    → 调用工具获取信息
  Observe → 看到工具返回的结果
  Think  → "信息够了吗？还需要查什么？"
  ...重复直到信息足够...
  回答   → 综合所有信息给出最终回答

  这就是 ReAct 模式：Reasoning（推理）+ Acting（行动）
""")


def exercise_2():
    """
    练习2：手写一个简单的Agent类

    把Agent的核心逻辑封装成类，理解其本质
    """
    print("=" * 50)
    print("练习2：手写一个简单Agent")
    print("=" * 50)

    class SimpleAgent:
        """
        一个最简单的Agent

        本质就是：
        1. 一个LLM（大脑）
        2. 一组工具（手脚）
        3. 一个循环（Think→Act→Observe）
        """

        def __init__(self, tools, tool_functions, system_prompt="你是一个智能助手。"):
            self.tools = tools
            self.tool_functions = tool_functions
            self.system_prompt = system_prompt
            self.max_steps = 5  # 最多执行5步，防止无限循环

        def run(self, user_input: str) -> str:
            """
            Agent主循环

            类比：一个while循环处理请求
            """
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_input},
            ]

            for step in range(self.max_steps):
                # 问AI下一步做什么
                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    tools=self.tools,
                )
                message = response.choices[0].message

                # 如果AI不调工具了 → 任务完成
                if not message.tool_calls:
                    return message.content

                # AI要调工具 → 执行
                messages.append(message)
                for tool_call in message.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)

                    print(f"  [Step {step + 1}] {func_name}({func_args})")

                    result = self.tool_functions[func_name](**func_args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })

            return "达到最大步数限制"

    # 创建Agent
    agent = SimpleAgent(
        tools=TOOLS,
        tool_functions=TOOL_FUNCTIONS,
        system_prompt="你是一个电商客服Agent，帮用户查询订单、用户、物流信息。回答要友好专业。",
    )

    # 测试不同复杂度的问题
    questions = [
        "帮我查一下订单10086的信息",                    # 简单：一步
        "订单10086是谁买的？叫什么名字？",               # 中等：两步
        "帮我查一下李四有没有待付款的订单",               # 复杂：AI需要推理
    ]

    for q in questions:
        print(f"\n用户：{q}")
        answer = agent.run(q)
        print(f"Agent回答：{answer}")
        print("-" * 40)

    print("""
【Agent类的本质】
  class Agent:
      tools = [...]          # 有哪些工具
      tool_functions = {}    # 工具怎么执行
      
      def run(question):
          while True:
              response = LLM(messages, tools)
              if 不需要工具了:
                  return response    # 任务完成
              else:
                  执行工具
                  把结果加到messages

  就这么简单。Agent = LLM + 工具 + 循环
""")


def exercise_3():
    """
    练习3：给Agent加上记忆（对话历史）

    核心：Agent记住之前的对话，支持追问
    """
    print("=" * 50)
    print("练习3：带记忆的Agent")
    print("=" * 50)

    class AgentWithMemory:
        def __init__(self, tools, tool_functions, system_prompt):
            self.tools = tools
            self.tool_functions = tool_functions
            # 记忆 = 持久化的messages列表
            self.memory = [{"role": "system", "content": system_prompt}]

        def chat(self, user_input: str) -> str:
            """带记忆的对话"""
            self.memory.append({"role": "user", "content": user_input})

            # Agent循环
            for _ in range(5):
                response = client.chat.completions.create(
                    model=model,
                    messages=self.memory,
                    tools=self.tools,
                )
                message = response.choices[0].message

                if not message.tool_calls:
                    self.memory.append({"role": "assistant", "content": message.content})
                    return message.content

                self.memory.append(message)
                for tool_call in message.tool_calls:
                    func_name = tool_call.function.name
                    func_args = json.loads(tool_call.function.arguments)
                    print(f"  [调用] {func_name}({func_args})")
                    result = self.tool_functions[func_name](**func_args)
                    self.memory.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })

            return "达到最大步数"

    # 创建带记忆的Agent
    agent = AgentWithMemory(
        tools=TOOLS,
        tool_functions=TOOL_FUNCTIONS,
        system_prompt="你是一个电商客服Agent，帮用户查询信息。回答简洁友好。"
    )

    # 模拟多轮对话
    conversations = [
        "帮我查一下订单10086",
        "这个订单是谁买的？",         # 追问：需要记住上一轮查的订单
        "他是什么等级的会员？",        # 继续追问：需要记住user_id
    ]

    for user_input in conversations:
        print(f"\n用户：{user_input}")
        answer = agent.chat(user_input)
        print(f"Agent：{answer}")

    print("""
【带记忆的Agent】
  · 普通Agent：每次对话是独立的
  · 带记忆Agent：记住之前的对话，支持追问
  · 实现方式：把messages列表持久化（self.memory）
  · 和阶段1学的多轮对话原理一样，只是加上了工具调用
""")


if __name__ == "__main__":
    print("Agent 原理练习")
    print("理解Agent的Think-Act-Observe循环\n")

    exercise_1()
    input("\n按回车继续下一个练习...")

    exercise_2()
    input("\n按回车继续下一个练习...")

    exercise_3()

    print("\n" + "=" * 50)
    print("阶段5完成！")
    print("=" * 50)
    print("""
你现在理解了：
  1. Agent循环 — Think→Act→Observe，直到任务完成
  2. 和FC的区别 — FC是单次调用，Agent是多步循环
  3. Agent本质 — LLM + 工具 + 循环，就这三样
  4. 记忆机制 — 把messages持久化，支持追问

下一步：阶段6 - MCP协议
运行：python learn/06_mcp.py
""")
