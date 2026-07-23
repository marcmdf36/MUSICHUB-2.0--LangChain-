from langchain_core.tools import tool
from agent.config import GENRES, SONGS_PER_DAY
from agent.music_search import fetch_candidates, format_candidates_for_llm, get_candidate_by_index
from agent.memory import get_history_as_text, save_recommendations, is_duplicate
from agent.email_builder import build_email_html
from agent.email_sender import send_email

# Variable compartida para el pool de candidatas entre tools
_current_candidates = []


@tool
def search_music() -> str:
    """Busca candidatas musicales en Spotify para los géneros configurados.
    Devuelve una lista numerada de canciones reales con artista, género, año y popularidad.
    Llama a esta herramienta primero, antes de seleccionar canciones."""
    global _current_candidates
    _current_candidates = fetch_candidates(GENRES, per_genre=10)
    return format_candidates_for_llm(_current_candidates)


@tool
def get_history() -> str:
    """Consulta el historial de canciones ya recomendadas.
    Devuelve las últimas canciones enviadas para evitar repeticiones.
    Llama a esta herramienta después de buscar candidatas."""
    return get_history_as_text() or "Ninguna aún (primer día)"


@tool
def save_and_send(selections_json: str) -> str:
    """Guarda las canciones seleccionadas y envía el email.
    Recibe un JSON string con esta estructura:
    {
      "selections": [{"title": "...", "artist": "...", "reason": "..."}],
      "email_subject": "...",
      "email_intro": "...",
      "email_outro": "..."
    }
    Los títulos y artistas deben coincidir EXACTAMENTE con los del pool de candidatas.
    Llama a esta herramienta después de elegir las canciones."""
    import json

    try:
        data = json.loads(selections_json)
    except json.JSONDecodeError:
        return "Error: JSON inválido. Asegúrate de enviar un JSON válido."

    # Cruzar con datos reales de Spotify
    final_songs = []
    not_found = []
    duplicates = []

    for selection in data.get("selections", []):
        full_data = get_candidate_by_index(
            _current_candidates, selection["title"], selection["artist"]
        )
        if not full_data:
            not_found.append(f"{selection['artist']} - {selection['title']}")
            continue
        if is_duplicate(full_data["title"], full_data["artist"]):
            duplicates.append(f"{selection['artist']} - {selection['title']}")
            continue

        full_data["reason"] = selection["reason"]
        final_songs.append(full_data)

        if len(final_songs) >= SONGS_PER_DAY:
            break

    if not final_songs:
        return "Error: ninguna canción válida. Revisa nombres y prueba de nuevo."

    # Guardar en base de datos
    save_recommendations(final_songs)

    # Construir y enviar email
    html = build_email_html(
        songs=final_songs,
        intro=data.get("email_intro", ""),
        outro=data.get("email_outro", ""),
    )
    success = send_email(data.get("email_subject", "🎵 Recomendaciones del día"), html)

    # Informe de resultado
    report = f"✅ {len(final_songs)} canciones guardadas y email {'enviado' if success else 'FALLIDO'}."
    if not_found:
        report += f"\n⚠️ No encontradas en pool: {', '.join(not_found)}"
    if duplicates:
        report += f"\n🔁 Duplicadas (excluidas): {', '.join(duplicates)}"

    return report


# Lista de tools para registrar en el agente
all_tools = [search_music, get_history, save_and_send]