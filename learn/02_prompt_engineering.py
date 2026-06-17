"""
阶段2：Prompt 工程

核心思想：Prompt 就是"写给AI的指令"，写得好不好直接决定AI回答质量。
类比：你写SQL写得好，查询就快准；Prompt写得好，AI回答就准。

运行方式：python learn/02_prompt_engineering.py
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


def call_llm(system_prompt, user_input, temperature=0):
    """封装一下调用，后面反复用"""
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content


def exercise_1():
    """
    练习1：让AI输出结构化JSON

    核心技巧：在Prompt里明确告诉AI输出格式
    场景：你要把AI的回答存到数据库，需要结构化数据而不是一段话
    """
    print("=" * 50)
    print("练习1：让AI输出结构化JSON")
    print("=" * 50)

    # 不好的写法：AI会返回一大段话
    bad_prompt = "你是一个技术分析师。"
    bad_result = call_llm(bad_prompt, "分析一下Redis的优缺点")
    print(f"【不指定格式】\n{bad_result[:200]}...\n")

    # 好的写法：明确要求JSON格式
    good_prompt = """你是一个技术分析师。请用严格的JSON格式回答，不要输出其他内容。
格式如下：
{
    "technology": "技术名称",
    "pros": ["优点1", "优点2", "优点3"],
    "cons": ["缺点1", "缺点2", "缺点3"],
    "use_cases": ["适用场景1", "适用场景2"]
}"""

    good_result = call_llm(good_prompt, "分析一下Redis的优缺点")
    print(f"【指定JSON格式】\n{good_result}\n")

    # 验证是不是合法JSON
    try:
        parsed = json.loads(good_result)
        print(f"✅ 解析成功！优点有 {len(parsed.get('pros', []))} 条")
    except json.JSONDecodeError:
        print("⚠️ JSON解析失败，可能AI输出了额外内容")

    print("""
【要点】
  · 在Prompt里给出完整的格式示例
  · 加一句"不要输出其他内容"防止AI多嘴
  · temperature=0 让输出更稳定
""")


def exercise_2():
    """
    练习2：Few-shot（给示例让AI学）

    核心技巧：与其描述规则，不如直接给几个例子
    类比：你教新人"按这个格式写"，给他看几个范例比说一堆规则有效
    """
    print("=" * 50)
    print("练习2：Few-shot 示例学习")
    print("=" * 50)

    # 场景：判断用户输入的意图
    # zero-shot（不给示例，直接让AI分类）
    zero_shot_prompt = """判断用户输入的意图类别，只输出类别名：
类别：ask_knowledge（问知识）、request_question（要出题）、chitchat（闲聊）"""

    test_inputs = [
        "HashMap底层怎么实现的",
        "给我出一道Redis的面试题",
        "你好呀",
        "考考我MySQL索引的知识",
        "能再详细说说吗",
    ]

    print("【Zero-shot（不给示例）】")
    for user_input in test_inputs:
        result = call_llm(zero_shot_prompt, user_input)
        print(f"  输入：{user_input} → {result.strip()}")

    print()

    # few-shot（给几个示例）
    few_shot_prompt = """判断用户输入的意图类别，只输出类别名。

示例：
输入："什么是B+树" → ask_knowledge
输入："给我出道题" → request_question
输入："来一道关于JVM的面试题" → request_question
输入："你好" → chitchat
输入："谢谢" → chitchat
输入："能详细说说吗" → ask_knowledge

现在判断："""

    print("【Few-shot（给了示例）】")
    for user_input in test_inputs:
        result = call_llm(few_shot_prompt, f'输入："{user_input}" →')
        print(f"  输入：{user_input} → {result.strip()}")

    print("""
【要点】
  · Few-shot = 给AI看几个"输入→输出"的例子
  · 比描述规则更有效，AI通过模仿示例来学习
  · 示例要覆盖各种类别，每类2-3个
  · 边界case（如"能详细说说吗"）也要给示例
""")


def exercise_3():
    """
    练习3：Chain of Thought（链式思考/一步步推理）

    核心技巧：让AI先分析再给结论，而不是直接给答案
    类比：考试时先写过程再写答案，过程对了答案大概率对
    """
    print("=" * 50)
    print("练习3：Chain of Thought 链式思考")
    print("=" * 50)

    question = """一个电商系统，orders表有1000万行数据，以下SQL为什么慢？
SELECT * FROM orders WHERE DATE(create_time) = '2024-01-01' ORDER BY amount DESC LIMIT 10"""

    # 不用CoT：直接回答
    direct_prompt = "你是一个DBA，简短回答问题。"
    direct_result = call_llm(direct_prompt, question)
    print(f"【直接回答】\n{direct_result}\n")

    # 用CoT：让AI一步步分析
    cot_prompt = """你是一个资深DBA。分析问题时请按以下步骤思考：

第1步：分析SQL的每个部分（SELECT、WHERE、ORDER BY）
第2步：判断每个部分是否能利用索引
第3步：找出性能瓶颈
第4步：给出优化方案

请一步步分析，每步都写出你的推理过程。"""

    cot_result = call_llm(cot_prompt, question)
    print(f"【链式思考】\n{cot_result}\n")

    print("""
【要点】
  · 加一句"请一步步分析"就能显著提升推理质量
  · 对复杂问题特别有效（简单问题不需要）
  · 原理：强迫AI展开推理过程，减少"跳步"导致的错误
  · 实际应用：SQL分析、Bug排查、系统设计等复杂场景
""")


def exercise_4():
    """
    练习4：约束条件（限制AI的行为）

    核心技巧：明确告诉AI什么该做什么不该做
    场景：AI容易"幻觉"（编造不存在的东西），需要约束
    """
    print("=" * 50)
    print("练习4：约束条件")
    print("=" * 50)

    # 模拟RAG场景：给AI一段知识，让它基于知识回答
    knowledge = """
Redis支持5种数据类型：String、List、Hash、Set、ZSet。
Redis是单线程模型（6.0之前），基于内存存储，读写速度极快。
Redis持久化方式有RDB和AOF两种。
"""

    question = "Redis的主从复制原理是什么？"

    # 不加约束：AI可能编造
    no_constraint = "你是一个Redis专家。"
    result_1 = call_llm(no_constraint, f"知识：{knowledge}\n\n问题：{question}")
    print(f"【不加约束】\n{result_1[:300]}\n")

    # 加约束：只基于给定知识回答
    with_constraint = """你是一个Redis专家。请严格基于提供的知识内容回答。

规则：
1. 只能使用提供的知识内容来回答
2. 如果知识内容中没有相关信息，请明确说"提供的资料中没有这部分内容"
3. 不要编造或补充知识内容之外的信息
4. 回答要注明来源"""

    result_2 = call_llm(with_constraint, f"知识：{knowledge}\n\n问题：{question}")
    print(f"【加约束】\n{result_2[:300]}\n")

    print("""
【要点】
  · "不要编造"、"如果不知道就说不知道" → 减少幻觉
  · "只基于提供的知识回答" → RAG场景必备
  · "回答要注明来源" → 可追溯，增加可信度
  · 约束越明确越好，不要含糊
""")


def exercise_5():
    """
    练习5：Prompt模板化（实际项目中的用法）

    核心技巧：把Prompt做成模板，运行时填入变量
    类比：Java的String.format() 或 SQL的预编译语句
    """
    print("=" * 50)
    print("练习5：Prompt模板化")
    print("=" * 50)

    # 定义模板（实际项目中放在单独的文件里）
    INTERVIEW_QUESTION_TEMPLATE = """你是一位资深技术面试官。请根据以下要求出一道面试题。

方向：{topic}
难度：{difficulty}
要求：{requirement}

请按以下格式输出：
## 面试题
（题目内容）

## 考察点
（考察什么知识点）

## 参考答案
（简要参考答案）
"""

    # 使用模板 - 像填表一样
    prompt = INTERVIEW_QUESTION_TEMPLATE.format(
        topic="MySQL索引",
        difficulty="中等",
        requirement="要结合实际场景，不要太理论化",
    )

    result = call_llm("", prompt, temperature=0.7)
    print(f"【生成的面试题】\n{result}\n")

    # 换个参数再生成一道
    prompt_2 = INTERVIEW_QUESTION_TEMPLATE.format(
        topic="Redis缓存",
        difficulty="困难",
        requirement="要考察对缓存穿透/击穿/雪崩的深入理解",
    )

    result_2 = call_llm("", prompt_2, temperature=0.7)
    print(f"【再来一道】\n{result_2}\n")

    print("""
【要点】
  · Prompt模板 = 固定结构 + 可变参数
  · 类比：SQL预编译，PreparedStatement 的 ?占位符
  · 实际项目中所有Prompt都应该模板化
  · 好处：复用、好维护、参数化调用
""")


if __name__ == "__main__":
    print("Prompt 工程练习")
    print("5个技巧，学完你就能写出高质量的Prompt\n")

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
    print("阶段2完成！")
    print("=" * 50)
    print("""
你现在掌握了5个核心Prompt技巧：
  1. 结构化输出 — 让AI输出JSON等固定格式
  2. Few-shot   — 给示例让AI模仿
  3. CoT        — 让AI一步步推理，提升复杂问题的准确率
  4. 约束条件   — 防止AI幻觉、限制回答范围
  5. 模板化     — 实际项目中Prompt的管理方式

下一步：阶段3 - RAG 检索增强生成
运行：python learn/03_rag.py
""")
