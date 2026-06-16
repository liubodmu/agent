"""
检索模块 - 从向量数据库中搜索相关知识

类比：类似 Elasticsearch 的搜索，但按语义相似度搜索
"""
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config.settings import settings


class KnowledgeRetriever:
    """知识检索器（类似 DAO 层，负责从向量库查数据）"""

    def __init__(self):
        # 连接向量数据库（类似创建数据库连接池）
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        # 获取集合（类似选择数据库表）
        self.collection = self.client.get_or_create_collection(
            name="interview_knowledge",
            metadata={"description": "面试知识库"},
        )

    def search(self, query: str, top_k: int = 5) -> list[dict]:
        """
        搜索相关知识

        类比 SQL：SELECT * FROM knowledge ORDER BY 相似度 DESC LIMIT top_k

        Args:
            query: 用户的问题
            top_k: 返回前几条最相关的

        Returns:
            相关知识片段列表
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k,
        )

        # 整理结果（类似把 ResultSet 转成 List<DTO>）
        documents = []
        if results and results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0
                documents.append(
                    {
                        "content": doc,
                        "metadata": metadata,
                        "relevance_score": 1 - distance,  # 距离越小越相关
                    }
                )

        return documents

    def get_stats(self) -> dict:
        """获取知识库统计信息"""
        return {
            "total_documents": self.collection.count(),
        }
