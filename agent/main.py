from agent.config import SONGS_PER_DAY, GENRES
from agent.prompts import build_prompt
from agent.llm import ask_llm
from agent.memory import get_history_as_text, save_recommendations, is_duplicate
from agent.music_search import fetch_candidates, format_candidates_for_llm, get_candidate_by_index
from agent.email_builder import build_email_html
from agent.email_sender import send_email


def run():
    # 1. Spotify genera el pool de candidatas reales
    print("🔍 Buscando candidatas en Spotify...")
    candidates = fetch_candidates(GENRES, per_genre=10)
    print(f"   Encontradas: {len(candidates)} canciones")


    if not candidates:
        print("❌ No se encontraron candidatas. Abortando.")
        return

    # 2. Preparar contexto
    candidates_text = format_candidates_for_llm(candidates)
    history_text = get_history_as_text()

    # 3. El LLM selecciona y redacta (ahora recibe mensajes de LangChain)
    print("🤖 El curador está eligiendo...")
    messages = build_prompt(candidates_text, history_text, SONGS_PER_DAY)
    result = ask_llm(messages)

    # 4. Cruzar selecciones del LLM con datos reales de Spotify
    final_songs = []
    for selection in result["selections"]:
        full_data = get_candidate_by_index(candidates, selection["title"], selection["artist"])
        if full_data and not is_duplicate(full_data["title"], full_data["artist"]):
            full_data["reason"] = selection["reason"]
            final_songs.append(full_data)
            if len(final_songs) >= SONGS_PER_DAY:
                break

    # 5. Guardar en la base de datos
    save_recommendations(final_songs)

    # 6. Construir y enviar email
    if final_songs:
        print("📧 Enviando email...")
        html = build_email_html(
            songs=final_songs,
            intro=result.get("email_intro", ""),
            outro=result.get("email_outro", ""),
        )
        success = send_email(result["email_subject"], html)
        if success:
            print("✅ Email enviado correctamente")
        else:
            print("❌ Fallo en el envío")
    else:
        print("⚠️ No hay canciones nuevas, no se envía email")

    # 7. Resumen en consola
    print(f"\n📋 Resumen: {len(final_songs)} canciones seleccionadas\n")
    for song in final_songs:
        print(f"  🎵 {song['artist']} - {song['title']} ({song['genre']}, {song['year']})")
        # print(f"     → {song['reason']}")
        # print(f"     🔗 {song['spotify_url']}")
        # print()


if __name__ == "__main__":
    run()