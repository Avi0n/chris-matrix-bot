from __future__ import unicode_literals
from dotenv import load_dotenv
from telegram.ext import (MessageHandler, CommandHandler, BaseFilter, Updater)
import os
import logging
import youtube_dl


# Initialize dotenv
load_dotenv()

mp3_name = ''

# Initialize logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

logger = logging.getLogger(__name__)


# Respond to /start
def start(bot, update):
    bot.send_message(chat_id=update.message.chat_id,
                     text="This bot can send you .mp3's of YouTube videos.")


# YouTube-dl stuff
def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)

class MyLogger(object):
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(msg)

def my_hook(d):
    if d['status'] == 'finished':
        print('Done downloading, now converting ...')

def download_audio(url):
    print("entered download_audio()")
    global mp3_name
    ydl_opts = {
        'outtmpl': '%(title)s.%(ext)s',
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'logger': MyLogger(),
        'progress_hooks': [my_hook],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
    
    # Find filename of converted audio
    for fname in os.listdir('.'):
        if fname.endswith('.mp3'):
            mp3_name = fname
            os.rename(fname, 'song.mp3')
            break

def delete_audio():
    # Cleanup downloaded media
    for fname in os.listdir('.'):
        if fname.endswith('.mp3'):
            os.remove(fname)
# End of YouTube-dl stuff


# Telegram bot
class FilterLinks(BaseFilter):
    def filter(self, message):
        accepted_links = [
            "youtube.com",
            "youtu.be",
            "soundcloud.com",
            "song.link"
        ]
        media_url = message.text

        for i in accepted_links:
            if i and 'http' in media_url:
                print("Yep, that's an acceptable link in the message")
                return True


def check_message_for_link(bot, update):
    # Assign link in message or sticker to a variable
    media_url = ""

    if not update.message.text is None:
        media_url = update.message.text
        print(media_url)

    #if update.message.chat.title == "Bot testing" or update.message.chat.title == "Music":
        # If message contains :heart:, add 3 points and forward the message to whoever liked it
    download_audio(media_url)
    bot.send_audio(chat_id=update.message.chat_id, audio=open('./song.mp3', 'rb'), title=mp3_name, timeout=20)
    delete_audio()


def main():
    # Initialize link filter class
    filter_links = FilterLinks()

    # Set Chris bot token
    updater = Updater(token=os.getenv("TEL_BOT_TOKEN"), request_kwargs={
                      'read_timeout': 15, 'connect_timeout': 30})

    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    message_handler = MessageHandler(filter_links, check_message_for_link)
    dispatcher.add_handler(message_handler)

    dispatcher.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
