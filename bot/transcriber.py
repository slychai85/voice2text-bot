import whisper
import os
import uuid
import subprocess
from typing import Optional

model = whisper.load_model("medium")  # можно использовать "base", "small", "medium", "large" в зависимости от нужд и ресурсов

def transcribe_audio(input_path: str, language: Optional[str] = "ru") -> str:
    """
    language:
      - "ru"  → ожидать русскую речь (лучше для голосовых)
      - None  → автоопределение языка (удобно для видео)
    """
    wav_path = f"{uuid.uuid4()}.wav"
    try:
        subprocess.run([
            "ffmpeg", "-i", input_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        kwargs = {}
        if language is not None:
            kwargs["language"] = language  # это ЯЗЫК АУДИО, не язык вывода

        result = model.transcribe(wav_path, **kwargs)
        text = result.get("text", "").strip()
        if not text:
            return "⚠️ Не удалось распознать речь. Попробуйте ещё раз."
        return text
    except Exception as e:
        return f"❌ Ошибка при распознавании: {e}"
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)
