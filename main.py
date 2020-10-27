import asyncio
import concurrent.futures
import time
from functools import lru_cache

import cv2
import discord
import requests

from overlay import Overlay
from overlay_monitor import active_speaker_indices

TOKEN = 'Mjg1ODg0OTgwNjQxNjYwOTI5.X5gJnw.GeideTTZykXP0vuioYgo5kTLGA0'
GUILD = 'Test' # guild where the voice channel that will be checked is (it could be better to check in which guild
# the user is in a voice_channel as he only can be in one
DELAY = 4 # delay between updating the global variables by the discord_client_loop

class MyClient(discord.Client):

    def _voice_channel_members(self):
        # returns the voice channel members of the voice channel the user is in in the GUILD
        guild = next(guild for guild in self.guilds if guild.name == GUILD)
        me_as_member = guild.get_member(self.user.id)
        voice_channel = me_as_member.voice.channel
        return voice_channel.members
        # return [guild.get_member(id) for id in voice_channel.voice_states.keys()]

    def voice_channel_member_names(self):
        return [member.name for member in self._voice_channel_members()]

    def voice_channel_member_avatars(self):
        results = []
        avatar_urls = [member.avatar_url for member in self._voice_channel_members()]
        for url in avatar_urls:
            img = download_avatar_img(url)
            results.append(img)
        return results

    async def on_voice_state_update(self, member, before, after):
        global names, speaker_indices, _last_update_time

        if quit:
            raise KeyboardInterrupt('quitting')

        now = time.time()
        if (now - _last_update_time) < DELAY:
            return
        _last_update_time = now

        names = self.voice_channel_member_names()
        speaker_indices = active_speaker_indices(self.voice_channel_member_avatars())


@lru_cache(20)
def download_avatar_img(url):
    avatar_file_name = 'avatar.png'
    with requests.get(url) as r:
        with open(avatar_file_name, 'wb') as f:
            f.write(r.content)
    img = cv2.imread(avatar_file_name)
    return img


# global variables for communication between threads
quit = False
names = []
speaker_indices = []
_last_update_time = time.time() - DELAY


def discord_client_loop():
    intents = discord.Intents.default()
    intents.members = True
    discord_client = MyClient(intents=intents)

    discord_client_loop = asyncio.get_event_loop()
    discord_client_loop.create_task(discord_client.start(TOKEN, bot=False))
    return discord_client_loop


def main_loop():
    while not quit:
        print(names, speaker_indices)
        time.sleep(2)


def setup():
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
    future1 = executor.submit(main_loop)
    future2 = executor.submit(discord_client_loop().run_forever())
    
    # main thread must be doing "work" to be able to catch a Ctrl+C 
    while not future1.done() and future2.done():
        time.sleep(1)

        
if __name__ == '__main__':
    try:
        setup()
    except KeyboardInterrupt:
        quit = True
