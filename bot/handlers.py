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
    await message.answer("🔄 Распознаю голос...")

    # Обработка в фоне
    loop = asyncio.get_running_loop()
    text = await loop.run_in_executor(executor, transcribe_audio, file_name)

    os.remove(file_name)
    await message.answer(f"🗣 Расшифровка:\n{text}")


def register_handlers(dispatcher):
    dispatcher.include_router(router)
