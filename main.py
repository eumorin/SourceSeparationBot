import logging
from pathlib import Path
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import filters, MessageHandler, ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler
import torchaudio
from openunmix import predict

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def separate_audio(input_file, output_dir, track_type):
    audio, rate = torchaudio.load(input_file)
    if rate != 44100:
        resample = torchaudio.transforms.Resample(orig_freq=rate, new_freq=44100)
        audio = resample(audio)
    estimates = predict.separate(audio=audio, rate=44100)
    estimate = estimates[track_type]
    print(estimate)
    output_file = Path.joinpath(output_dir, f"{track_type}.mp3")
    torchaudio.save(output_file, estimate[0], 44100)
    print('Дорожки разделены')
    return output_file


async def handle_audio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    audio = update.message.audio
    file = await audio.get_file()
    print('файл успешно получен')
    original_filename = audio.file_name if audio.file_name else f"{file.file_id}"

    input_path = Path('C:/Users/ethernetcake/PycharmProjects/ssm_bot/input_storage')
    if not input_path.exists():
        os.makedirs(input_path)
    file_path = Path.joinpath(input_path, f'{original_filename}')
    await file.download_to_drive(custom_path=file_path)
    print("файл успешно загружен")

    context.user_data['audio_file_path'] = file_path
    print(context.user_data)

    keyboard = [
        [InlineKeyboardButton("Аудио вокала", callback_data='vocals')],
        [InlineKeyboardButton("Аудио трека без вокала", callback_data='drums')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выбери, что хочешь получить:', reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    track_type = query.data

    await query.edit_message_text(text=f"Выбранный вариант: {track_type}")

    input_file_path = context.user_data.get('audio_file_path', None)
    if input_file_path is None:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Не найден аудиофайл для обработки.")
        return

    output_path = Path('C:/Users/ethernetcake/PycharmProjects/ssm_bot/output_storage')
    if not output_path.exists():
        os.makedirs(output_path)
    output_file = separate_audio(input_file_path, output_path, track_type)
    await context.bot.send_audio(chat_id=update.effective_chat.id, audio=open(output_file, 'rb'))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Отправь мне аудио трек, и я помогу разделить его на компоненты.")


if __name__ == '__main__':
    app = ApplicationBuilder().token('6983757573:AAENUdVZxVE2yp-MCb6LhGlR744YxGFcOAQ').build()

    start_handler = CommandHandler('start', start)
    audio_handler = MessageHandler(filters.AUDIO & (~filters.COMMAND), handle_audio)
    button_handler = CallbackQueryHandler(button)

    app.add_handler(start_handler)
    app.add_handler(audio_handler)
    app.add_handler(button_handler)

    app.run_polling()