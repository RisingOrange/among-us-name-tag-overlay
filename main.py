import asyncio
import multiprocessing as mp
from functools import lru_cache

import cv2
import discord
import keyboard
import requests
import wx

from discord_overlay_monitor import active_speaker_indices
from game_meeting_screen import slot_rect_by_idx, name_tag_slot_at
from name_tag import NameTag

TOKEN = 'Mjg1ODg0OTgwNjQxNjYwOTI5.X5gJnw.GeideTTZykXP0vuioYgo5kTLGA0'
# guild where the voice channel that will be checked is (it could be better to check in which guild

# the user is in a voice_channel as he only can be in one
DISCORD_LOOP_DELAY = 1  # seconds between updating the global variables by the discord_client_loop
GUI_LOOP_DELAY = 0.1 # seconds between running gui updates based on the data
PAUSE_HOTKEY = 'ctrl+<'


EVERYONE_ALWAYS_SPEAKS_TEST_MODE = False


class DicordClient(discord.Client):
    # connects to discord and updates the app state every DELAY seconds

    def __init__(self, *args, state=None, **dargs):
        assert state is not None
        self.state = state

        super().__init__(*args, **dargs)

        self._last_recent_channel = None

        self.loop.create_task(self.main())

    def _voice_channel_members(self):
        # returns the voice channel members of the voice channel the user is in in the GUILD

        # first check if self.user stayed in the same voice_channel
        if (self._last_recent_channel is not None and 
            self.user.id in [m.id for m in self._last_recent_channel.members]):
            return self._last_recent_channel.members

        # ... else search all visivle voice_channels in all visible guilds
        for guild in self.guilds:
            for channel in guild.voice_channels:
                for member in channel.members:
                    if member.id == self.user.id:
                        return channel.members
        return []

    def _voice_channel_member_names(self):
        return [member.name for member in self._voice_channel_members()]

    def _voice_channel_member_avatars(self):
        results = []
        avatar_urls = [
            member.avatar_url for member in self._voice_channel_members()]
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
            self.state['speaker_indices'] = active_speaker_indices(
                self._voice_channel_member_avatars())

            await asyncio.sleep(DISCORD_LOOP_DELAY)


@lru_cache(20)
def download_avatar_img(url):
    avatar_file_name = 'avatar.png'
    with requests.get(url) as r:
        with open(avatar_file_name, 'wb') as f:
            f.write(r.content)
    img = cv2.imread(avatar_file_name)
    return img


def run_dicord_client(state):
    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True
    discord_client = DicordClient(intents=intents, state=state)

    discord_client.run(TOKEN, bot=False)


class GuiRoot(wx.Frame):

    # sentinel value to signal that a slot contains multiple names
    MULTIPLE_NAMES = object()

    # root gui element that is invisible and controls the NameOverlays
    def __init__(self, state):
        wx.Frame.__init__(self, None)

        self.state = state

        self._name_tags_by_name = dict()

        self._main()

    def _main(self):

        if keyboard.is_pressed(PAUSE_HOTKEY):
            self.state['pause'] = not self.state['pause']
            print('pause = ', self.state['pause'])

            if self.state['pause']:
                for element in self._name_tags_by_name.values():
                    element.Hide()
            else:
                for element in self._name_tags_by_name.values():
                    element.Show()

        if not self.state['pause']:
            self._update_name_tags()

        if not self.state['quit']:
            wx.CallLater(GUI_LOOP_DELAY*1000, self._main)
        else:
            wx.Exit()    
    
    def _names_by_slot(self):
        result = dict()
        for name, tag in self._name_tags_by_name.items():
            slot = name_tag_slot_at(tag.GetPosition())
            if slot is None:
                continue
            if result.get(slot, None) is None:
                result[slot] = name
            else:
                result[slot] = self.MULTIPLE_NAMES
        return result

        

    def _update_name_tags(self):
        self._update_name_tag_presences()
        self._update_name_tag_highlight_states()
        self._snap_name_tags_to_slots()

    def _snap_name_tags_to_slots(self):
        # set the position of nametags that are alone in their slot to the slot center
        for slot, name in self._names_by_slot().items():
            if name is self.MULTIPLE_NAMES:
                continue
            name_tag = self._name_tags_by_name[name]
            x, y, w, h = slot_rect_by_idx()[slot]
            snap_pos = (
                x + w // 2 - 100,
                y + h // 2
            )
            name_tag.SetPosition(snap_pos)


    def _update_name_tag_presences(self):
        prev_names = list(self._name_tags_by_name.keys())

        # add, remove overlays based on names
        if set(self.state['names']) != set(self._name_tags_by_name.keys()):
            # add overlays for new names
            new_names = set(self.state['names']) - set(prev_names)
            for name in new_names:
                self._name_tags_by_name[name] = NameTag(text=name)

            # remove overlays for gone names
            gone_names = set(prev_names) - set(self.state['names'])
            for name in gone_names:
                self._name_tags_by_name[name].Close()
                del self._name_tags_by_name[name]

    def _update_name_tag_highlight_states(self):
        speaker_names = self._speaker_names()
        non_speaker_names = set(
            self._name_tags_by_name.keys()) - set(speaker_names)
        for name in speaker_names:
            self._name_tags_by_name[name].highlight()
        for name in non_speaker_names:
            self._name_tags_by_name[name].dehighlight()

    def _speaker_names(self):
        if EVERYONE_ALWAYS_SPEAKS_TEST_MODE:
            return self.state['names']
        return [self.state['names'][speaker_idx] for speaker_idx in self.state['speaker_indices']]


def run_gui(state):
    app = wx.App()
    GuiRoot(state)
    app.MainLoop()


def setup(state):

    jobs = [
        mp.Process(target=run_gui, args=(state,)),
        mp.Process(target=run_dicord_client, args=(state,)),
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
