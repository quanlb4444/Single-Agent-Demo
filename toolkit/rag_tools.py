from typing import Any, Dict, List

from pydantic import BaseModel, Field
from rank_bm25 import BM25Okapi

from .base import Tool, ToolSpec


class RAGArgs(BaseModel):
    query: str = Field(description="User search query")


def rag_tool_factory(corpus: List[str] | None = None) -> Tool:
    corpus = corpus or [
        "Single Agent là kiến trúc một agent duy nhất có thể lập kế hoạch và hành động bằng cách gọi các công cụ",
        "RAG (Retrieval Augmented Generation) hoạt động bằng cách truy xuất các tài liệu liên quan và kết hợp vào sinh văn bản",
        "Function Calling cho phép model gọi hàm với tham số có cấu trúc",
    ]
    tokenized = [doc.split() for doc in corpus]
    bm25 = BM25Okapi(tokenized)

    def handler(query: str) -> Dict[str, Any]:
        scores = bm25.get_scores(query.split())
        ranked = sorted(zip(corpus, scores), key=lambda x: x[1], reverse=True)[:5]
        return {
            "success": True,
            "results": [
                {"text": doc, "score": float(score)} for doc, score in ranked
            ],
        }

    spec = ToolSpec(
        name="rag_search",
        description="Search internal knowledge base using BM25 and return top matches",
        args_schema=RAGArgs,
    )
    return Tool(spec, handler)


