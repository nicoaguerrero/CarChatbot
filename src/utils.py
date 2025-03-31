from langchain_openai import OpenAIEmbeddings
import faiss
from langchain_community.docstore.in_memory import InMemoryDocstore
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
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
