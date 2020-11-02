import asyncio
import configparser
import multiprocessing as mp
from functools import lru_cache

import cv2
import discord
import keyboard
import requests
import wx

from discord_overlay_monitor import active_speaker_names
from game_meeting_screen import (name_tag_slot_at, ocr_slot_names,
                                 slot_pos_by_idx, slot_rect_by_idx)
from name_tag import NameTag

config = configparser.ConfigParser()
config.read('config.ini')
config = config['DEFAULT']


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

            if not self.state['pause']:

                self.state['names'] = self._voice_channel_member_names()
                self.state['speaker_names'] = active_speaker_names(
                    self._voice_channel_member_names(),
                    self._voice_channel_member_avatars())

                if self.state['speaker_names']:
                    print(self.state['speaker_names'], 'are speaking now')

            await asyncio.sleep(config.getint('DISCORD_LOOP_DELAY_MS') / 1000.0)


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

    discord_client.run(config['DISCORD_TOKEN'], bot=False)


class GuiRoot(wx.Frame):

    # sentinel value to signal that a slot contains multiple names
    MULTIPLE_NAMES = object()

    # root gui element that is invisible and controls the NameOverlays
    def __init__(self, state):
        wx.Frame.__init__(self, None)

        self.state = state

        self._name_tags_by_name = dict()

        self._name_to_slot_idx = dict()
        self._just_created_name_to_slot = False

        self._main()

    def _main(self):

        if keyboard.is_pressed(config['PAUSE_HOTKEY']):
            self.state['pause'] = not self.state['pause']
            print('pause = ', self.state['pause'])

            if self.state['pause']:
                for element in self._name_tags_by_name.values():
                    element.Hide()
            else:
                for element in self._name_tags_by_name.values():
                    element.Show()

        # HACK when I was trying to move the tags right after generating name_to_slot,
        # they sometimes stayed at the same place, that was probably because the generation
        # of the mapping takes some time (ocr) and therefore blocks the gui process
        # to do this the right way, the mappings generation should probably be delegated to another process
        # ... here the mapping is used to move the tags (one iteration after their generation)
        if self._just_created_name_to_slot:
            self._just_created_name_to_slot = False
            self._move_name_tags_to_matching_slots()
        # ... here the mapping is generated
        if keyboard.is_pressed(config['MOVE_TAGS_TO_MATCHING_SLOTS_HOTKEY']):
            self._generate_name_to_slot()

        if not self.state['pause']:
            self._update_name_tags()

        if not self.state['quit']:
            wx.CallLater(config.getint('GUI_LOOP_DELAY_MS'), self._main)
        else:
            wx.Exit()

    def _generate_name_to_slot(self):

        def best_match(name, names, threshold=2):
            score, match = max([
                (match_score(x, name), x)
                for x in names
                if match_score(x, name) >= threshold
            ], default=(None, None))

            if score is None:
                return None
            elif score > 0:
                return match
            else:
                return None

        def match_score(a, b):
            # length of longest common prefix
            i = 0
            while i < min(len(a), len(b)) and a[i] == b[i]:
                i += 1
            return i

        # reset the mapping
        self._name_to_slot_idx = dict()

        # generate new mapping
        print('starting generating mapping of names to slots...')
        slot_names = [name.lower() for name in ocr_slot_names()]
        print('slot_names:', slot_names)

        for name in self._name_tags_by_name.keys():
            match = best_match(name.lower(), slot_names)
            if not match:
                continue
            self._name_to_slot_idx[name] = slot_names.index(match)

        self._just_created_name_to_slot = True

    def _move_name_tags_to_matching_slots(self):
        for name, slot_idx in self._name_to_slot_idx.items():
            slot_position = slot_pos_by_idx(slot_idx)
            self._name_tags_by_name[name].SetPosition(slot_position)

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
        for slot_idx, name in self._names_by_slot().items():
            if name is self.MULTIPLE_NAMES:
                continue
            name_tag = self._name_tags_by_name[name]
            x, y, w, h = slot_rect_by_idx(slot_idx)
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
                # assign name tag to name and move it away from the overlay
                self._name_tags_by_name[name] = NameTag(text=name)
                self._name_tags_by_name[name].SetPosition((300, 0))

            # remove overlays for gone names
            gone_names = set(prev_names) - set(self.state['names'])
            for name in gone_names:
                self._name_tags_by_name[name].Close()
                del self._name_tags_by_name[name]

    def _update_name_tag_highlight_states(self):
        speaker_names = self.state['speaker_names']
        non_speaker_names = set(
            self._name_tags_by_name.keys()) - set(speaker_names)

        for name in speaker_names:
            self._name_tags_by_name[name].highlight()
        for name in non_speaker_names:
            self._name_tags_by_name[name].dehighlight()


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
    state['speaker_names'] = []

    try:
        setup(state)
    except KeyboardInterrupt:
        state['quit'] = True
