from flask import Flask, current_app
import os
from dotenv import load_dotenv

from src.agents import setup_graph, create_agent
from src.llm import setup_llm
from src.utils import setup_vectorstore
from src.tools import dbquery, retrieve

from langchain_community.utilities import SQLDatabase

app = Flask(__name__)

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")

with app.app_context():
    app.llm = setup_llm()
    app.db = SQLDatabase.from_uri(DATABASE_URL)
    app.rag_agent = create_agent(app.llm, [retrieve])
    dbtools = dbquery()
    app.dbquery_agent = create_agent(app.llm, dbtools)
    app.vector_store = setup_vectorstore()
    app.graph = setup_graph()


@app.route('/prueba', methods=['GET', 'POST'])
def prueba():
    input_question = "Que autos tienen, podrias decirme las marcas?"
    for event in current_app.graph.stream({"messages": [("user", input_question)]}, subgraphs=True):
        print(event)
        print("----")
    return "Prueba terminada"


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


if __name__ == '__main__':
    app.run()
