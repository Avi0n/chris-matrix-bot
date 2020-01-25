from __future__ import unicode_literals
from dotenv import load_dotenv
from time import sleep
from telegram.ext import (MessageHandler, CommandHandler, BaseFilter, Updater)
import os
import logging
import youtube_dl
import requests


# Initialize dotenv
load_dotenv()

mp3_name = ''
songlink_url = ''

# Initialize logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


# Find YouTube/Soundcloud link from song.link URLs
def get_song_download_url(url):
    youtube_url = ''
    soundcloud_url = ''
    global songlink_url
    global song_title

    API_URL = "https://api.song.link/v1-alpha.1/links?"

    data = {
        "url": url,
        "userCountry": "US"
    }

    response = requests.get(API_URL, data)
    json_data = response.json()

    try:
        youtube_url = json_data['linksByPlatform']['youtube']['url']
        soundcloud_url = json_data['linksByPlatform']['soundcloud']['url']
        songlink_url = json_data['pageUrl']
        song_title = list(json_data['entitiesByUniqueId'].values())[0]['title']
    except:
        print('YouTube or Soundcloud link not found')

    if youtube_url is not None:
        print(youtube_url)
        return youtube_url
    elif soundcloud_url is not None:
        print(soundcloud_url)
        return soundcloud_url
    else:
        print("Couldn't find a YouTube/Soundcloud URL to download from")
    return


# Respond to /start
def start(context, update):
    context.bot.send_message(chat_id=update.message.chat_id,
                             text="This bot can send you .mp3's of videos.")


# YouTube-dl stuff
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
    global mp3_name

    ydl_opts = {
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
        ydl.download(['https://www.youtube.com/watch?v=BaW_jenozKc'])

    print('Downloading video and/or audio')
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Find filename of converted audio
    for fname in os.listdir('.'):
        if fname.endswith('.mp3'):
            os.rename(fname, song_title + '.mp3')
            mp3_name = song_title + '.mp3'
            break


def delete_audio():
    # Cleanup downloaded media
    for fname in os.listdir('.'):
        if fname.endswith('.mp3'):
            os.remove(fname)

# End of YouTube-dl stuff


def check_message_for_link(update, context):
    # Assign link in message or sticker to a variable
    media_url = ''

    if update.message.text is not None:
        media_url = get_song_download_url(update.message.text)
        print(media_url)

    # Download video/audio and covert to mp3
    try:
        print('download function url: ' + media_url)
        download_audio(media_url)
        # Try to send telegram message with audio file. If error, try again in 5 sec.
        i = 0
        error = ''
        while i < 5:
            i += 1
            try:
                print(mp3_name)
                context.bot.send_audio(chat_id=update.message.chat_id, audio=open(
                    './' + mp3_name, 'rb'), disable_notification=True,
                    caption='[Song.link URL](' + songlink_url + ')',
                    parse_mode='Markdown', timeout=20)
                print('Telegram message sent!')
                break
            except Exception as e:
                error = str(e)
                print('Exception: ' + str(e) + '. Trying again in 5 seconds')
                sleep(5)
                continue
        if i == 5:
            context.bot.send_message(
                chat_id=update.message.chat_id, text=error, disable_notification=True)
    except Exception as e:
        print('Exception: ' + str(e))
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text="Couldn't find a YouTube/Soundcloud URL to download from.")

    # All done! Delete audio file.
    delete_audio()


class FilterLinks(BaseFilter):
    def filter(self, message):
        accepted_links = [
            'youtube.com',
            'youtu.be',
            'play.google.com/music',
            'soundcloud.com',
            'spotify.com',
            'music.apple.com',
            'coub.com',
            'song.link'
        ]
        media_url = message.text

        for i in accepted_links:
            if i in media_url:
                print("Yep, that's an acceptable link in the message")
                return True


def main():
    # Initialize link filter class
    filter_links = FilterLinks()

    # Set Chris bot token
    updater = Updater(os.getenv('TEL_BOT_TOKEN'), use_context=True)

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
