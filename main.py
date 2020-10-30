import asyncio
import multiprocessing as mp
from functools import lru_cache
from shaped_image import ShapedImage

import cv2
import discord
import keyboard
import requests
import wx

from discord_overlay_monitor import active_speaker_indices
from game_meeting_screen import name_tag_slot_at, mouth_pos_for_slot
from name_tag import NameTag

TOKEN = 'Mjg1ODg0OTgwNjQxNjYwOTI5.X5gJnw.GeideTTZykXP0vuioYgo5kTLGA0'
# guild where the voice channel that will be checked is (it could be better to check in which guild
GUILD = 'Test'
# the user is in a voice_channel as he only can be in one
DELAY = 1  # delay between updating the global variables by the discord_client_loop
PAUSE_HOTKEY = 'ctrl+<'


class DicordClient(discord.Client):
    # connects to discord and updates the app state every DELAY seconds

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


def run_dicord_client(state):
    intents = discord.Intents.default()
    intents.members = True
    discord_client = DicordClient(intents=intents, state=state)

    discord_client.run(TOKEN, bot=False)


class GuiRoot(wx.Frame):

    MULTIPLE_NAMES = object()

    # root gui element that is invisible and controls the NameOverlays
    def __init__(self, state):
        wx.Frame.__init__(self, None)

        self.state = state

        self._name_tags_by_name = dict()
        self._mouths_by_name = dict()

        self._main()

    def _main(self):

        if keyboard.is_pressed(PAUSE_HOTKEY):
            self.state['pause'] = not self.state['pause']
            print('pause = ', self.state['pause'])

            if self.state['pause']:
                for overlay in self._name_tags_by_name.values():
                    overlay.Hide()
            else:
                for overlay in self._name_tags_by_name.values():
                    overlay.Show()

        if not self.state['pause']:
            self._update_name_tags()
            self._update_mouths()

        if not self.state['quit']:
            # Call main again in 0.5 seconds
            wx.CallLater(500, self._main)
        else:
            wx.Exit()

    def _update_mouths(self):
        self._update_mouth_presence()  
        self._update_mouth_visibility_and_positions()
          
    
    def _update_mouth_visibility_and_positions(self):
        
        # show mouths next to name tags that contain one name tag of which the corresponding persons speaks
        shown_mouths = set()
        for slot, name in self._name_by_slot().items():
            if name is self.MULTIPLE_NAMES or name not in self._speaker_names():
                continue

            mouth = self._mouths_by_name[name]

            mouth.SetPosition(mouth_pos_for_slot(slot))
            mouth.Show()
            shown_mouths.add(mouth)

        # hide other mouths
        mouths_to_hide = set(self._mouths_by_name.values()) - shown_mouths
        for mouth in mouths_to_hide:
            mouth.Hide()

    def _update_mouth_presence(self):
        prev_names = list(self._mouths_by_name.keys())

        # add, remove mouths based on names
        if set(self.state['names']) != set(self._mouths_by_name.keys()):
            # add mouths for new names
            new_names = set(self.state['names']) - set(prev_names)
            for name in new_names:
                mouth = ShapedImage(None, 'images/mouth.png', (0, 0))
                mouth.Hide()
                self._mouths_by_name[name] = mouth
                

            # remove mouths for gone names
            gone_names = set(prev_names) - set(self.state['names'])
            for name in gone_names:
                self._mouths_by_name[name].Destroy()
                del self._mouths_by_name[name]
            

    def _name_by_slot(self):
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
        return [self.state['names'][speaker_idx] for speaker_idx in self.state['speaker_indices']]


def run_gui(state):
    app = wx.App()
    root = GuiRoot(state)
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
