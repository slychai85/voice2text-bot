import os
import uuid
import subprocess
from typing import Optional

from config.config import WHISPER_MODEL, WHISPER_COMPUTE, WHISPER_THREADS
from faster_whisper import WhisperModel

# офлайн перевод как раньше
from argostranslate import package as argos_package
from argostranslate import translate as argos_translate

# Инициализируем faster-whisper
model = WhisperModel(
    model_size_or_path=WHISPER_MODEL,   # "base" | "medium" | "large-v3"
    device="cpu",
    compute_type=WHISPER_COMPUTE,       # "int8" — самый быстрый на CPU
    cpu_threads=WHISPER_THREADS,
)

def _ensure_argos_pair(from_code: str, to_code: str = "ru") -> None:
    installed = argos_translate.get_installed_languages()
    src = next((l for l in installed if l.code == from_code), None)
    dst = next((l for l in installed if l.code == to_code), None)
    if src and dst and src.get_translation(dst):
        return
    argos_package.update_package_index()
    pkg = next((p for p in argos_package.get_available_packages()
                if p.from_code == from_code and p.to_code == to_code), None)
    if pkg:
        argos_package.install_from_path(pkg.download())

def _translate_to_ru(text: str, from_code: str) -> str:
    _ensure_argos_pair(from_code, "ru")
    installed = argos_translate.get_installed_languages()
    src = next((l for l in installed if l.code == from_code), None)
    dst = next((l for l in installed if l.code == "ru"), None)
    if not src or not dst:
        return text
    return src.get_translation(dst).translate(text)

def _fw_transcribe(wav_path: str, language: Optional[str]) -> tuple[str, str | None]:
    # vad_filter ускоряет за счёт удаления тишины; beam_size=1 — быстрее
    segments, info = model.transcribe(
        wav_path,
        language=language,               # None → автоопределение
        vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
        beam_size=1,
        without_timestamps=True,
        condition_on_previous_text=False
    )
    text = "".join(seg.text for seg in segments).strip()
    detected = info.language
    return text, detected

def transcribe_audio(input_path: str, language: Optional[str] = "ru") -> str:
    wav_path = f"{uuid.uuid4()}.wav"
    try:
        subprocess.run(
            ["ffmpeg", "-i", input_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav_path],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        text, detected = _fw_transcribe(wav_path, language)
        if not text:
            return "⚠️ Не удалось распознать речь. Попробуйте ещё раз."

        # Для видео мы зовём language=None → если не RU, переводим офлайн
        if language is None and (detected and detected != "ru"):
            try:
                return (_translate_to_ru(text, detected) or text).strip()
            except Exception:
                return text

        return text
    except Exception as e:
        return f"❌ Ошибка при распознавании: {e}"
    finally:
        if os.path.exists(wav_path):
            try: os.remove(wav_path)
            except: pass
