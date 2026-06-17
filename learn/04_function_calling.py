"""
阶段4：Function Calling（工具调用）

核心思想：
  之前：AI只能"说话"（输出文本）
  现在：AI可以"动手"（调用工具/函数）

  类比：
  之前：你问同事"数据库里有多少用户"，他猜一个数
  现在：你问同事，他打开数据库查了一下，告诉你准确数字

运行方式：python learn/04_function_calling.py
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


# ========== 先定义几个"假工具"（模拟真实功能） ==========

def get_weather(city: str) -> str:
    """模拟天气查询"""
    weather_data = {
        "北京": "晴天，28°C，湿度40%",
        "上海": "多云，26°C，湿度65%",
        "深圳": "小雨，30°C，湿度80%",
    }
    return weather_data.get(city, f"{city}：暂无数据")


def query_order(order_id: str) -> str:
    """模拟订单查询"""
    orders = {
        "10086": json.dumps({"id": "10086", "status": "已发货", "amount": 99.9, "tracking": "SF123456"}, ensure_ascii=False),
        "10087": json.dumps({"id": "10087", "status": "待付款", "amount": 199.0}, ensure_ascii=False),
    }
    return orders.get(order_id, f"订单{order_id}不存在")


def calculate(expression: str) -> str:
    """模拟计算器"""
    try:
        result = eval(expression)
        return str(result)
    except Exception:
        return "计算错误"


# 工具名到函数的映射
TOOL_FUNCTIONS = {
    "get_weather": get_weather,
    "query_order": query_order,
    "calculate": calculate,
}


def exercise_1():
    """
    练习1：基本工具调用流程

    核心概念：
    1. 你告诉AI有哪些工具可用（Tool定义）
    2. AI分析用户问题，决定要不要调工具
    3. 如果要调，AI会告诉你调哪个工具、传什么参数
    4. 你执行工具，把结果返回给AI
    5. AI基于工具返回的结果生成最终回答
    """
    print("=" * 50)
    print("练习1：基本工具调用流程")
    print("=" * 50)

    # 第1步：定义工具（告诉AI有什么工具可用）
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "查询指定城市的天气情况",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "城市名称，如北京、上海"
                        }
                    },
                    "required": ["city"]
                }
            }
        }
    ]

    user_input = "北京今天天气怎么样？"
    print(f"用户：{user_input}\n")

    # 第2步：发给AI，看AI怎么决策
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": user_input}],
        tools=tools,
    )

    message = response.choices[0].message

    # 第3步：检查AI是否要调工具
    if message.tool_calls:
        tool_call = message.tool_calls[0]
        func_name = tool_call.function.name
        func_args = json.loads(tool_call.function.arguments)

        print(f"AI决策：调用工具 {func_name}，参数 {func_args}")

        # 第4步：执行工具
        tool_func = TOOL_FUNCTIONS[func_name]
        result = tool_func(**func_args)
        print(f"工具返回：{result}")

        # 第5步：把工具结果返回给AI，让AI生成最终回答
        final_response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": user_input},
                message,  # AI决定调工具的那条消息
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                },
            ],
            tools=tools,
        )
        print(f"\nAI最终回答：{final_response.choices[0].message.content}")
    else:
        print(f"AI决定不调工具，直接回答：{message.content}")

    print("""
【流程总结】
  1. 定义工具（name + description + 参数schema）
  2. 用户提问 → 发给AI（带上工具定义）
  3. AI判断"需不需要调工具"
     · 需要 → 返回 tool_calls（工具名+参数）
     · 不需要 → 直接返回文本回答
  4. 你执行工具，拿到结果
  5. 把结果发给AI → AI生成最终回答
""")


def exercise_2():
    """
    练习2：多个工具，AI自己选

    核心概念：你注册多个工具，AI根据用户问题自动选择合适的工具
    类比：你桌上有计算器、字典、地图，别人问你问题，你自己判断该用哪个
    """
    print("=" * 50)
    print("练习2：多工具选择")
    print("=" * 50)

    # 注册3个工具
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "查询指定城市的天气情况",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "城市名称"}
                    },
                    "required": ["city"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "query_order",
                "description": "根据订单ID查询订单状态、金额等信息",
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
                "name": "calculate",
                "description": "计算数学表达式的结果",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {"type": "string", "description": "数学表达式，如 2+3*4"}
                    },
                    "required": ["expression"]
                }
            }
        },
    ]

    # 不同问题，AI会选不同工具
    questions = [
        "上海天气如何？",
        "帮我查一下订单10086",
        "123乘以456等于多少？",
        "你好呀",  # 这个不需要工具
    ]

    for question in questions:
        print(f"用户：{question}")

        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": question}],
            tools=tools,
        )

        message = response.choices[0].message

        if message.tool_calls:
            tool_call = message.tool_calls[0]
            func_name = tool_call.function.name
            func_args = json.loads(tool_call.function.arguments)
            print(f"  → AI选择工具：{func_name}，参数：{func_args}")

            # 执行工具
            result = TOOL_FUNCTIONS[func_name](**func_args)
            print(f"  → 工具返回：{result}")
        else:
            print(f"  → AI不调工具，直接回答：{message.content[:100]}")

        print()

    print("""
【要点】
  · AI通过Tool的 description 来判断该调哪个工具
  · description 写得好不好，直接决定AI选择是否正确
  · 如果问题和所有工具都不相关，AI会直接回答（不调工具）
  · 这就是Agent的基础：AI自主决定用什么工具
""")


def exercise_3():
    """
    练习3：封装一个通用的工具调用流程

    核心概念：把前面的流程封装成可复用的函数
    实际项目中就是这么做的
    """
    print("=" * 50)
    print("练习3：封装通用工具调用流程")
    print("=" * 50)

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "查询指定城市的天气情况",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string", "description": "城市名称"}
                    },
                    "required": ["city"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "query_order",
                "description": "根据订单ID查询订单状态、金额等信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "order_id": {"type": "string", "description": "订单ID"}
                    },
                    "required": ["order_id"]
                }
            }
        },
    ]

    def chat_with_tools(user_input: str) -> str:
        """
        封装后的调用：传入用户问题，自动处理工具调用，返回最终回答

        这个函数就是一个简化版的Agent！
        """
        messages = [{"role": "user", "content": user_input}]

        # 第1步：问AI
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
        )
        message = response.choices[0].message

        # 第2步：如果AI要调工具
        if message.tool_calls:
            messages.append(message)

            # 执行所有工具调用
            for tool_call in message.tool_calls:
                func_name = tool_call.function.name
                func_args = json.loads(tool_call.function.arguments)

                # 执行
                result = TOOL_FUNCTIONS[func_name](**func_args)

                # 把结果加到消息里
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

            # 第3步：让AI基于工具结果生成回答
            final_response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
            )
            return final_response.choices[0].message.content
        else:
            return message.content

    # 使用封装后的函数
    questions = [
        "深圳天气如何？",
        "查一下订单10087的状态",
        "你好",
    ]

    for q in questions:
        print(f"用户：{q}")
        answer = chat_with_tools(q)
        print(f"AI：{answer}\n")

    print("""
【要点】
  · 封装后对外就是一个简单的 chat_with_tools(问题) → 回答
  · 内部自动处理：判断要不要调工具 → 调工具 → 拿结果 → 生成回答
  · 这就是Agent的雏形！
  · 下一步（阶段5）会加上"循环"——一个问题可能需要调多次工具
""")


if __name__ == "__main__":
    print("Function Calling（工具调用）练习")
    print("理解AI怎么'动手做事'\n")

    exercise_1()
    input("\n按回车继续下一个练习...")

    exercise_2()
    input("\n按回车继续下一个练习...")

    exercise_3()

    print("\n" + "=" * 50)
    print("阶段4完成！")
    print("=" * 50)
    print("""
你现在理解了：
  1. Tool定义 — 告诉AI有哪些工具（name + description + 参数）
  2. AI决策  — AI根据问题自动选择工具和参数
  3. 执行+返回 — 你执行工具，把结果喂给AI
  4. 封装    — 把整个流程封装成函数，这就是Agent雏形

下一步：阶段5 - Agent原理（Think-Act-Observe循环）
运行：python learn/05_agent.py
""")
