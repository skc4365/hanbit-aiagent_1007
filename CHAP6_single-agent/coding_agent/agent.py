from dotenv import load_dotenv

from langchain.agents import create_agent, AgentState
from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic

from tools import python_exec_tool, file_write_tool

load_dotenv()

# tools = [python_exec_tool]
tools = [python_exec_tool, file_write_tool]

llm = ChatOpenAI(model="gpt-4o")
# llm = ChatAnthropic(model="claude-opus-4-1-20250805") # 책의 실행 결과는 본 클로드 모델을 사용하여 나온 결과입니다.

graph = create_agent(
    model=llm,
    tools=tools
)


if __name__ == "__main__":
    response = graph.stream(
        {
            "messages": [
                "첫번째 항이 1인 피보나치 수열을 출력하는 파이썬 코드를 작성해주세요. 정상적으로 실행되는 지 확인도 해주세요. ",
                "확인했다면 그 코드는 .py 파일로 저장하세요."
            ]
        }
    )

    for chunk in response:
        for node, value in chunk.items():
            if node:
                print("---", node, "---")
            if "messages" in value:
                print(value['messages'][0].content)

# 결과

# D:\hanbit-aiagent_1007>uv run CHAP6_single-agent\coding_agent\agent.py
# --- model ---

# [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
# [1, 1, 2, 3, 5, 8, 13, 21, 34, 55]
# --- tools ---
# 성공적으로 코드가 실행되었습니다. :
# ```python

# ```
# --- model ---

# --- tools ---
# 파일 'fibonacci_sequence.py'에 성공적으로 작성했습니다.
# --- model ---
# 피보나치 수열을 출력하는 파이썬 코드가 정상적으로 실행되었으며, `fibonacci_sequence.py` 파일로 저장되었습니다.
