from pathlib import Path

TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "email_template.html"

GENRE_EMOJIS = {
    "rock": "🎸",
    "indie": "🌿",
    "electronic": "🔊",
    "house": "🏠",
    "classical": "🎻",
    "techno": "⚡",
    "jazz": "🎷",
    "hiphop": "🎤",
    "soul": "💜",
    "pop": "🎵",
}


def build_email_html(songs: list[dict], intro: str, outro: str) -> str:
    """Construye el email HTML con datos reales de Spotify."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
 
    songs_html = "".join(
        build_song_card(
            song=song,
            emoji=GENRE_EMOJIS.get(song.get("genre", ""), "🎵"),
            cover=song.get("album_cover") or None,
            url=song.get("spotify_url", "#"),
        )
        for song in songs
    )

    html = template.replace("{{intro}}", intro)
    html = html.replace("{{songs_html}}", songs_html)
    html = html.replace("{{outro}}", outro)
 
    return html


def build_song_card(song: dict, emoji: str, cover: str | None, url: str) -> str:
    """
    Genera el bloque HTML de una tarjeta de canción para el email de MusicHub.
    Estructura: fila superior (carátula + info), fila inferior (descripción completa).
    """

    cover_td = (
        f"<td width='90' style='vertical-align:top; padding:0;'>"
        f"<img src='{cover}' width='90' height='90' "
        f"style='display:block; border-radius:10px 0 0 0; object-fit:cover;' "
        f"alt='Portada'/></td>"
        if cover else ""
    )

    album_year = " · ".join(filter(None, [song.get("album", ""), str(song.get("year", ""))]))
    reason     = song.get("reason", "")

    reason_row = f"""
              <!-- ─── Fila inferior: descripción ─── -->
              <tr>
                <td colspan="2"
                    style="padding:10px 16px 14px;
                           border-top:1px solid #e0d0f5;">
                  <p class="song-reason song-reason-p"
                     style="margin:0; font-size:13px; color:#4a3560;
                            line-height:1.7; font-family:'Lato', Arial, sans-serif;
                            font-weight:300;">
                    {reason}
                  </p>
                </td>
              </tr>
    """ if reason else ""

    return f"""
        <tr>
          <td class="song-cell" style="padding:10px 32px 0;">
            <table width="100%" cellpadding="0" cellspacing="0"
                   class="song-card"
                   style="background-color:#f0e8fa;
                          border-radius:10px;
                          overflow:hidden;
                          border-left:3px solid #9b6ecf;">

              <!-- ─── Fila superior: carátula + info ─── -->
              <tr>
                {cover_td}
                <td style="padding:14px 16px; vertical-align:middle;">

                  <!-- Título -->
                  <p class="song-title" style="margin:0 0 4px; font-size:15px; line-height:1.4;">
                    <span>{emoji}</span>
                    <a class="song-title-a" href="{url}"
                       style="color:#2e1a44;
                              text-decoration:none;
                              font-family:'Playfair Display', Georgia, serif;
                              font-weight:600;
                              letter-spacing:0.3px;">
                      {song['title']}
                    </a>
                  </p>

                  <!-- Artista · Álbum · Año -->
                  <p class="song-meta song-meta-p"
                     style="margin:0;
                            font-size:12px;
                            color:#9b6ecf;
                            font-family:'Lato', Arial, sans-serif;
                            letter-spacing:0.5px;
                            text-transform:uppercase;
                            font-weight:400;">
                    {song['artist']}{(' · ' + album_year) if album_year else ''}
                  </p>

                </td>
              </tr>

              {reason_row}

            </table>
          </td>
        </tr>
        <tr><td style="height:6px;"></td></tr>
    """