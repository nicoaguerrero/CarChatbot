from langchain.chat_models import init_chat_model

def setup_llm():
    return init_chat_model("gpt-4o-mini", model_provider="openai")