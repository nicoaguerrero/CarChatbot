from flask import current_app, jsonify

import faiss
import os
import requests
import json

from langchain_openai import OpenAIEmbeddings
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

def setup_vectorstore():
    embeddings = OpenAIEmbeddings(model="text-embedding-3-large")
    embedding_dim = len(embeddings.embed_query("hello world"))
    index = faiss.IndexFlatL2(embedding_dim)

    if os.path.exists("vectorstore"):
        vector_store = FAISS.load_local("vectorstore", embeddings, allow_dangerous_deserialization=True)
    else:
        vector_store = FAISS(
            embedding_function=embeddings,
            index=index,
            docstore=InMemoryDocstore(),
            index_to_docstore_id={},
        )
        PATH = os.path.join(os.path.dirname(__file__), "..", "data")
        loader = DirectoryLoader(PATH, glob="**/*.txt", loader_cls=TextLoader)
        docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,  # chunk size (characters)
            chunk_overlap=160,  # chunk overlap (characters)
        )
        all_splits = text_splitter.split_documents(docs)

        _ = vector_store.add_documents(documents=all_splits)

        vector_store.save_local("vectorstore")

    return vector_store

# Whatsapp

def get_text_message_input(recipient, text):
    return json.dumps(
        {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
    )

def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.ACCESS_TOKEN}",
    }

    url = f"https://graph.facebook.com/{current_app.VERSION}/{current_app.PHONE_NUMBER_ID}/messages"

    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        return response

def process_whatsapp_message(body):
    wa_id = body["entry"][0]["changes"][0]["value"]["contacts"][0]["wa_id"]
    name = body["entry"][0]["changes"][0]["value"]["contacts"][0]["profile"]["name"]

    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    message_body = message["text"]["body"]

    #response = generate_response(message_body)
    response = "Hola"

    data = get_text_message_input(current_app.RECIPIENT_WAID, response)
    send_message(data)


def is_valid_whatsapp_message(body):
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )
