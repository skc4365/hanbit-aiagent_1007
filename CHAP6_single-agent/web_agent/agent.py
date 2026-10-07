from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch

from dotenv import load_dotenv

load_dotenv()

### 도구 정의 ###

tool = TavilySearch(max_results=3)
tools = [tool]

llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools(tools)


### 그래프 상태 정의 ###

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)


### 그래프 노드 추가 ###

#### 챗봇 노드 ####

def chatbot(state: State):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}

graph_builder.add_node("chatbot", chatbot)

#### 도구 실행 노드 ####

import json
from langchain_core.messages import ToolMessage

class BasicToolNode:
    """
        마지막 AIMessage에서 요청된 도구를 실행하는 노드
    """

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools} # ["tavily_search" : TavilySearch()]

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []): # [ 1 ]
            message = messages[-1]
        else:
            raise ValueError("ERROR: 입력에 메시지가 없습니다.")

        outputs = []
        for tool_call in message.tool_calls: # 메시지에서 호출된 도구를 불러옴
            tool_result = self.tools_by_name[tool_call["name"]].invoke( # [ 2 ] Tool 호출 실행
                tool_call["args"]
            )
            outputs.append( # [ 3 ] Tool 호출 결과(ToolMessage) 추가
                ToolMessage(
                    content=json.dumps(tool_result, ensure_ascii=False),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}

tool_node = BasicToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)


### 조건부 엣지 추가 ###

def route_tools(
    state: State,
):
    """
    마지막 메시지에 도구 호출이 있는 경우, ToolNode로 라우팅하고 그렇지 않으면 END로 라우팅
    """
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"ERROR: 입력에 메시지가 없습니다. 상태: {state}")

    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END


graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    {"tools": "tools", END: END},
)


### 나머지 엣지 추가 및 그래프 컴파일 ###

graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile()


def invoke():
    response = graph.invoke(
        {
            "messages": ["Langgraph가 무엇인가요?"]
        }
    )

    for msg in response["messages"]:
        msg.pretty_print()


async def ainvoke():
    response = await graph.ainvoke(
        {
            "messages": ["Langgraph가 무엇인가요?"]
        }
    )

    for msg in response["messages"]:
        msg.pretty_print()


def stream():
    response = graph.stream(
        {
            "messages": ["Langgraph가 무엇인가요?"]
        }
    )
    for chunk in response:
        for node, state in chunk.items():
            print("---", node, "---")
            print(state)
            print("=" * 60)

def stream_values():
    response = graph.stream(
        {
            "messages": ["Langgraph가 무엇인가요?"]
        },
        stream_mode="values"
    )

    for chunk in response:
        for state_key, state_value in chunk.items():
            print("--- 현재 상태 ---")
            for msg in state_value:
                print(f"{type(msg).__name__}: {msg.content[:50]}")
            if state_key == "messages":
                state_value[-1].pretty_print()
            print("=" * 60)

def stream_messages():
    response = graph.stream(
        {
            "messages": ["Langgraph가 무엇인가요?"]
        },
        stream_mode="messages"
    )

    for token, metadata in response:
        print(token.content)
        # print(metadata["langgraph_node"])

async def astream():
    response = graph.astream(
        {
            "messages": ["Langgraph가 무엇인가요?"]
        }
    )
    async for chunk in response:
        for node, state in chunk.items():
            print("---", node, "---")
            print(state)
            print("=" * 60)


if __name__ == "__main__":
    import asyncio
    asyncio.run(ainvoke())
    # asyncio.run(astream())

    # invoke()
    # stream()
    # stream_values()
    # stream_messages()


# 겱과

# D:\hanbit-aiagent_1007>uv run CHAP6_single-agent\web_agent\agent.py
# ================================ Human Message =================================

# Langgraph가 무엇인가요?
# ================================== Ai Message ==================================
# Tool Calls:
#   tavily_search (call_6dyldSEgFSfOg5SDizSulWQp)
#  Call ID: call_6dyldSEgFSfOg5SDizSulWQp
#   Args:
#     query: Langgraph가 무엇인가요?
# ================================= Tool Message =================================
# Name: tavily_search

# {"query": "Langgraph가 무엇인가요?", "follow_up_questions": null, "answer": null, "images": [], "results": [{"url": "https://www.ibm.com/kr-ko/think/topics/langgraph", "title": "LangGraph란 무엇인가요? | IBM", "content": "# LangGraph란 무엇인가요?\n\nBryan Clark \n\nSenior AI Advocate\n\n## LangGraph란 무엇인가요?\n\nLangChain에서 만든 LangGraph는 복잡한 생성형 AI 에이전트 워크플로를 구축, 배포, 관리하도록 설계된 오픈 소스 AI 에이전트 프레임워크입니다. 이는 사용자가 확장가능한 방식으로 대규모 언어 모델(LLM)을 만들어서 실행하고 최적화하게 해주는 툴과 라이브러리 세트를 제공합니다. LangGraph의 핵심은 그래프 기반 아키텍처의 힘을 사용하여 AI 에이전트 워크플로의 다양한 구성 요소 간의 복잡한 관계를 모델링하고 관리하는 것입니다. [...] LangGraph 워크플로\n\nLangGraph는 AI 워크플로 안에서 이루어지는 프로세스를 조명하여 에이전트 상태를 완전히 투명하게 공개합니다. LangGraph에 있는 \"상태\" 기능은 AI 시스템이 처리하는 모든 중요 정보를 기록하고 추적하는 기억 장치 역할을 합니다. 이는 다양한 워크플로나 그래프 분석 단계를 오가는 데이터를 캡처하고 업데이트하는 디지털 노트와 유사합니다.\n\n예를 들어 날씨를 모니터링하는 에이전트는 눈이 내린 횟수를 추적하고 변화하는 강설 추세를 바탕으로 제안을 할 수 있습니다. 복잡한 작업을 완수하기 위해 시스템이 어떻게 작동하는지 볼 수 있는 관찰 가능성은 초보자가 상태 관리를 더 깊이 이해하는 데 유용합니다. 상태 관리는 애플리케이션의 상태를 중앙으로 집중시켜서 디버깅 시 유용합니다. 그래서 프로세스 전체를 단축시켜 주곤 합니다. [...] ## LangGraph 확장 방법\n\nLangGraph는 그래프 기반 아키텍처를 사용하여 사용자가 효율성을 저하시키지 않으면서 인공 지능 워크플로를 확장하도록 지원합니다. LangGraph는 노드 간의 복잡한 관계를 모델링하여 의사 결정을 향상시킵니다. 즉, AI 에이전트를 사용하여 이 노드들의 과거 행동과 피드백을 분석합니다. LLM의 세계에서는 이 프로세스를 성찰(reflection)이라고 합니다.\n\n의사 결정: LangGraph는 노드 간의 복잡한 관계를 모델링하여 보다 효과적인 의사 결정 시스템을 구축하기 위한 프레임워크를 제공합니다.\n\n유연성 향상: 개발자가 새로운 구성 요소를 통합하고 기존 워크플로를 조정할 수 있는 오픈 소스 특성과 모듈식 디자인을 갖췄습니다.", "score": 0.91137725, "raw_content": null, "id": "a705dc-00"}, {"url": "https://velog.io/@ohback/LangGraph", "title": "LangGraph란 무엇이고 언제 쓰면 좋을까?", "content": "여기서 등장하는 게 LangGraph다. 이름 그대로 그래프(노드/엣지)로 LLM 애플리케이션의 흐름을 설계한다.  \n LangChain이 블록(모델·프롬프트·툴)을 잘 조립하게 해주는 공구상자라면, LangGraph는 그 블록들이 언제, 어떤 조건으로, 어떤 상태를 들고 움직일지를 정밀하게 오케스트레이션하는 조감도 + 신호등에 가깝다.\n\n  \n\n## 그래서 LangGraph가 뭐냐면..\n\n> LangChain 에서 개발한 LangGraph는 복잡한 생성형 AI 에이전트 워크플로를 구축, 배포 및 관리하도록 설계된 오픈소스 AI 에이전트 프레임워크입니다. 사용자가 확장 가능하고 효율적인 방식으로 대규모 언어 모델 (LLM)을 생성, 실행 및 최적화할 수 있도록 지원하는 도구와 라이브러리 세트를 제공합니다. LangGraph는 그래프 기반 아키텍처의 강력한 기능을 활용하여 AI 에이전트 워크플로 의 다양한 구성 요소 간의 복잡한 관계를 모델링하고 관리합니다. [...] > LangGraph는 단일 에이전트의 한계를 뛰어넘는 다중 에이전트 시스템을 구축할 수 있게 해줍니다. 각 에이전트는 특정 목표를 향해 자율적으로 행동하며, 다른 에이전트들과 협업하여 복잡한 문제를 해결합니다. 이러한 에이전트는 복잡한 의사결정을 위한 사전 정보, 작업 단계를 단축하기 위해 도움이 되는 미리 정의된 도구들 등에 접근하여 활용할지 스스로 결정할 수 있습니다.\n\n \n\n###### 출처: \n\n  \n\n## 구성 요소 및 예시 살펴보기\n\nLangGraph는 기본적으로 에이전트 워크플로를 그래프로 모델링 하는데, 세 가지 핵심 구성 요소를 사용하여 에이전트의 동작을 정의한다.", "score": 0.902481, "raw_content": null, "id": "f6b992-01"}, {"url": "https://data-newbie.tistory.com/997", "title": "LangGraph) LangGraph에 대한 개념과 간단한 예시 만들어보기 — All I Need Is Data.", "content": "LangGraph는 LangChain 생태계 내에서 이러한 문제를 직접 해결하기 위해 설계된 강력한 라이브러리입니다. 이 라이브러리는 여러 LLM 에이전트(또는 체인)를 구조화된 방식으로 정의, 조정 및 실행할 수 있는 프레임워크를 제공합니다.\n\n## LangGraph란 무엇인가요?\n\nLangGraph는 LLM을 사용하여 상태를 유지하고 여러 에이전트를 포함한 애플리케이션을 쉽게 만들 수 있도록 도와줍니다. 이 도구는 LangChain의 기능을 확장하여, 복잡한 에이전트 런타임 개발에 필수적인 순환 그래프를 만들고 관리할 수 있는 기능을 추가합니다. LangGraph의 핵심 개념에는 그래프 구조, 상태 관리 및 조정이 포함됩니다.\n\n### Graph structure\n\nLangGraph에서는 각 노드가 LLM 에이전트를 나타내고, edge는 이 에이전트들 간의 통신 채널입니다.", "score": 0.8934678, "raw_content": null, "id": "afb362-02"}], "response_time": 1.15, "request_id": "ba224da8-fc35-4296-b5a6-367d20a2a518"}
# ================================== Ai Message ==================================

# LangGraph는 LangChain에서 개발한 오픈 소스 AI 에이전트 프레임워크로, 복잡한 생성형 AI 에이전트 워크플로를 구축, 배포, 관리하도록 설계되었습니다. 이 프레임워크는 사용자에게 확장 가능하고 효율적인 방식으로 대규모 언어 모델(LLM)을 생성하고 최적화할 수 있도록 다양한 도구와 라이브러리를 제공합니다. 

# LangGraph의 핵심은 그래프 기반 아키텍처를 활용하여 AI 에이전트 워크플로의 각 구성 요소 간의 복잡한 관계를 모델링하고 관리하는 것입니다. 이를 통해 단일 에이전트의 한계를 넘어서는 다중 에이전트 시스템을 구축할 수 있으며, 여러 에이전트가 협업하여 복잡한 문제를 해결할 수 있게 도와줍니다. 

# LangGraph는 그래프 구조를 활용하여 노드들(LLM 에이전트) 간의 관계와 통신을 모델링하고, 상태 관리 및 조정을 통해 에이전트의 동작을 정의하고 최적화할 수 있습니다.

# 출처: [IBM](https://www.ibm.com/kr-ko/think/topics/langgraph), [Velog](https://velog.io/@ohback/LangGraph)