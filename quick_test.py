"""
快速验证脚本 - 验证 LLM 调用是否正常

第一步先跑这个，确认 API Key 能用
使用方式：python quick_test.py
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

api_key = os.getenv("LLM_API_KEY")
base_url = os.getenv("LLM_BASE_URL", "https://api.deepseek.com")
model = os.getenv("LLM_MODEL", "deepseek-chat")

if not api_key:
    print("错误：请先在 .env 文件中配置 LLM_API_KEY")
    print("步骤：")
    print("  1. 复制 .env.example 为 .env")
    print("  2. 填入你的 DeepSeek API Key")
    print("  注册地址：https://platform.deepseek.com/")
    exit(1)

print(f"配置信息：")
print(f"  API Base: {base_url}")
print(f"  Model: {model}")
print(f"  API Key: {api_key[:8]}...{api_key[-4:]}")
print()

client = OpenAI(api_key=api_key, base_url=base_url)

print("正在调用 LLM...")
print("-" * 40)

response = client.chat.completions.create(
    model=model,
    messages=[{"role": "user", "content": "用一句话解释什么是HashMap"}],
    max_tokens=200,
)

print(f"回答：{response.choices[0].message.content}")
print("-" * 40)
print("\n✅ LLM 调用成功！可以继续下一步了。")
