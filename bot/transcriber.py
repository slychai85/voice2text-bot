import whisper
import os
import uuid
import subprocess

# Загружаем модель один раз при импорте
model = whisper.load_model("base")

def transcribe_audio(input_path: str) -> str:
    try:
        # Генерируем путь для .wav
        output_path = f"{uuid.uuid4()}.wav"

        # Конвертируем в .wav
        subprocess.run([
            "ffmpeg", "-i", input_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", output_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Распознаём
        result = model.transcribe(output_path)
        text = result["text"]

        # Удаляем временный файл
        os.remove(output_path)
        return text.strip()

    except Exception as e:
        return f"❌ Ошибка при распознавании: {e}"
