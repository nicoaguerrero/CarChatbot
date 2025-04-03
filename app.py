from urllib import request

from flask import Flask, current_app, request
import os
from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage
from langchain_community.utilities import SQLDatabase
from langgraph.checkpoint.postgres import PostgresSaver

from src.llm import setup_llm
from src.utils import setup_vectorstore
from src.tools import dbquery, retrieve
from src.agents import setup_graph
from src.prompts import system_prompt
from src.webhook import webhook_get, webhook_post

from psycopg_pool import ConnectionPool

app = Flask(__name__)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

with ConnectionPool(
    conninfo=DATABASE_URL,
    max_size=20,
    kwargs={"autocommit": True, "prepare_threshold": 0}
) as pool:
    checkpointer = PostgresSaver(pool)
checkpointer.setup()


with app.app_context():
    """
    app.APP_ID = os.getenv("APP_ID")
    app.APP_SECRET = os.getenv("APP_SECRET")
    app.ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
    app.VERSION = os.getenv("VERSION")
    app.RECIPIENT_WAID = os.getenv("RECIPIENT_WAID")
    app.PHONE_NUMBER_ID = os.getenv("PHONE_NUMBER_ID")
    app.VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")
    """
    app.checkpointer = checkpointer
    app.llm = setup_llm()
    app.db = SQLDatabase.from_uri(DATABASE_URL)
    app.tools = [retrieve] + dbquery()
    app.vector_store = setup_vectorstore()
    app.graph = setup_graph()

@app.route('/prueba', methods=['GET', 'POST'])
def prueba():
    config = {"configurable": {"thread_id": "1"}}
    current_state = current_app.graph.get_state(config)
    existing_messages: list[BaseMessage] = current_state.values.get("messages", []) if current_state else []
    input_question = "Que autos tienen, podrias decirme las marcas?"
    
    messages_to_send = []
    if not existing_messages:
        messages_to_send.append(SystemMessage(content=system_prompt))
        messages_to_send.append(HumanMessage(content=input_question))
    else:
        messages_to_send.append(HumanMessage(content=input_question))
    
    events = current_app.graph.stream(
        {"messages": messages_to_send},
        config,
        stream_mode="values")
    for event in events:
        print("Assistant:", event["messages"][-1].content)
    return "Prueba terminada"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return webhook_get()
    elif request.method == 'POST':
        return webhook_post()


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
