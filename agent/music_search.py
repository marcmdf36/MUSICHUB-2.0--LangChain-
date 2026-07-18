import random
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from agent.config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, LASTFM_API_KEY

_client = None

# Artistas de referencia por género.
# Definen el gusto editorial del agente — se usan para búsqueda directa
# y para descubrir artistas relacionados vía API de Spotify.
REFERENCE_ARTISTS = {
    "rock": ["The Strokes", "Radiohead", "Red Hot Chili Peppers", "Arctic Monkeys", "Franz Ferdinand", "The National", "Pixies"],
    "indie": ["Tame Impala", "Phoenix", "Gorillaz", "Arctic Monkeys", "Radiohead", "Beirut"],
    "electronic": ["Daft Punk", "Kavinsky", "M83", "Crystal Castles", "Caravan Palace", "Empire of the Sun"],
    "pop": ["The Weeknd", "C. Tangana", "Black Eyed Peas", "Twenty One Pilots", "Imagine Dragons", "David Guetta", "Sia"],
    "classical": ["Max Richter", "Erik Satie", "Ludwig Göransson", "Hans Zimmer", "Chopin", "Rachmaninov", "Tchaikovsky", "Nils Frahm"],
}

# Queries de género como fallback para diversidad
SEARCH_QUERIES = {
    "rock": ["genre:rock", "genre:alternative", "genre:garage rock", "genre:post-punk", "genre:psych rock"],
    "indie": ["genre:indie", "genre:indie pop", "genre:indie rock", "genre:dream pop", "genre:shoegaze"],
    "electronic": ["genre:electronic", "genre:ambient", "genre:idm", "genre:downtempo", "genre:electronica"],
    "house": ["genre:house", "genre:deep house", "genre:progressive house", "genre:disco house", "genre:uk garage"],
    "techno": ["genre:techno", "genre:minimal techno", "genre:detroit techno", "genre:dub techno", "genre:acid techno"],
    "classical": ["genre:classical", "genre:orchestra", "genre:piano classical", "genre:contemporary classical", "genre:baroque"],
    "jazz": ["genre:jazz", "genre:bebop", "genre:cool jazz", "genre:jazz fusion", "genre:modal jazz"],
    "hiphop": ["genre:hip hop", "genre:rap", "genre:boom bap", "genre:conscious hip hop", "genre:underground hip hop"],
    "soul": ["genre:soul", "genre:neo soul", "genre:funk", "genre:motown", "genre:r&b"],
    "pop": ["genre:pop", "genre:art pop", "genre:synth pop", "genre:chamber pop", "genre:baroque pop"],
}

# Popularidad mínima para filtrar relleno sin sesgar hacia lo mainstream
MIN_POPULARITY = 20


def _get_client() -> spotipy.Spotify:
    global _client
    if _client is None:
        auth = SpotifyClientCredentials(
            client_id=SPOTIFY_CLIENT_ID,
            client_secret=SPOTIFY_CLIENT_SECRET,
        )
        _client = spotipy.Spotify(auth_manager=auth)
    return _client


def _search_tracks(query: str, limit: int = 10, offset: int = 0) -> list[dict]:
    """Busca canciones en Spotify y devuelve datos estructurados."""
    sp = _get_client()
    try:
        results = sp.search(q=query, type="track", limit=limit, offset=offset)
    except Exception:
        return []

    tracks = []
    for track in results.get("tracks", {}).get("items", []):
        try:
            popularity = track.get("popularity")
            if popularity is not None and popularity < MIN_POPULARITY:
                continue
            popularity = popularity or 0
            tracks.append({
                "title": shorten_title(track["name"]),
                "artist": track["artists"][0]["name"],
                "album": track["album"]["name"],
                "year": track["album"]["release_date"][:4] if track["album"].get("release_date") else None,
                "spotify_url": track["external_urls"]["spotify"],
                "album_cover": track["album"]["images"][0]["url"] if track["album"].get("images") else None,
                "popularity": popularity,
            })
        except (KeyError, IndexError):
            continue
    return tracks


def _get_similar_artists_lastfm(artist_name: str, limit: int = 20) -> list[str]:
    """
    Devuelve artistas similares a uno dado usando Last.fm artist.getSimilar.
    Más fiable que Spotify related_artists para apps en modo desarrollo.
    """
    try:
        response = requests.get(
            "http://ws.audioscrobbler.com/2.0/",
            params={
                "method": "artist.getSimilar",
                "artist": artist_name,
                "api_key": LASTFM_API_KEY,
                "format": "json",
                "limit": limit,
            },
            timeout=10,
        )
        data = response.json()
        similar = data.get("similarartists", {}).get("artist", [])
        return [a["name"] for a in similar]
    except Exception:
        return []


def _fetch_tracks_for_artist(artist_name: str, genre: str, limit: int = 5) -> list[dict]:
    """Busca canciones de un artista concreto y les asigna género."""
    tracks = _search_tracks(f"artist:{artist_name}", limit=limit)
    for t in tracks:
        t["genre"] = genre
    return tracks


def _fetch_reference_tracks(genre: str, references: list[str], total: int = 20) -> list[dict]:
    """
    40% del pool: canciones de artistas de referencia directos.
    Elige 3 artistas aleatorios de la lista y busca canciones de cada uno.
    """
    selected = random.sample(references, min(3, len(references)))
    per_artist = max(1, total // len(selected))
    tracks = []
    for artist in selected:
        tracks.extend(_fetch_tracks_for_artist(artist, genre, limit=per_artist))
    return tracks


def _fetch_related_tracks(genre: str, references: list[str], total: int = 20) -> list[dict]:
    """
    40% del pool: canciones de artistas relacionados a las referencias.
    Elige 2 artistas de referencia, obtiene similares vía Last.fm
    y busca canciones de una muestra de esos similares en Spotify.
    """
    anchors = random.sample(references, min(2, len(references)))
    similar_names = []

    for anchor in anchors:
        similar_names.extend(_get_similar_artists_lastfm(anchor, limit=20))

    if not similar_names:
        return []

    # Deduplicar, excluir los propios artistas de referencia y samplear
    all_references = {a.lower() for artists in REFERENCE_ARTISTS.values() for a in artists}
    similar_names = list({
        name for name in similar_names
        if name.lower() not in all_references
    })

    selected = random.sample(similar_names, min(5, len(similar_names)))
    per_artist = max(1, total // len(selected))
    tracks = []
    for artist in selected:
        tracks.extend(_fetch_tracks_for_artist(artist, genre, limit=per_artist))
    return tracks


def _fetch_genre_tracks(genre: str, total: int = 10) -> list[dict]:
    """
    20% del pool: búsquedas por genre: para descubrimientos fuera de la órbita
    de los artistas de referencia.
    """
    queries = SEARCH_QUERIES.get(genre, [f"genre:{genre}"])
    selected_queries = random.sample(queries, min(2, len(queries)))
    tracks = []
    for query in selected_queries:
        offset = random.randint(0, 100)  # Offset más conservador que antes
        fetched = _search_tracks(query, limit=total // 2, offset=offset)
        for t in fetched:
            t["genre"] = genre
        tracks.extend(fetched)
    return tracks


def fetch_candidates(genres: list[str], per_genre: int = 18) -> list[dict]:
    """
    Genera el pool de candidatas combinando tres fuentes por género:
    - 40% artistas de referencia directos
    - 40% artistas relacionados a las referencias (descubrimiento)
    - 20% búsquedas por genre: (diversidad)
    """
    candidates = []
    seen = set()

    ref_count    = int(per_genre * 0.4)  # ~7 canciones
    related_count = int(per_genre * 0.4) # ~7 canciones
    genre_count  = int(per_genre * 0.2)  # ~4 canciones

    for genre in genres:
        references = REFERENCE_ARTISTS.get(genre, [])
        genre_tracks = []

        if references:
            genre_tracks.extend(_fetch_reference_tracks(genre, references, total=ref_count))
            genre_tracks.extend(_fetch_related_tracks(genre, references, total=related_count))

        genre_tracks.extend(_fetch_genre_tracks(genre, total=genre_count))

        for track in genre_tracks:
            key = (track["title"].lower(), track["artist"].lower())
            if key not in seen:
                candidates.append(track)
                seen.add(key)

    random.shuffle(candidates)
    return candidates


def format_candidates_for_llm(candidates: list[dict]) -> str:
    """Formatea el pool como texto para el prompt."""
    lines = []
    for i, song in enumerate(candidates, 1):
        lines.append(
            f"{i}. {song['artist']} - {song['title']} "
            f"({song['genre']}, {song['year']}, popularidad: {song['popularity']})"
        )
    return "\n".join(lines)


def get_candidate_by_index(candidates: list[dict], title: str, artist: str) -> dict | None:
    """Busca una canción en el pool por título y artista."""
    for c in candidates:
        if c["title"].lower() == title.lower() and c["artist"].lower() == artist.lower():
            return c
    return None


def shorten_title(title: str, max_words: int = 6) -> str:
    """Acorta títulos largos eliminando sufijos comunes."""
    for sep in [' - ', ': ', ' (']:
        if sep in title:
            short = title.split(sep)[0].strip()
            if len(short.split()) <= max_words:
                return short
    return title