from app.core.config import settings

def get_llm():
    try:
        from langchain_groq import ChatGroq
        return ChatGroq(
            api_key=settings.groq_api_key,
            model_name=settings.groq_model_name,
            temperature=0.5,
            max_tokens=settings.max_llm_tokens,
            model_kwargs={"top_p": 0.9},
            stop=None,
        )
    except Exception:
        class _DummyLLM:
            def invoke(self, prompt):
                return type("R", (), {"content": ""})()
        return _DummyLLM()

def get_llm_response(question: str):
    formatted_prompt = f"You are a helpful assistant.\n{question}"
    llm = get_llm()
    response = llm.invoke(formatted_prompt)
    return response.content
