from agent.memory import get_history
from collections import Counter

def check_db():
    history = get_history()

    if not history:
        print("La base de datos está vacía.")
        return

    # ── Resumen global ──────────────────────────────────────────
    dates = [s['recommended_date'] for s in history]
    genres = [s['genre'] for s in history]
    genre_counts = Counter(genres).most_common()

    print("=" * 55)
    print("📊 RESUMEN GLOBAL DE LA BASE DE DATOS")
    print("=" * 55)
    print(f"  Total de canciones recomendadas : {len(history)}")
    print(f"  Días con recomendaciones        : {len(set(dates))}")
    print(f"  Primera recomendación           : {min(dates)}")
    print(f"  Última recomendación            : {max(dates)}")
    print()
    print("  Canciones por género:")
    for genre, count in genre_counts:
        print(f"    - {genre}: {count}")

    # ── Muestra de los primeros 5 registros ────────────────────
    print()
    print("=" * 55)
    print("🎵 MUESTRA (primeros 5 registros)")
    print("=" * 55)
    for song in history[:5]:
        print(f"  {song['recommended_date']} | {song['artist']} - {song['title']} ({song['genre']})")

    print()
    print(f"  ... y {len(history) - 5} canciones más en la DB.")

if __name__ == "__main__":
    print("Iniciando check_db...")
    check_db()