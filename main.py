import yaml
import asyncio
import simplematrixbotlib as botlib
import requests.utils
import yt_dlp
from urllib.parse import urlparse
import json


config = botlib.Config()
config.encryption_enabled = True 
config.emoji_verify = True
config.ignore_unverified_devices = True
#config.store_path = "./crypto_store"

with open("config.yaml", "r") as yamlfile:
    config = yaml.load(yamlfile, Loader=yaml.Loader)

creds = botlib.Creds(
    homeserver=config["homeserver"],
    username=config["username"],
    password=config["password"],
    session_stored_file="./store/session.txt")
bot = botlib.Bot(creds)
PREFIX = config["prefix"]


class SongLink():
    def __init__(self):
        self.api_base = 'https://api.song.link/v1-alpha.1/links?url='
        self.country_code = '&userCountry=US'
    async def get_link(self, url):
        link = self.api_base + url + self.country_code
        url_encoded = requests.utils.requote_uri(link)
        request = requests.get(url_encoded)
        data = request.json()
        #print(json.dumps(data, indent=4))
        songlink = str(data['pageUrl'])

        return songlink


async def return_url(message):
    accepted_links = [
        'youtube.com', 'youtu.be', 'play.google.com/music',
        'soundcloud.com', 'spotify.com', 'music.apple.com'
    ]
    text = message
    urls = []

    print(f"text: {text}")

    for i in accepted_links:
        if i in text:
            print("Yep, that's an acceptable link in the message")
            # Find URL
            # Split the string into words
            words = text.split()
            
            # Extract URLs from the words using urlparse()
            for word in words:
                parsed = urlparse(word)
                if parsed.scheme and parsed.netloc:
                    urls.append(word)
            
            # Return the extracted URLs
            return urls
    # This should return []
    return urls

                
@bot.listener.on_message_event
async def return_songlink(room, message):
    match = botlib.MessageMatch(room, message, bot, PREFIX)

    if match.is_not_from_this_bot():
        try:
            if "http" in message.body:
                # Check if it's a music link
                urls = await return_url(message.body)
                print(f"urls: {urls}")
                
                # If there's only one URL, no need to loop
                if len(urls) == 1:
                    text = await SongLink().get_link(url = urls[0])
                    await bot.api.send_text_message(
                        room.room_id, text
                    )
                # If there's more than one URL, we need to loop
                else:
                    # Create message with multiple links
                    text = "Song.link URLs:<br/><ol>"

                    for i in urls:
                        text += f"<li><p>{await SongLink().get_link(url = i)}</p></li>"

                    text += "</ol>"

                    await bot.api.send_markdown_message(
                        room.room_id, text
                    )
        except Exception as e:
            print(f"Exception: {e}")


bot.run()
