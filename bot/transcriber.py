import whisper
import os
import uuid
import subprocess

model = whisper.load_model("medium")  # Загрузка модели Whisper base, medium, large и т.д.

def transcribe_audio(input_path: str) -> str:
    wav_path = f"{uuid.uuid4()}.wav"
    try:
        subprocess.run([
            "ffmpeg", "-i", input_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        result = model.transcribe(wav_path, language="ru")
        text = result.get("text", "").strip()
        if not text:
            return "⚠️ Не удалось распознать речь. Попробуйте ещё раз."
        return text
    except Exception as e:
        return f"❌ Ошибка при распознавании: {e}"
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)
