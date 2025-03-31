from langchain.tools import tool
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from pydantic import BaseModel
from flask import current_app

class RagToolSchema(BaseModel):
    question: str
@tool(args_schema=RagToolSchema)
def retrieve(question: str):
    """Retrieve information related to a query."""
    retriever = current_app.vector_store.as_retriever(search_kwargs={"k":2})
    retriever_result = retriever.invoke(question)
    return "\n\n".join(doc.page_content for doc in retriever_result)

def dbquery():
    sql_toolkit = SQLDatabaseToolkit(db=current_app.db, llm=current_app.llm)
    sql_tools = sql_toolkit.get_tools()
    return sql_tools