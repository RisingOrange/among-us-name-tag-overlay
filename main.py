import asyncio
import concurrent.futures
import time
from functools import lru_cache

import cv2
import discord
import requests
import wx

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

        print(speaker_indices)


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


class Overlay(wx.Frame):
    def __init__(self, *args, text=None, **dargs):
        assert text is not None

        style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR |
                  wx.NO_BORDER | wx.FRAME_SHAPED  )
        wx.Frame.__init__(self, None, *args, **dargs, style=style)
        self.Bind(wx.EVT_MOTION, self.on_mouse)
        self.SetTransparent(220)

        # put some text with a larger bold font on it
        self.st = wx.StaticText(self, label=text)
        font = self.st.GetFont()
        font.PointSize += 5
        font = font.Bold()
        self.st.SetFont(font)
        
        # resize frame to size of the text
        frame_size = self.st.GetSize()
        self.SetSize(frame_size)

        # make the frame draggable by the text
        self.st.Bind(wx.EVT_MOTION, self.on_mouse)

        self.Show(True)

    def highlight(self):
        self.st.SetForegroundColour((15, 255, 63))

    def dehighlight(self):
        self.st.SetForegroundColour((0, 0, 0))

    def on_mouse(self, event):
        """implement dragging"""
        if not event.Dragging():
            self._dragPos = None
            return
        if not self._dragPos:
            self._dragPos = event.GetPosition()
        else:
            pos = event.GetPosition()
            displacement = self._dragPos - pos
            self.SetPosition( self.GetPosition() - displacement )


class Root(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None)
        
        self.overlays_by_name = dict()
        self.active_speakers = []
        self.on_timer()

    def on_timer(self):

        self.overlays_update_add_remove()
        self.overlays_update_highlights()
            
        if not quit:
            wx.CallLater(2000, self.on_timer)
        else:
            wx.Exit()

    def overlays_update_highlights(self):
        speaker_names = [names[speaker_idx] for speaker_idx in speaker_indices]
        non_speaker_names = set(self.overlays_by_name.keys()) - set(speaker_names)
        for name in speaker_names:
            self.overlays_by_name[name].highlight()
        for name in non_speaker_names:
            self.overlays_by_name[name].dehighlight()

    def overlays_update_add_remove(self):
        prev_names = list(self.overlays_by_name.keys())

        # add, remove overlays based on names
        if set(names) != set(self.overlays_by_name.keys()):
            # add overlays for new names
            new_names = set(names) - set(prev_names)
            for name in new_names:
                self.overlays_by_name[name] = Overlay(text=name)

            # remove overlays for gone names
            gone_names = set(prev_names) - set(names)
            for name in gone_names:
                self.overlays_by_name[name].Close()
                del self.overlays_by_name[name]


def gui_loop():
    app = wx.App()
    root = Root()
    app.MainLoop()


def setup():
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=3)
    future1 = executor.submit(gui_loop)
    future2 = executor.submit(discord_client_loop().run_forever())
    
    # main thread must be doing "work" to be able to catch a Ctrl+C 
    while not future1.done() and future2.done():
        time.sleep(1)

        
if __name__ == '__main__':
    try:
        setup()
    except KeyboardInterrupt:
        quit = True
