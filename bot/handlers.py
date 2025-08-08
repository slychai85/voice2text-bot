import os
import uuid
import asyncio
from aiogram import Router
from aiogram.types import Message
from bot.transcriber import transcribe_audio
from concurrent.futures import ThreadPoolExecutor

router = Router()
executor = ThreadPoolExecutor()

@router.message(lambda msg: msg.voice)
async def handle_voice(message: Message):
    file_id = message.voice.file_id
    file_info = await message.bot.get_file(file_id)
    file_path = file_info.file_path
    file_name = f"{uuid.uuid4()}.oga"

    # Скачиваем голосовое
    await message.bot.download_file(file_path, destination=file_name)
    processing_msg = await message.answer("🔄 Распознаю голос...")

    # Обработка в фоне
    text = await asyncio.to_thread(transcribe_audio, file_name)
    
    # Удаляем временный файл
    if os.path.exists(file_name):
        os.remove(file_name)

    # Удаляем сообщение о процессе
    await processing_msg.delete()

    # Отправляем результат
    await message.answer(f"🗣 Расшифровка:\n{text}")

def register_handlers(dispatcher):
    dispatcher.include_router(router)
