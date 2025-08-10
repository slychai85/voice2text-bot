import os, uuid, subprocess
from typing import Optional
from config.config import ASR_BACKEND, WHISPER_MODEL, WHISPER_COMPUTE, WHISPER_THREADS, OPENAI_API_KEY

# локально: faster-whisper
from faster_whisper import WhisperModel
fw_model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type=WHISPER_COMPUTE, cpu_threads=WHISPER_THREADS)

# офлайн-перевод (как было)
from argostranslate import package as argos_package
from argostranslate import translate as argos_translate

# OpenAI API
from openai import OpenAI
oai = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def _ensure_argos_pair(fc: str, tc: str="ru"):
    installed = argos_translate.get_installed_languages()
    src = next((l for l in installed if l.code==fc), None)
    dst = next((l for l in installed if l.code==tc), None)
    if src and dst and src.get_translation(dst): return
    argos_package.update_package_index()
    pkg = next((p for p in argos_package.get_available_packages() if p.from_code==fc and p.to_code==tc), None)
    if pkg: argos_package.install_from_path(pkg.download())

def _translate_to_ru(text: str, fc: str) -> str:
    _ensure_argos_pair(fc, "ru")
    installed = argos_translate.get_installed_languages()
    src = next((l for l in installed if l.code==fc), None)
    dst = next((l for l in installed if l.code=="ru"), None)
    return src.get_translation(dst).translate(text) if (src and dst) else text

def _fw_transcribe(wav: str, lang: Optional[str]) -> tuple[str, Optional[str]]:
    segs, info = fw_model.transcribe(
        wav, language=lang, vad_filter=True,
        vad_parameters=dict(min_silence_duration_ms=500),
        beam_size=1, without_timestamps=True, condition_on_previous_text=False
    )
    return ("".join(s.text for s in segs).strip(), getattr(info, "language", None))

def _oai_transcribe(wav: str, lang: Optional[str]) -> tuple[str, Optional[str]]:
    with open(wav, "rb") as f:
        r = oai.audio.transcriptions.create(model="whisper-1", file=f, language=lang)
    return ((getattr(r, "text", "") or "").strip(), None)

def transcribe_audio(input_path: str, language: Optional[str] = "ru") -> str:
    wav = f"{uuid.uuid4()}.wav"
    try:
        subprocess.run(
            ["ffmpeg","-i",input_path,"-ar","16000","-ac","1","-c:a","pcm_s16le",wav],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )

        # --- выбор бэкенда с авто-фолбэком ---
        if ASR_BACKEND == "openai" and oai:
            try:
                text, detected = _oai_transcribe(wav, language)
            except Exception as e:
                # тихо логируем и падаем на локальный faster-whisper
                print(f"[ASR] OpenAI failed: {e}. Falling back to local faster-whisper.")
                text, detected = _fw_transcribe(wav, language)
        else:
            text, detected = _fw_transcribe(wav, language)
        # --- конец выбора бэкенда ---

        if not text:
            return "⚠️ Не удалось распознать речь. Попробуйте ещё раз."

        # Для видео (language=None): если не RU — переводим офлайн в RU
        if language is None and (detected and detected != "ru"):
            try:
                return (_translate_to_ru(text, detected) or text).strip()
            except Exception:
                return text
        return text
    except Exception as e:
        return f"❌ Ошибка при распознавании: {e}"
    finally:
        try: os.remove(wav)
        except: pass
