"""
Prompt 模板集合

类比：SQL 模板 / 请求模板，预定义好格式，运行时填入变量
"""

# 意图识别 Prompt
INTENT_PROMPT = """你是一个意图分类器。根据用户的输入和对话历史，判断用户的意图。

意图类别：
1. ask_knowledge - 用户想了解某个技术知识点（如"HashMap原理是什么"）
2. request_question - 用户想让你出题/模拟面试（如"给我出一道Redis的题"）
3. follow_up - 用户在追问上一个话题（如"能再详细说说吗"）
4. chitchat - 闲聊/无关内容

对话历史：
{history}

用户输入：{user_input}

请返回JSON格式（不要其他内容）：
{{"intent": "意图类别", "topic": "识别到的技术主题", "difficulty": "easy/medium/hard"}}"""

# 出题 Prompt
QUESTION_PROMPT = """你是一位资深技术面试官。请根据以下知识内容，出一道面试题。

参考知识：
{context}

要求：
1. 难度：{difficulty}
2. 方向：{topic}
3. 题目要考察对知识点的深入理解，不要太基础

输出格式：
## 面试题
（题目内容）

## 考察点
（这道题考察什么）

## 参考答案
（详细的参考答案）

## 评分要点
（面试官会关注哪些点）"""

# 知识问答 Prompt（已集成在 pipeline.py 中）
