import sqlite3
from datetime import datetime
from agent.config import DB_PATH


def _get_connection() -> sqlite3.Connection:
    """Crea la conexión y la tabla si no existe."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            artist TEXT NOT NULL,
            genre TEXT,
            year INTEGER,
            reason TEXT,
            spotify_url TEXT,
            recommended_date TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn


def save_recommendations(recommendations: list[dict], date: str = None) -> None:
    """Guarda una lista de recomendaciones en la base de datos."""
    conn = _get_connection()
    date = date or datetime.now().strftime("%Y-%m-%d")

    for song in recommendations:
        conn.execute(
            """
            INSERT INTO recommendations (title, artist, genre, year, reason, spotify_url, recommended_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                song["title"],
                song["artist"],
                song.get("genre"),
                song.get("year"),
                song.get("reason"),
                song.get("spotify_url"),
                date,
            ),
        )

    conn.commit()
    conn.close()


def get_history(limit: int = 50) -> list[dict]:
    """Devuelve las últimas N canciones recomendadas."""
    conn = _get_connection()
    rows = conn.execute(
        "SELECT title, artist, genre, recommended_date FROM recommendations ORDER BY id DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_history_as_text(limit: int = 50) -> str:
    """Devuelve el histórico formateado como texto para inyectar en el prompt."""
    history = get_history(limit)
    if not history:
        return ""
    lines = [f"- {song['artist']} - {song['title']} ({song['genre']}, {song['recommended_date']})" for song in history]
    return "\n".join(lines)


def is_duplicate(title: str, artist: str) -> bool:
    """Comprueba si una canción ya fue recomendada."""
    conn = _get_connection()
    row = conn.execute(
        "SELECT id FROM recommendations WHERE LOWER(title) = LOWER(?) AND LOWER(artist) = LOWER(?)",
        (title, artist),
    ).fetchone()
    conn.close()
    return row is not None