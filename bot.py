import os
import sys
import instaloader
from pathlib import Path
import shutil
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import TelegramError
import asyncio

class InstagramDownloaderBot:
    def __init__(self):
        self.L = instaloader.Instaloader(
            quiet=True,
            download_pictures=True,
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False
        )
        self.DOWNLOAD_DIR = "downloads"

    def clear_directory(self, directory_path):
        folder_path = Path(directory_path)
        if not folder_path.exists():
            os.makedirs(directory_path, exist_ok=True)
            return

        try:
            for item in folder_path.iterdir():
                if item.is_file() or item.is_symlink():
                    item.unlink()  
                elif item.is_dir():
                    shutil.rmtree(item)  
        except Exception as e:
            print("Failed to clear directory:", e)

    def normalize_instagram_url(self, url):
        url = url.split("?")[0]  
        url = url.replace("reels/", "reel/")  
        return url.strip()

    def download_instagram_post(self, post_url):
        try:
            post_url = self.normalize_instagram_url(post_url)  
            shortcode = post_url.split("/")[-2]  
            print(f"Downloading content from shortcode: {shortcode}")

            self.clear_directory(self.DOWNLOAD_DIR)

            post = instaloader.Post.from_shortcode(self.L.context, shortcode)
            self.L.download_post(post, target=self.DOWNLOAD_DIR)
            print(f"Content downloaded to {self.DOWNLOAD_DIR}")

            return True
        except Exception as e:
            print(f"Error loading content: {e}")
            return False

    def find_downloaded_files(self, directory_path):
        files = []
        for file_name in os.listdir(directory_path):
            if file_name.lower().endswith((".jpg", ".mp4")):
                files.append(os.path.join(directory_path, file_name))
        return files

    async def send_to_telegram(self, bot, chat_id, files):
        for file_path in files:
            try:
                if file_path.endswith('.mp4'):
                    with open(file_path, 'rb') as video_file:
                        await bot.send_video(chat_id=chat_id, video=video_file)
                elif file_path.endswith('.jpg'):
                    with open(file_path, 'rb') as photo_file:
                        await bot.send_photo(chat_id=chat_id, photo=photo_file)
                print(f"Successfully sent {file_path}")
                os.remove(file_path)
            except TelegramError as e:
                print(f"Failed to send {file_path}: {e}")
            except Exception as e:
                print(f"Unexpected error with {file_path}: {e}")

    async def process_url(self, url, bot, chat_id):
        if not url:
            return "Пожалуйста, отправьте действительную ссылку Instagram"
        
        if "instagram.com/p/" not in url and "instagram.com/reel/" not in url:
            return "Неверная ссылка Instagram. Отправьте ссылку на пост или рил."

        success = self.download_instagram_post(url)
        if not success:
            return "Не удалось загрузить контент из Instagram"

        files = self.find_downloaded_files(self.DOWNLOAD_DIR)
        if not files:
            return "Не найдены медиафайлы после загрузки"

        await self.send_to_telegram(bot, chat_id, files)
        return "Контент успешно отправлен!"

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            "Привет! Отправь мне ссылку на пост или рил из Instagram, и я пришлю тебе его содержимое."
        )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        url = update.message.text
        await update.message.reply_text("Начинаю загрузку...")

        result = await self.process_url(url, context.bot, update.message.chat_id)
        await update.message.reply_text(result)

    def run_bot(self, token):
        application = Application.builder().token(token).build()

        application.add_handler(CommandHandler("start", self.start))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

        print("Бот запущен и готов принимать сообщения от всех пользователей...")
        application.run_polling()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python instagram_bot.py <TELEGRAM_BOT_TOKEN>")
        sys.exit(1)

    bot_token = sys.argv[1]
    downloader_bot = InstagramDownloaderBot()
    downloader_bot.run_bot(bot_token)