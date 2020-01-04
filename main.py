from __future__ import unicode_literals
from dotenv import load_dotenv
from bs4 import BeautifulSoup
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
def scrape_songlink(url):
    global songlink_url

    headers = {'User-Agent': 'Mozilla/5.0'}

    # Returns a requests.models.Response object
    page = requests.get(url, headers=headers)

    songlink_url = url

    soup = BeautifulSoup(page.text, 'html.parser')

    # Find all links
    link_found = False
    while link_found is False:
        for link in soup.find_all('a'):
            if 'youtube.com' in link.get('href'):
                print(link.get('href'))
                return link.get('href')
            elif 'soundcloud.com' in link.get('href'):
                print(link.get('href'))
                return link.get('href')
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

    print('Downloading video and/or audio')
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

# End of YouTube-dl stuffError


def check_message_for_link(update, context):
    # Assign link in message or sticker to a variable
    media_url=''

    if not update.message.text is None:
        media_url=update.message.text
        print(media_url)

    # Grab YouTube/Soundcloud link from Song.link if it's a spotify or song.link URL
    if 'spotify.com' in update.message.text:
        print('song.linkifying spotify link')
        media_url=scrape_songlink('https://odesli.co/' + update.message.text)
    elif 'music.apple.com' in update.message.text:
        print('song.linkifying Apple Music link')
        media_url=scrape_songlink('https://odesli.co/' + update.message.text)        
    elif 'song.link' in update.message.text:
        # Grab YouTube/Soundcloud URL from song.link URL
        media_url=scrape_songlink(update.message.text)
    else:
        print('Not a song.link or spotify/apple URL, continuing to download song.')

    # Download video/audio and covert to mp3
    try:
        download_audio(media_url)
        # Get song.link URL
        media_url=scrape_songlink('https://odesli.co/' + update.message.text)
    except Exception as e:
        print('Exception: ' + str(e))
        context.bot.send_message(chat_id=update.message.chat_id,
                    text="Couldn't find a YouTube/Soundcloud URL to download from.")

    # Try to send telegram message with audio file. If error, try again in 5 sec.
    i = 0
    error = ''
    while i < 5:
        i += 1
        try:
            context.bot.send_audio(chat_id=update.message.chat_id, audio=open(
                           './song.mp3', 'rb'), title=mp3_name, disable_notification=True, 
                           caption='[Song.link URL](' + songlink_url + ')', 
                           parse_mode='Markdown', timeout=20)
            print('Telegram message sent!')
            break
        except Exception as e:
            error = str(e)
            print('Exception: ' + str(e) + '. Trying again in 5 seconds')
            sleep(5)
            continue
    if i is 5:
        context.bot.send_message(chat_id=update.message.chat_id, text=error, disable_notification=True)

    # All done! Delete audio file.
    delete_audio()


class FilterLinks(BaseFilter):
    def filter(self, message):
        accepted_links=[
            'youtube.com',
            'youtu.be',
            'soundcloud.com',
            'spotify.com',
            'music.apple.com',
            'coub.com',
            'song.link'
        ]
        media_url=message.text

        for i in accepted_links:
            if i in media_url:
                print("Yep, that's an acceptable link in the message")
                return True


def main():
    # Initialize link filter class
    filter_links=FilterLinks()

    # Set Chris bot token
    updater = Updater(os.getenv('TEL_BOT_TOKEN'), use_context=True)

    dispatcher=updater.dispatcher

    start_handler=CommandHandler('start', start)
    dispatcher.add_handler(start_handler)

    message_handler=MessageHandler(filter_links, check_message_for_link)
    dispatcher.add_handler(message_handler)

    dispatcher.add_error_handler(error)

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
