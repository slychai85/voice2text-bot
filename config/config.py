import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# ASR
ASR_BACKEND = os.getenv("ASR_BACKEND", "whisper_local")
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "medium")
WHISPER_COMPUTE = os.getenv("WHISPER_COMPUTE", "int8")
WHISPER_THREADS = int(os.getenv("WHISPER_THREADS", "4"))
