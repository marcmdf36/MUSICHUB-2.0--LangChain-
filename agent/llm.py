import json
from langchain_google_genai import ChatGoogleGenerativeAI
from agent.config import GEMINI_API_KEY, LLM_MODEL

# El LLM como objeto de LangChain
llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL,
    api_key=GEMINI_API_KEY,
    temperature=1.0,
)


def ask_llm(messages) -> dict:
    """Envía los mensajes al LLM y devuelve la respuesta parseada como dict."""
    response = llm.invoke(messages)

    # Extraer texto: puede ser string o lista de bloques
    content = response.content
    if isinstance(content, list):
        content = "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        clean = content.strip().strip("```json").strip("```").strip()
        return json.loads(clean)