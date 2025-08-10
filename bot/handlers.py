import os
import uuid
import asyncio
from aiogram import Router, F
from aiogram.types import Message
from aiogram.enums import ChatType
from bot.transcriber import transcribe_audio

router = Router()

# Голосовые — везде
@router.message(F.voice)
async def handle_voice(message: Message):
    file_info = await message.bot.get_file(message.voice.file_id)
    src_path = file_info.file_path
    local_path = f"{uuid.uuid4()}.oga"

    await message.bot.download_file(src_path, destination=local_path)
    processing_msg = await message.answer("🔄 Распознаю голос...")

    # Для голосовых фиксируем русский — выше точность
    text = await asyncio.to_thread(transcribe_audio, local_path, "ru")

    if os.path.exists(local_path):
        os.remove(local_path)

    await processing_msg.delete()
    await message.answer(f"🗣 Расшифровка:\n{text}")

# Видео — только в ЛИЧКЕ (private). В группах игнорим.
@router.message(
    (F.chat.type == ChatType.PRIVATE) &
    (F.video | (F.document & F.document.mime_type.startswith("video/")))
)
async def handle_video_private(message: Message):
    file = message.video or message.document
    file_info = await message.bot.get_file(file.file_id)
    src_path = file_info.file_path

    local_path = f"{uuid.uuid4()}.mp4"
    await message.bot.download_file(src_path, destination=local_path)

    processing_msg = await message.answer("🎞 Извлекаю аудио и распознаю речь...")

    # Для видео — автоопределение языка
    text = await asyncio.to_thread(transcribe_audio, local_path, None)

    if os.path.exists(local_path):
        os.remove(local_path)

    await processing_msg.delete()
    await message.answer(f"🗣 Расшифровка из видео:\n{text}")

def register_handlers(dispatcher):
    dispatcher.include_router(router)
