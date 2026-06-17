"""
阶段3：RAG 检索增强生成

核心思想：
  普通问答：用户问 → AI用自己的知识回答（可能编造）
  RAG问答：用户问 → 先从知识库搜索相关内容 → 把内容+问题一起给AI → AI基于真实内容回答

类比：
  普通问答 = 你问同事一个问题，他凭记忆回答（可能记错）
  RAG = 你问同事，他先翻文档找到相关内容，再基于文档回答（更准确）

运行方式：python learn/03_rag.py
前置条件：pip install chromadb
"""
import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("LLM_API_KEY"),
    base_url=os.getenv("LLM_BASE_URL"),
)
model = os.getenv("LLM_MODEL", "deepseek-chat")


def exercise_1():
    """
    练习1：Embedding（向量化）是什么

    核心概念：
    - 文本 → 一串数字（向量），语义相近的文本，向量也相近
    - 类比：GPS坐标。"北京"和"朝阳区"的坐标很近，"北京"和"纽约"的坐标很远
    - 文本的"语义坐标"就是Embedding
    """
    print("=" * 50)
    print("练习1：理解 Embedding（向量化）")
    print("=" * 50)

    # ChromaDB 内置了 Embedding 模型，不需要单独调 API
    import chromadb
    client_db = chromadb.Client()  # 内存模式，不持久化

    # 创建一个集合（类似建一张表）
    collection = client_db.create_collection(name="demo")

    # 存入几条数据（ChromaDB 自动把文本转成向量）
    collection.add(
        documents=[
            "HashMap底层是数组+链表+红黑树结构",
            "Redis是基于内存的键值对数据库，读写速度极快",
            "MySQL的B+树索引，所有数据存储在叶子节点",
            "TCP三次握手：SYN → SYN+ACK → ACK",
            "Java的垃圾回收机制主要有标记清除、复制、标记整理三种算法",
        ],
        ids=["1", "2", "3", "4", "5"],
    )

    # 搜索：语义相似度搜索
    print("现在来搜索，看看语义搜索有多智能：\n")

    queries = [
        "Java集合的底层实现",       # 应该匹配 HashMap
        "NoSQL数据库",              # 应该匹配 Redis
        "数据库索引原理",           # 应该匹配 MySQL B+树
        "网络协议的连接过程",       # 应该匹配 TCP三次握手
        "JVM内存管理",              # 应该匹配 GC
    ]

    for query in queries:
        results = collection.query(query_texts=[query], n_results=1)
        matched = results["documents"][0][0]
        distance = results["distances"][0][0]
        print(f"  搜索：{query}")
        print(f"  匹配：{matched}")
        print(f"  距离：{distance:.4f}（越小越相关）\n")

    print("""
【要点】
  · Embedding把文本变成向量（一串数字）
  · 语义相似的文本，向量距离近
  · "Java集合" 能匹配到 "HashMap" → 因为语义相关
  · 传统搜索靠关键词匹配，向量搜索靠语义理解
  · ChromaDB内置了Embedding模型，自动处理
""")


def exercise_2():
    """
    练习2：文档分块（Chunking）

    核心概念：
    - 长文档不能整篇存入，要切成小块
    - 类比：一本书不能整本当答案，要定位到具体哪一页哪一段
    - 块太大 → 搜索不精准（把整本书丢给你）
    - 块太小 → 缺乏上下文（只给你一句话）
    """
    print("=" * 50)
    print("练习2：文档分块")
    print("=" * 50)

    # 模拟一篇长文档
    long_document = """# HashMap 面试知识点

## 基本原理
HashMap是基于哈希表实现的Map接口。它允许null key和null value，是非线程安全的。
默认初始容量16，负载因子0.75。

## 底层数据结构
JDK 1.8之前是数组+链表，JDK 1.8之后是数组+链表+红黑树。
当链表长度超过8且数组长度超过64时，链表转为红黑树。

## put流程
1. 计算key的hash值
2. 计算数组下标
3. 如果该位置为空，直接放入
4. 如果不为空（哈希冲突），key相同则覆盖，不同则追加到链表/红黑树
5. 判断是否需要扩容

## 扩容机制
当元素数量超过容量乘以负载因子时触发扩容。
每次扩容为原来的2倍。
JDK 1.8优化：扩容时元素要么在原位置，要么在原位置加旧容量的位置。

## 线程安全
JDK 1.7中并发put可能导致死循环（链表成环）。
JDK 1.8中不会死循环，但会导致数据丢失。
解决方案：ConcurrentHashMap。"""

    # 分块方法1：按固定字数切
    def split_by_size(text, chunk_size=100):
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i + chunk_size])
        return chunks

    # 分块方法2：按标题（##）切
    def split_by_headers(text):
        chunks = []
        current_chunk = []
        for line in text.split("\n"):
            if line.startswith("## ") and current_chunk:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
            else:
                current_chunk.append(line)
        if current_chunk:
            chunks.append("\n".join(current_chunk))
        return chunks

    # 对比两种分块方式
    size_chunks = split_by_size(long_document, 100)
    header_chunks = split_by_headers(long_document)

    print(f"原文长度：{len(long_document)} 字\n")

    print(f"【按固定100字切】共 {len(size_chunks)} 块")
    for i, chunk in enumerate(size_chunks[:3]):
        print(f"  块{i + 1}：{chunk[:50].strip()}...")
    print(f"  ... 共 {len(size_chunks)} 块\n")

    print(f"【按标题 ## 切】共 {len(header_chunks)} 块")
    for i, chunk in enumerate(header_chunks):
        first_line = chunk.strip().split("\n")[0]
        print(f"  块{i + 1}：{first_line}（{len(chunk)}字）")

    print("""
【要点】
  · 按字数切：简单粗暴，但可能把一个知识点切断
  · 按标题切：保持知识点完整，更推荐
  · 实际项目中通常按标题切 + 字数限制（太长再按字数切）
  · 块之间可以有重叠（overlap），保证语义连贯
""")


def exercise_3():
    """
    练习3：完整 RAG 流程

    核心：把前面学的串起来
    文档分块 → Embedding存入向量库 → 用户提问 → 检索 → 拼Prompt → LLM回答
    """
    print("=" * 50)
    print("练习3：完整 RAG 流程")
    print("=" * 50)

    import chromadb

    # === 第1步：准备知识库 ===
    print("[1/5] 准备知识库...")

    knowledge_chunks = [
        {
            "id": "hashmap_basic",
            "content": "HashMap是基于哈希表实现的Map接口，底层JDK1.8是数组+链表+红黑树。默认初始容量16，负载因子0.75。允许null key和null value，非线程安全。",
            "source": "java_hashmap.md"
        },
        {
            "id": "hashmap_put",
            "content": "HashMap的put流程：1.计算hash值 2.计算数组下标(n-1)&hash 3.位置为空直接放入 4.不为空则key相同覆盖，不同追加链表/红黑树 5.判断是否扩容。",
            "source": "java_hashmap.md"
        },
        {
            "id": "hashmap_resize",
            "content": "HashMap扩容：元素数量超过容量×负载因子时触发，每次扩容为2倍。JDK1.8优化：元素要么在原位置，要么在原位置+旧容量位置，用位运算判断。",
            "source": "java_hashmap.md"
        },
        {
            "id": "redis_basic",
            "content": "Redis是基于内存的键值对数据库，支持String/List/Hash/Set/ZSet五种数据类型。单线程模型，基于IO多路复用处理并发，读写速度极快（10w+ QPS）。",
            "source": "redis_basics.md"
        },
        {
            "id": "redis_cache",
            "content": "缓存穿透：查不存在的数据，方案是布隆过滤器或缓存空值。缓存击穿：热点key过期，方案是互斥锁或永不过期。缓存雪崩：大量key同时过期，方案是过期时间加随机值。",
            "source": "redis_basics.md"
        },
        {
            "id": "mysql_index",
            "content": "MySQL InnoDB使用B+树索引。所有数据存在叶子节点，叶子节点用双向链表连接。非叶子节点只存索引，树高一般2-4层。查询时IO次数等于树的高度。",
            "source": "mysql_index.md"
        },
        {
            "id": "mysql_index_fail",
            "content": "索引失效场景：1.对索引列用函数 2.隐式类型转换 3.LIKE以%开头 4.OR中有非索引列 5.索引列参与计算。可以用EXPLAIN查看是否走了索引。",
            "source": "mysql_index.md"
        },
    ]

    # === 第2步：存入向量库 ===
    print("[2/5] 存入向量数据库...")

    chroma_client = chromadb.Client()
    # 先删旧的再建新的
    try:
        chroma_client.delete_collection("rag_demo")
    except Exception:
        pass
    collection = chroma_client.create_collection("rag_demo")

    collection.add(
        ids=[chunk["id"] for chunk in knowledge_chunks],
        documents=[chunk["content"] for chunk in knowledge_chunks],
        metadatas=[{"source": chunk["source"]} for chunk in knowledge_chunks],
    )
    print(f"  已存入 {collection.count()} 条知识片段\n")

    # === 第3步 & 4 & 5：提问 → 检索 → 生成 ===
    questions = [
        "HashMap的put过程是怎样的？",
        "Redis缓存穿透怎么解决？",
        "MySQL索引什么时候会失效？",
    ]

    for question in questions:
        print(f"问题：{question}")

        # 第3步：检索
        results = collection.query(query_texts=[question], n_results=2)
        retrieved_docs = results["documents"][0]
        retrieved_sources = [m["source"] for m in results["metadatas"][0]]

        print(f"[3/5] 检索到 {len(retrieved_docs)} 条相关知识：")
        for i, (doc, src) in enumerate(zip(retrieved_docs, retrieved_sources)):
            print(f"  片段{i + 1}（来自{src}）：{doc[:60]}...")

        # 第4步：拼Prompt
        context = "\n\n".join(retrieved_docs)
        prompt = f"""基于以下知识内容回答问题。只能使用提供的知识，不要编造。

知识内容：
{context}

问题：{question}"""

        # 第5步：调LLM生成回答
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "你是一个技术面试辅导专家，基于提供的知识内容准确回答。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )
        answer = response.choices[0].message.content
        print(f"\n[5/5] AI回答：\n{answer}")
        print("-" * 50 + "\n")

    print("""
【RAG完整流程总结】
  1. 知识库准备：文档 → 分块 → 存入向量库
  2. 用户提问
  3. 检索：用问题去向量库搜索相关片段
  4. 拼Prompt：把检索到的片段 + 用户问题组合成Prompt
  5. 生成：LLM基于检索内容生成回答

  就像一个开卷考试：
  用户出题 → 你先翻书找到相关内容 → 基于书上的内容作答
""")


def exercise_4():
    """
    练习4：对比有无RAG的效果

    直观感受RAG的价值（以及局限性）
    """
    print("=" * 50)
    print("练习4：对比有无RAG的效果")
    print("=" * 50)

    import chromadb

    # 建一个包含"AI不太可能知道的信息"的知识库
    chroma_client = chromadb.Client()
    try:
        chroma_client.delete_collection("compare_demo")
    except Exception:
        pass
    collection = chroma_client.create_collection("compare_demo")

    # 存一些"自定义的/非公开的"知识
    collection.add(
        ids=["1", "2", "3"],
        documents=[
            "我们公司的订单超时时间是30分钟，超过30分钟未支付自动取消。退款周期是3-5个工作日。",
            "我们的用户等级分为：普通会员（消费0-999）、银卡（1000-4999）、金卡（5000-19999）、钻石（20000以上）。",
            "我们的API限流规则：普通用户100次/分钟，VIP用户500次/分钟，超出返回429错误码。",
        ],
    )

    question = "我们公司的用户等级是怎么划分的？"

    # 方式A：直接问AI（没有RAG）
    response_no_rag = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": question}],
        temperature=0,
    )
    print(f"问题：{question}\n")
    print(f"【没有RAG - 直接问AI】")
    print(f"{response_no_rag.choices[0].message.content[:200]}\n")

    # 方式B：RAG（先检索再回答）
    results = collection.query(query_texts=[question], n_results=1)
    context = results["documents"][0][0]

    response_with_rag = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "基于提供的知识回答，不要编造。"},
            {"role": "user", "content": f"知识：{context}\n\n问题：{question}"},
        ],
        temperature=0,
    )
    print(f"【有RAG - 基于知识库回答】")
    print(f"{response_with_rag.choices[0].message.content[:200]}\n")

    print("""
【对比总结】
  · 没有RAG：AI不知道"你们公司"的信息，只能瞎猜或说不知道
  · 有了RAG：AI基于知识库中的真实数据回答，准确可靠

  RAG的真正价值：让AI能回答"它本来不知道的私有信息"
  公开知识（HashMap原理）→ AI本身就会，RAG价值不大
  私有知识（公司规则）→ AI不知道，RAG价值很大
""")


if __name__ == "__main__":
    print("RAG 检索增强生成 练习")
    print("4个练习，理解RAG的完整流程\n")

    exercise_1()
    input("\n按回车继续下一个练习...")

    exercise_2()
    input("\n按回车继续下一个练习...")

    exercise_3()
    input("\n按回车继续下一个练习...")

    exercise_4()

    print("\n" + "=" * 50)
    print("阶段3完成！")
    print("=" * 50)
    print("""
你现在理解了：
  1. Embedding — 文本转向量，语义相似的向量距离近
  2. 分块策略 — 按标题切比按字数切更好
  3. RAG完整流程 — 分块→存库→检索→拼Prompt→生成
  4. RAG的价值 — 让AI回答它不知道的私有信息

下一步：阶段4 - Function Calling（工具调用）
运行：python learn/04_function_calling.py
""")
