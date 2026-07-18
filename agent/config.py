import os
from dotenv import load_dotenv

load_dotenv()

# LLM
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
LLM_MODEL = "gemini-3-flash-preview"

# Spotify
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")

# Last.fm
LASTFM_API_KEY = os.getenv("LASTFM_API_KEY")

# Email
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
RECIPIENTS = os.getenv("RECIPIENTS", "").split(",")

# Agente
GENRES = ["rock", "indie", "electronic", "pop", "classical"]
SONGS_PER_DAY = 5
DB_PATH = "data/history.db"