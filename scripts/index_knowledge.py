"""
知识库建索引脚本 - 离线跑一次

功能：读取 data/knowledge/ 下的文档 → 分块 → 存入向量数据库

类比：类似跑 SQL 初始化脚本，或者 Elasticsearch 建索引

使用方式：
    python scripts/index_knowledge.py
"""
import os
import sys

# 把项目根目录加入 Python 路径（类似 classpath）
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config.settings import settings


def load_documents(knowledge_dir: str) -> list[dict]:
    """
    加载知识文档

    类比：读取文件/从数据源拉数据
    """
    documents = []

    if not os.path.exists(knowledge_dir):
        print(f"知识库目录不存在: {knowledge_dir}")
        print("请创建目录并放入 .md 或 .txt 文件")
        return documents

    for filename in os.listdir(knowledge_dir):
        filepath = os.path.join(knowledge_dir, filename)

        if filename.endswith((".md", ".txt")):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            documents.append(
                {
                    "content": content,
                    "metadata": {
                        "source": filename,
                        "type": filename.rsplit(".", 1)[-1],
                    },
                }
            )
            print(f"  已加载: {filename} ({len(content)} 字)")

    return documents


def split_documents(documents: list[dict], chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    """
    文档分块

    类比：把一篇长文章按段落切开，方便后续检索

    Args:
        documents: 原始文档列表
        chunk_size: 每块大约多少字（太大检索不精准，太小缺乏上下文）
        overlap: 块之间重叠多少字（保证语义连贯）
    """
    chunks = []

    for doc in documents:
        content = doc["content"]
        metadata = doc["metadata"]

        # 先按标题（## / ###）分段
        sections = _split_by_headers(content)

        for section in sections:
            # 如果段落太长，再按字数切
            if len(section) > chunk_size:
                sub_chunks = _split_by_size(section, chunk_size, overlap)
                for chunk in sub_chunks:
                    chunks.append({"content": chunk.strip(), "metadata": metadata})
            else:
                if section.strip():
                    chunks.append({"content": section.strip(), "metadata": metadata})

    return chunks


def _split_by_headers(text: str) -> list[str]:
    """按 Markdown 标题分段"""
    lines = text.split("\n")
    sections = []
    current_section = []

    for line in lines:
        if line.startswith("## ") and current_section:
            sections.append("\n".join(current_section))
            current_section = [line]
        else:
            current_section.append(line)

    if current_section:
        sections.append("\n".join(current_section))

    return sections


def _split_by_size(text: str, chunk_size: int, overlap: int) -> list[str]:
    """按字数分块"""
    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks


def index_to_chroma(chunks: list[dict]):
    """
    将分块后的文档存入向量数据库

    类比：INSERT INTO vector_table (id, content, metadata, embedding) VALUES (...)
    """
    client = chromadb.PersistentClient(
        path=settings.CHROMA_PERSIST_DIR,
        settings=ChromaSettings(anonymized_telemetry=False),
    )

    # 删除旧集合（重建索引）
    try:
        client.delete_collection("interview_knowledge")
    except Exception:
        pass

    # 创建新集合
    collection = client.get_or_create_collection(
        name="interview_knowledge",
        metadata={"description": "面试知识库"},
    )

    # 批量写入（Chroma 内置了 Embedding 模型，自动向量化）
    batch_size = 50
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]

        ids = [f"chunk_{i + j}" for j in range(len(batch))]
        documents = [chunk["content"] for chunk in batch]
        metadatas = [chunk["metadata"] for chunk in batch]

        collection.add(ids=ids, documents=documents, metadatas=metadatas)
        print(f"  已入库: {i + len(batch)}/{len(chunks)} 条")

    return collection.count()


def main():
    print("=" * 50)
    print("知识库建索引")
    print("=" * 50)

    # 第1步：加载文档
    print("\n[1/3] 加载文档...")
    documents = load_documents(settings.KNOWLEDGE_DIR)
    if not documents:
        print("\n没有找到文档，请将 .md 或 .txt 文件放入 data/knowledge/ 目录")
        return

    print(f"共加载 {len(documents)} 个文档")

    # 第2步：分块
    print("\n[2/3] 文档分块...")
    chunks = split_documents(documents)
    print(f"共切分为 {len(chunks)} 个知识片段")

    # 第3步：入库
    print("\n[3/3] 写入向量数据库...")
    total = index_to_chroma(chunks)
    print(f"\n索引完成！知识库共 {total} 条记录")
    print(f"存储位置: {settings.CHROMA_PERSIST_DIR}")


if __name__ == "__main__":
    main()
