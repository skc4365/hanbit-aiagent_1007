from langgraph.graph import MessagesState

# ============================
# MessagesState: 대화형 에이전트(Chatbot/Agent) 구축 시, 
#       LLM 메시지 기록(Chat History)을 자동으로 추적하고, 누적 관리해 주는 기본 상태(State) 클래스.

# 내부적으로 messages: Annotated[list[AnyMessage], add_messages] 필드 존재함.
# HumanMessage, AIMessage, ToolMessage 등의 메시지 객체 리스트가 이곳에 누적됨.

# add_messages 리듀서(Reducer) 내장
# 동일한 id를 가진 메시지가 전달되면 기존 메시지를 수정(Update)함.
# ============================

class AgentState(MessagesState):
    question: str
    context: str
    answer: str
    retry_num: int

