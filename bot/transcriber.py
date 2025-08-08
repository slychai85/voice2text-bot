import whisper
import os
import uuid
import subprocess

# Загружаем модель один раз при импорте
model = whisper.load_model("medium") # Замените на "base", "medium" или "large" при необходимости

def transcribe_audio(input_path: str) -> str:
    output_path = f"{uuid.uuid4()}.wav"

    try:
        # Конвертируем .oga → .wav
        subprocess.run([
            "ffmpeg", "-i", input_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", output_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Распознаём речь
        result = model.transcribe(output_path, language="ru")
        text = result.get("text", "").strip()

        if not text:
            return "⚠️ Не удалось распознать голос. Попробуйте ещё раз."

        return text

    except Exception as e:
        return f"❌ Ошибка при распознавании: {e}"

    finally:
        # Безопасно удаляем временный файл
        if os.path.exists(output_path):
            os.remove(output_path)
