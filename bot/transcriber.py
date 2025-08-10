import whisper
import os
import uuid
import subprocess
from typing import Optional

# --- Argos Translate (офлайн перевод) ---
from argostranslate import package as argos_package
from argostranslate import translate as argos_translate

model = whisper.load_model("medium")  # оптимально для CPU

def _ensure_argos_pair(from_code: str, to_code: str = "ru") -> None:
    """Гарантируем наличие пары from->ru для офлайн-перевода."""
    installed = argos_translate.get_installed_languages()
    have_from = next((l for l in installed if l.code == from_code), None)
    have_to = next((l for l in installed if l.code == to_code), None)
    if have_from and have_to and have_from.get_translation(have_to):
        return
    # Ставим нужный пакет (скачает и установит один раз)
    argos_package.update_package_index()
    available = argos_package.get_available_packages()
    pkg = next((p for p in available if p.from_code == from_code and p.to_code == to_code), None)
    if pkg:
        argos_package.install_from_path(pkg.download())

def _translate_to_ru(text: str, from_code: str) -> str:
    """Переводим text -> RU офлайн через Argos."""
    _ensure_argos_pair(from_code, "ru")
    installed = argos_translate.get_installed_languages()
    src = next((l for l in installed if l.code == from_code), None)
    dst = next((l for l in installed if l.code == "ru"), None)
    if not src or not dst:
        return text
    translator = src.get_translation(dst)
    return translator.translate(text)

def transcribe_audio(input_path: str, language: Optional[str] = "ru") -> str:
    """
    language:
      - "ru"  → ожидаем русскую речь (лучше для голосовых; без перевода)
      - None  → автоопределение языка (для видео; если не RU — переведём в RU)
    """
    wav_path = f"{uuid.uuid4()}.wav"
    try:
        subprocess.run([
            "ffmpeg", "-i", input_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav_path
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        kwargs = {}
        if language is not None:
            kwargs["language"] = language  # язык АУДИО

        result = model.transcribe(wav_path, **kwargs)
        text = (result.get("text") or "").strip()
        detected = result.get("language")  # 'en', 'ru', ...

        if not text:
            return "⚠️ Не удалось распознать речь. Попробуйте ещё раз."

        # Если автоопределяли и это не русский — офлайн-перевод в RU
        if language is None and detected and detected != "ru":
            try:
                text_ru = _translate_to_ru(text, detected)
                return text_ru.strip() or text
            except Exception:
                return text

        return text

    except Exception as e:
        return f"❌ Ошибка при распознавании: {e}"
    finally:
        if os.path.exists(wav_path):
            os.remove(wav_path)
