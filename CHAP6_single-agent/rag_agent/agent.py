from dotenv import load_dotenv

load_dotenv()

from langgraph.prebuilt import tools_condition
from langgraph.graph import StateGraph, MessagesState, START, END

from state import AgentState
from nodes import chatbot, retrieve, context_organizer, generate, transform_query
from edges import decide_to_generate, check_hallucinations


graph_builder = StateGraph(AgentState, input_schema=MessagesState)

# chatbot: 사용자 질문 분석 및 검색 도구 호출 여부 결정
graph_builder.add_node("chatbot", chatbot)

# retriever: 벡터 DB 문서 검색 및 페이지별 검색 결과 저장
graph_builder.add_node("retriever", retrieve)

# 시작점 → 사용자 질문 분석
graph_builder.add_edge(START, "chatbot")

# 검색 도구 호출 → retriever / 일반 답변 → 종료
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
    {
        "tools": "retriever",
        END: END,
    }
)

# context_organizer: 검색 문서의 공백·형식 정리
graph_builder.add_node("context_organizer", context_organizer)

# transform_query: 검색에 적합한 질문으로 재작성
graph_builder.add_node("transform_query", transform_query)

# generate: 검색 문서 기반 답변 생성 및 출처 표시
# 재시도 3회 이상: 검색 결과 기반 대체 질문 안내
graph_builder.add_node("generate", generate)

# 문서 검색 → 검색 결과 정리
graph_builder.add_edge("retriever", "context_organizer")

# 문서 관련성 낮음 → 질문 재작성 / 관련성 충분 → 답변 생성
graph_builder.add_conditional_edges(
    "context_organizer",
    decide_to_generate,
    {
        "transform_query": "transform_query",
        "generate": "generate",
    },
)

# 재작성된 질문 → 문서 재검색
graph_builder.add_edge("transform_query", "retriever")

# 문서 근거 부족 → 답변 재생성 / 문서 근거 충족 → 종료
graph_builder.add_conditional_edges(
    "generate",
    check_hallucinations,
    {
        "not supported": "generate",
        "support": END
    },
)

graph = graph_builder.compile()


if __name__ == "__main__":
    try:
        png_bytes = graph.get_graph().draw_mermaid_png()
        with open("graph.png", "wb") as f:
            f.write(png_bytes)
    except Exception:
        pass

    response = graph.stream(
        {
            "messages": [
                "구개음화가 뭐야?"
            ]
        }
    )

    for chunk in response:
        for node, value in chunk.items():
            if node:
                print("---", node, "---")
            if "messages" in value:
                print(value['messages'][0].content)

        print("="*60)

# ===========================================
# 랭그래프 띄우기
# (hanbit-aiagent) D:\hanbit-aiagent_1007\CHAP6_single-agent>uv run langgraph dev

# langgraph.json
    # {
    #   "dependencies": ["./rag_agent"],
    #   "graphs": {
    #     "agent": "./rag_agent/agent.py:graph"
    #   },
    #   "env": ".env"
    # }

# ===========================================

# .env
# OPENAI_API_KEY=${OPENAI_API_KEY}
# TAVILY_API_KEY=${TAVILY_API_KEY}

# ===========================================

# LangSmith 
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_ENDPOINT="https://api.smith.langchain.com"
# LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
# LANGCHAIN_PROJECT="proj0929"

# ===========================================
