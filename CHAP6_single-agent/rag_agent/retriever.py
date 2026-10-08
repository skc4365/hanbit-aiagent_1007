from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.tools import create_retriever_tool

from dotenv import load_dotenv
load_dotenv()

# 이소스에서는 밖의 경로에 DB를 생성하고 있음.
DB_PATH = "./rag_agent/chroma_db" # [ 1 ]

vectorstore = Chroma(
    persist_directory=DB_PATH,
    embedding_function=OpenAIEmbeddings(model="text-embedding-3-small"),
    collection_name="korean_pdf",
)

vectorstore.get()

retriever = vectorstore.as_retriever(search_kwargs={"k": 3}) # [ 2 ]

retriever_tool = create_retriever_tool( # [ 3 ]
    retriever,
    name="pdf_search",
    description="이 도구를 사용하여 한국어 맞춤법 규칙 PDF 문서에서 정보를 검색하세요.",
)

if __name__ == "__main__":
    response = retriever_tool.invoke("부엌 이 들어간 경우 어떻게 발음하나요?")
    print(response)
