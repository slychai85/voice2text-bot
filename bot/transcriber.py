import whisper
import os, uuid, subprocess
from typing import Optional
from googletrans import Translator

model = whisper.load_model("medium") # модель Whisper для распознавания речи base, small, medium, large
translator = Translator()  # онлайн-перевод

def transcribe_audio(input_path: str, language: Optional[str] = "ru") -> str:
    wav_path = f"{uuid.uuid4()}.wav"
    try:
        subprocess.run([
            "ffmpeg", "-i", input_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        kwargs = {}
        if language is not None:
            kwargs["language"] = language  # язык аудио

        result = model.transcribe(wav_path, **kwargs)
        text = (result.get("text") or "").strip()
        detected = result.get("language")  # 'en', 'ru', ...

        if not text:
            return "⚠️ Не удалось распознать речь. Попробуйте ещё раз."

        # если автоопределяли и это не русский — переведём в ru
        if language is None and detected and detected != "ru":
            try:
                text_ru = translator.translate(text, src=detected, dest="ru").text
                return text_ru.strip() or text
            except Exception:
                return text  # если перевод упал — вернём оригинал

        return text
    except Exception as e:
        return f"❌ Ошибка при распознавании: {e}"
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)
