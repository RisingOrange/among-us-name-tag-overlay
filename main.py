import asyncio
import multiprocessing as mp
from functools import lru_cache

import cv2
import discord
import keyboard
import requests
import wx

from discord_overlay_monitor import active_speaker_indices
from name_overlay import NameOverlay

TOKEN = 'Mjg1ODg0OTgwNjQxNjYwOTI5.X5gJnw.GeideTTZykXP0vuioYgo5kTLGA0'
GUILD = 'Test' # guild where the voice channel that will be checked is (it could be better to check in which guild
# the user is in a voice_channel as he only can be in one
DELAY = 1 # delay between updating the global variables by the discord_client_loop
PAUSE_HOTKEY = 'ctrl+<'


class DicordClient(discord.Client):

    def __init__(self, *args, state=None, **dargs):
        assert state is not None
        self.state = state

        super().__init__(*args, **dargs)

        self.loop.create_task(self.main())

    def _voice_channel_members(self):
        # returns the voice channel members of the voice channel the user is in in the GUILD
        guild = next(guild for guild in self.guilds if guild.name == GUILD)
        me_as_member = guild.get_member(self.user.id)
        voice_channel = me_as_member.voice.channel
        return voice_channel.members

    def _voice_channel_member_names(self):
        return [member.name for member in self._voice_channel_members()]

    def _voice_channel_member_avatars(self):
        results = []
        avatar_urls = [member.avatar_url for member in self._voice_channel_members()]
        for url in avatar_urls:
            img = download_avatar_img(url)
            results.append(img)
        return results

    async def main(self):

        while not self.is_ready():
            await asyncio.sleep(0.5)

        while True:

            if self.state['quit']:
                raise KeyboardInterrupt('quitting')

            if self.state['pause']:
                return

            self.state['names'] = self._voice_channel_member_names()
            self.state['speaker_indices'] = active_speaker_indices(self._voice_channel_member_avatars())

            if self.state['speaker_indices']:
                print(self.state['speaker_indices'])

            await asyncio.sleep(DELAY)


@lru_cache(20)
def download_avatar_img(url):
    avatar_file_name = 'avatar.png'
    with requests.get(url) as r:
        with open(avatar_file_name, 'wb') as f:
            f.write(r.content)
    img = cv2.imread(avatar_file_name)
    return img



def discord_client_loop(state):
    intents = discord.Intents.default()
    intents.members = True
    discord_client = DicordClient(intents=intents, state=state)

    discord_client.run(TOKEN, bot=False)



class Root(wx.Frame):
    # root gui element that is invisible and controls the NameOverlays
    def __init__(self, state):
        wx.Frame.__init__(self, None)

        self.state = state
        
        self.overlays_by_name = dict()
        self.active_speakers = []
        self.on_timer()

    def on_timer(self):

        if keyboard.is_pressed(PAUSE_HOTKEY):
            self.state['pause'] = not self.state['pause']
            print('pause = ', self.state['pause'])
            
            if self.state['pause']:
                for overlay in self.overlays_by_name.values():
                    overlay.Hide()
            else:
                for overlay in self.overlays_by_name.values():
                    overlay.Show()

        if not self.state['pause']:
            self.update_overlay_presences()
            self.update_overlay_highlight_states()
            
        if not self.state['quit']:
            wx.CallLater(500, self.on_timer)
        else:
            wx.Exit()

    def update_overlay_presences(self):
        prev_names = list(self.overlays_by_name.keys())

        # add, remove overlays based on names
        if set(self.state['names']) != set(self.overlays_by_name.keys()):
            # add overlays for new names
            new_names = set(self.state['names']) - set(prev_names)
            for name in new_names:
                self.overlays_by_name[name] = NameOverlay(text=name)

            # remove overlays for gone names
            gone_names = set(prev_names) - set(self.state['names'])
            for name in gone_names:
                self.overlays_by_name[name].Close()
                del self.overlays_by_name[name]

    def update_overlay_highlight_states(self):
        speaker_names = [self.state['names'][speaker_idx] for speaker_idx in self.state['speaker_indices']]
        non_speaker_names = set(self.overlays_by_name.keys()) - set(speaker_names)
        for name in speaker_names:
            self.overlays_by_name[name].highlight()
        for name in non_speaker_names:
            self.overlays_by_name[name].dehighlight()


def gui_loop(state):
    app = wx.App()
    root = Root(state)
    app.MainLoop()


def setup(state):

    jobs = [
        mp.Process(target=gui_loop, args=(state,)),
        mp.Process(target=discord_client_loop, args=(state,)),
    ]

    for job in jobs:
        job.start()

    for job in jobs:
        job.join()


        
if __name__ == '__main__':

    manager = mp.Manager()
    state = manager.dict()
    
    state['quit'] = False
    state['pause'] = False
    state['names'] = []
    state['speaker_indices'] = []
    
    try:
        setup(state)
    except KeyboardInterrupt:
        state['quit'] = True
