"""
阶段1：LLM 基础练习

运行方式：python learn/01_basics.py
按提示一个个练习，理解每个概念
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com"),
)
model = os.getenv("LLM_MODEL", "deepseek-chat")


def exercise_1():
    """
    练习1：最简单的API调用

    核心概念：
    - messages 是一个列表，每条消息有 role 和 content
    - role 有三种：system（系统设定）、user（用户说的）、assistant（AI说的）
    - 类比：你调一个HTTP接口，request body 就是 messages，response 就是 AI 的回答
    """
    print("=" * 50)
    print("练习1：最简单的API调用")
    print("=" * 50)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "user", "content": "用一句话解释什么是HashMap"}
        ],
    )

    # response.choices[0].message.content 就是AI的回答
    print(f"AI回答：{response.choices[0].message.content}")
    print()


def exercise_2():
    """
    练习2：System Prompt（角色设定）

    核心概念：
    - system 消息告诉AI"你是谁、该怎么回答"
    - 类比：你给一个新员工发工作说明书，告诉他职责是什么
    - 同一个问题，不同的system prompt，AI回答风格完全不同
    """
    print("=" * 50)
    print("练习2：System Prompt 的影响")
    print("=" * 50)

    question = "什么是Redis？"

    # 角色A：面试官
    response_a = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是一个严格的技术面试官，回答要简洁专业，像在面试中追问候选人一样。"},
            {"role": "user", "content": question},
        ],
    )

    # 角色B：幼儿园老师
    response_b = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "你是一个幼儿园老师，要用5岁小朋友能听懂的话来解释技术概念，可以用比喻。"},
            {"role": "user", "content": question},
        ],
    )

    print(f"问题：{question}\n")
    print(f"【面试官风格】\n{response_a.choices[0].message.content}\n")
    print(f"【幼儿园老师风格】\n{response_b.choices[0].message.content}\n")


def exercise_3():
    """
    练习3：Temperature（温度/随机性）

    核心概念：
    - temperature=0 → AI每次给一样的回答（确定性高）
    - temperature=1 → AI每次给不一样的回答（随机性高）
    - 类比：
        temperature=0 → 照着标准答案念
        temperature=1 → 自由发挥
    - 实际使用：做分类/提取信息用0，做创作/聊天用0.7-1
    """
    print("=" * 50)
    print("练习3：Temperature 的影响")
    print("=" * 50)

    question = "给我讲一个关于程序员的笑话"

    print(f"问题：{question}\n")

    # temperature=0，跑两次看看是不是一样的
    for i in range(2):
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": question}],
            temperature=0,
        )
        print(f"【temperature=0 第{i+1}次】\n{response.choices[0].message.content}\n")

    # temperature=1，跑两次看看是不是不一样
    for i in range(2):
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": question}],
            temperature=1,
        )
        print(f"【temperature=1 第{i+1}次】\n{response.choices[0].message.content}\n")


def exercise_4():
    """
    练习4：多轮对话

    核心概念：
    - AI本身没有记忆，每次调用都是独立的
    - 要实现"多轮对话"，你需要把之前的对话历史一起发过去
    - messages里按顺序放：user说的 → assistant回的 → user又说的 → ...
    - 类比：AI是个金鱼脑，你每次都要把之前说过的话重复给它听
    """
    print("=" * 50)
    print("练习4：多轮对话")
    print("=" * 50)

    messages = [
        {"role": "system", "content": "你是一个Java技术专家，回答简洁。"}
    ]

    # 模拟3轮对话
    conversations = [
        "HashMap和HashTable有什么区别？",
        "你说的第一点能详细说说吗？",       # 追问 → AI需要知道"第一点"是什么
        "那ConcurrentHashMap呢？",          # 继续追问 → AI需要知道在聊线程安全
    ]

    for user_input in conversations:
        print(f"你：{user_input}")

        # 把用户的新消息加到历史里
        messages.append({"role": "user", "content": user_input})

        # 发送完整的历史给AI
        response = client.chat.completions.create(
            model=model,
            messages=messages,  # 每次都发完整历史
            temperature=0.7,
        )

        ai_reply = response.choices[0].message.content
        print(f"AI：{ai_reply}\n")

        # 把AI的回答也加到历史里（下一轮要用）
        messages.append({"role": "assistant", "content": ai_reply})


def exercise_5():
    """
    练习5：max_tokens（控制回答长度）

    核心概念：
    - Token ≈ 一个汉字或半个英文单词
    - max_tokens 限制AI最多输出多少Token
    - 类比：你告诉AI"最多说50个字"
    - 注意：设太小会导致回答被截断
    """
    print("=" * 50)
    print("练习5：max_tokens 控制回答长度")
    print("=" * 50)

    question = "详细解释一下MySQL的索引原理"

    # 限制50个token → 回答会很短/被截断
    response_short = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": question}],
        max_tokens=50,
    )

    # 限制500个token → 回答比较完整
    response_long = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": question}],
        max_tokens=500,
    )

    print(f"问题：{question}\n")
    print(f"【max_tokens=50】\n{response_short.choices[0].message.content}\n")
    print(f"【max_tokens=500】\n{response_long.choices[0].message.content}\n")

    # 查看实际用了多少token
    print(f"短回答用了 {response_short.usage.completion_tokens} 个token")
    print(f"长回答用了 {response_long.usage.completion_tokens} 个token")
    print(f"（token大致等于字数，但不完全一样）")


if __name__ == "__main__":
    print("LLM 基础练习")
    print("每个练习演示一个核心概念\n")

    exercise_1()
    input("\n按回车继续下一个练习...")

    exercise_2()
    input("\n按回车继续下一个练习...")

    exercise_3()
    input("\n按回车继续下一个练习...")

    exercise_4()
    input("\n按回车继续下一个练习...")

    exercise_5()

    print("\n" + "=" * 50)
    print("阶段1完成！")
    print("=" * 50)
    print("""
你现在应该理解了：
  1. messages 的格式（role + content）
  2. System Prompt 控制AI的角色和风格
  3. Temperature 控制随机性
  4. 多轮对话需要自己维护历史
  5. max_tokens 控制回答长度

下一步：阶段2 - Prompt工程
运行：python learn/02_prompt_engineering.py
""")
