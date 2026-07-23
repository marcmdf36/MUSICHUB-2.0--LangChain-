from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from agent.config import GEMINI_API_KEY, LLM_MODEL, GENRES, SONGS_PER_DAY
from agent.tools import all_tools

# LLM con tools vinculadas
llm = ChatGoogleGenerativeAI(
    model=LLM_MODEL,
    api_key=GEMINI_API_KEY,
    temperature=1.0,
)

AGENT_INSTRUCTIONS = """
Eres un curador musical experto con gusto ecléctico y profundo conocimiento
de {genre_list}. Tienes la personalidad de un amigo melómano que siempre
tiene recomendaciones increíbles.

Tu flujo de trabajo es:
1. Usa la herramienta search_music para obtener candidatas reales de Spotify.
2. Usa la herramienta get_history para ver qué canciones ya recomendaste.
3. Selecciona las {selections_count} mejores canciones del pool, siguiendo estos criterios:
   - Variedad de géneros: no repitas género ni artista.
   - Prioriza canciones interesantes, no las más populares.
   - Equilibrio entre clásicos infravalorados y lanzamientos recientes.
   - NO selecciones canciones del historial.
4. Usa la herramienta save_and_send con un JSON que incluya:
   - selections: título y artista EXACTOS del pool + razón con personalidad
   - email_subject: asunto creativo con algún emoji
   - email_intro: 1-2 frases de apertura con tono cercano
   - email_outro: despedida breve con carácter propio

IMPORTANTE: Los títulos y artistas deben coincidir EXACTAMENTE con el pool.
El contenido del email debe estar en español.
""".format(
    genre_list=", ".join(GENRES),
    selections_count=SONGS_PER_DAY + 3,
)


def run():
    from langgraph.prebuilt import create_react_agent

    agent = create_react_agent(
        model=llm,
        tools=all_tools,
        prompt=AGENT_INSTRUCTIONS,
    )

    print("🤖 Agente iniciado...\n")

    result = agent.invoke(
        {"messages": [HumanMessage(content="Genera las recomendaciones musicales del día y envía el email.")]}
    )

    # Mostrar el resultado final del agente
    last_message = result["messages"][-1]
    print(f"\n📋 Resultado del agente:\n{last_message.content}")


if __name__ == "__main__":
    run()