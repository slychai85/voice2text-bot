import os
import asyncio
import tempfile
from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType
from bot.transcriber import transcribe_audio

MAX_TG_LEN = 4096
SAFE_LEN = 3500  # оставим запас под заголовки/эмодзи

def _chunk_text(text: str, size: int = SAFE_LEN):
    text = text.strip()
    chunks = []
    while text:
        cut = text.rfind("\n", 0, size)
        if cut == -1:
            cut = text.rfind(" ", 0, size)
        if cut == -1:
            cut = min(len(text), size)
        chunks.append(text[:cut].strip())
        text = text[cut:].lstrip()
    return chunks

async def _send_long_text(message, text: str, header: str | None = None):
    if header:
        text = f"{header}\n{text}"
    if len(text) <= MAX_TG_LEN:
        await message.answer(text)
        return
    for part in _chunk_text(text):
        await message.answer(part)

router = Router()

# лимит размера файла для скачивания (байты). 19 МБ — запас под лимит Telegram.
MAX_FILE_SIZE = 19 * 1024 * 1024


async def _download_to_tempfile(message: Message, file_id: str, suffix: str) -> str:
    """Скачивает файл во временный путь и возвращает путь. Выбрасывает исключение если файл велик."""
    file_info = await message.bot.get_file(file_id)

    # у некоторых типов есть file_size в самом объекте, но надёжнее проверить info
    if getattr(file_info, "file_size", None) and file_info.file_size > MAX_FILE_SIZE:
        raise ValueError("Файл слишком большой для скачивания ботом")

    # создаём временный файл вне репозитория
    fd, temp_path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)  # нам нужен только путь

    await message.bot.download_file(file_info.file_path, destination=temp_path)
    return temp_path


@router.message(F.voice)
async def handle_voice(message: Message):
    processing_msg = await message.answer("🔄 Распознаю голос...")

    local_path = None
    try:
        local_path = await _download_to_tempfile(message, message.voice.file_id, suffix=".oga")
        # для голосовых фиксируем русский — лучшая точность
        text = await asyncio.to_thread(transcribe_audio, local_path, "ru")
        await processing_msg.delete()
        await _send_long_text(message, text, "🗣 Расшифровка:")
    except ValueError as e:
        await processing_msg.delete()
        await message.answer(f"⚠️ {e}. Отправь, пожалуйста, более короткое голосовое.")
    except Exception as e:
        # на всякий случай не падаем молча
        try:
            await processing_msg.delete()
        except Exception:
            pass
        await message.answer(f"❌ Ошибка при обработке: {e}")
    finally:
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass


# Видео — ТОЛЬКО в личке. В группах игнорируем.
@router.message(
    (F.chat.type == ChatType.PRIVATE)
    & (F.video | (F.document & F.document.mime_type.startswith("video/")))
)
async def handle_video_private(message: Message):
    processing_msg = await message.answer("🎞 Извлекаю аудио и распознаю речь...")

    # берём объект видео/документа и проверяем размер заранее
    file_obj = message.video or message.document
    if getattr(file_obj, "file_size", 0) > MAX_FILE_SIZE:
        await processing_msg.delete()
        await message.answer("⚠️ Видео слишком большое. Отправь файл до 19 МБ или укороти ролик.")
        return

    local_path = None
    try:
        local_path = await _download_to_tempfile(message, file_obj.file_id, suffix=".mp4")
        # для видео — автоопределение языка; если не ru, переводим в transcriber (если настроен)
        text = await asyncio.to_thread(transcribe_audio, local_path, None)
        await processing_msg.delete()
        await _send_long_text(message, text, "🗣 Расшифровка из видео:")
    except ValueError as e:
        await processing_msg.delete()
        await message.answer(f"⚠️ {e}. Сожми видео или пришли короче 19 МБ.")
    except Exception as e:
        try:
            await processing_msg.delete()
        except Exception:
            pass
        await message.answer(f"❌ Ошибка при обработке видео: {e}")
    finally:
        if local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass


def register_handlers(dispatcher):
    dispatcher.include_router(router)
