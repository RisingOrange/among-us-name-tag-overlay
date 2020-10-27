import asyncio
import time

import cv2
import discord
import requests

from overlay_monitor import active_speaker_indices
from text_overlay import XOverlay

TOKEN = 'Mjg1ODg0OTgwNjQxNjYwOTI5.X5gJnw.GeideTTZykXP0vuioYgo5kTLGA0'
GUILD = 'Test'
DELAY = 2 # delay between updating everything

class MyClient(discord.Client):

    # async def on_message(self, message):
    #     if message.content == 'ping':
    #         await message.channel.send('pong')

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
            avatar_file_name = 'avatar.png'
            with requests.get(url) as r:
                with open(avatar_file_name, 'wb') as f:
                    f.write(r.content)
            img = cv2.imread(avatar_file_name)
            results.append(img)
        return results

    # async def on_voice_state_update(self, member, before, after):
    #     pass

def speaker_overlays(speaker_indices):
    results = []
    for speaker_idx in speaker_indices:
        results.append(XOverlay(50, 30 + 20 * speaker_idx))
    return results


def main():

    intents = discord.Intents.default()
    intents.members = True
    client = MyClient(intents=intents)

    async def my_background_task():
        await client.wait_until_ready()

        overlays = []
        while True:
            for overlay in overlays:
                overlay.hide()

            avatars = client.voice_channel_member_avatars()
            overlays = speaker_overlays(active_speaker_indices(avatars))

            await asyncio.sleep(DELAY)

    client.loop.create_task(my_background_task())
    client.run(TOKEN, bot=False)
    
if __name__ == '__main__':
    main()