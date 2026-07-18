import json
import time
from google import genai
from google.genai.errors import ServerError
from agent.config import GEMINI_API_KEY, LLM_MODEL

client = genai.Client(api_key=GEMINI_API_KEY)

FALLBACK_MODEL = "gemini-2.5-flash"  # Modelo de fallback si el principal falla
MAX_RETRIES = 3
RETRY_DELAY = 10  # segundos entre reintentos

def _call_model(model: str, prompt: str) -> dict:
    """Llama a un modelo concreto y devuelve la respuesta parseada."""
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={
            "temperature": 0.9,
            "top_p": 0.95,
            "response_mime_type": "application/json"
        }
    )
    try:
        return json.loads(response.text)
    except json.JSONDecodeError:
        clean = response.text.strip().strip("```json").strip("```").strip()
        return json.loads(clean)

def ask_llm(prompt: str) -> dict:
    """Envía el prompt a Gemini con reintentos y fallback ante errores 503."""
    models_to_try = [LLM_MODEL, FALLBACK_MODEL]

    for model in models_to_try:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                print(f"[LLM] Usando modelo '{model}', intento {attempt}/{MAX_RETRIES}")
                return _call_model(model, prompt)
            except ServerError as e:
                if "503" in str(e):
                    if attempt < MAX_RETRIES:
                        print(f"[LLM] 503 en '{model}'. Reintentando en {RETRY_DELAY}s...")
                        time.sleep(RETRY_DELAY)
                    else:
                        print(f"[LLM] '{model}' agotó reintentos. Probando fallback...")
                else:
                    raise  # Otros errores se propagan directamente

    raise RuntimeError("[LLM] Todos los modelos fallaron tras reintentos.")