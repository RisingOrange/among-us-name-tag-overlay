import asyncio
import configparser
import multiprocessing as mp

import discord
import keyboard
import wx

from discord_overlay_monitor import active_speaker_names
from game_meeting_screen import LEDGE_RECT, GameMeetingScreen
from name_tag import NameTag
from pyinstaller_utils import resource_path
from utils import active_window_title

config = configparser.ConfigParser()
config.read(resource_path('config.ini'))
config = config['DEFAULT']


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

    async def main(self):

        while not self.is_ready():
            await asyncio.sleep(0.5)

        while True:

            if self.state['quit']:
                await self.close()

            if not self.state['pause']:

                self.state['names'] = self._voice_channel_member_names()
                self.state['speaker_names'] = active_speaker_names(
                    self._voice_channel_member_names())

            await asyncio.sleep(config.getint('DISCORD_LOOP_DELAY_MS') / 1000.0)


def run_dicord_client(state):
    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True
    discord_client = DicordClient(intents=intents, state=state)

    discord_client.run(config['DISCORD_TOKEN'], bot=False)


class NameTagController(wx.Frame):

    # sentinel value to signal that a slot contains multiple names
    MULTIPLE_NAMES = object()

    # root gui element that is invisible and controls the NameTags
    def __init__(self, state):
        wx.Frame.__init__(self, None)

        self.state = state

        self.gms = GameMeetingScreen()

        self._just_was_in_meeting = False

        self._name_tags_by_name = dict()

        self._ocrd_name_to_slot_idx = dict()
        self._just_ocrd_name_to_slot = False

        self._name_to_colour = dict()

        keyboard.add_hotkey(config['PAUSE_HOTKEY'], self._on_pause_toggle)
        keyboard.add_hotkey(
            config['ARRANGE_TAGS_USING_OCR_HOTKEY'], self._ocr_name_to_slot_matching)

        self._main()

    def _main(self):
        # show/hide tags depending on pause state and foreground window and meeting status
        if not self.state['pause']:
            self._actual_main()
        else:
            self._hide_all_tags()

        if not self.state['quit']:
            wx.CallLater(config.getint('GUI_LOOP_DELAY_MS'), self._main)
        else:
            self.gms.close()
            wx.Exit()

    def _actual_main(self):
        if ((
            active_window_title() == 'Among Us'
            or active_window_title().startswith('nametag_')
            or config.getboolean('SHOW_TAGS_OUTSIDE_OF_GAME')
        )
            and self.gms.is_voting_or_end_phase_of_meeting()
        ):
            if not self._just_was_in_meeting:
                self._restore_name_to_colour_matching()

            if self._just_ocrd_name_to_slot:
                self._just_ocrd_name_to_slot = False
                self._arrange_tags_based_on_ocrd_name_to_slot_matching()

            self._update_name_tags()
            self._show_all_tags()
        else:
            if self._just_was_in_meeting:
                self._save_name_to_colour_matching()
            self._hide_all_tags()

        self._just_was_in_meeting = self.gms.is_voting_or_end_phase_of_meeting()

    def _on_pause_toggle(self):
        self.state['pause'] = not self.state['pause']
        print('pause = ', self.state['pause'])

        if self.state['pause']:
            self._save_name_to_colour_matching()
        else:
            self._restore_name_to_colour_matching()

    def _show_all_tags(self):
        for element in self._name_tags_by_name.values():
            element.Show()

    def _hide_all_tags(self):
        for element in self._name_tags_by_name.values():
            element.Hide()

    # save/restore name-to-colour-matching of tags
    def _save_name_to_colour_matching(self):

        self._name_to_colour = {
            name: None for name in self._name_tags_by_name.keys()}

        colours = self.gms.slot_colours_from_second_ago()
        for slot_idx, name in self._names_by_slot().items():
            if name is self.MULTIPLE_NAMES:
                continue
            # XXX don't know why the check is needed but without it there were IndexErrors sometimes
            if slot_idx < len(colours):
                self._name_to_colour[name] = colours[slot_idx]
        print('name to colour: ', self._name_to_colour)

    def _restore_name_to_colour_matching(self):
        colours = self.gms.slot_colours()
        for name, colour in self._name_to_colour.items():
            if colour is not None:
                pos = self.gms.slot_pos_by_idx(colours.index(colour))
            else:
                pos = self._get_next_free_ledge_position_for_name_tag(name)
            self._name_tags_by_name[name].SetPosition(pos)

    # match and arrange tags to slots using OCR
    def _ocr_name_to_slot_matching(self):

        def best_match(name, names, threshold):
            score, match = max([
                (match_score(x, name), x)
                for x in names
                if match_score(x, name) >= threshold
            ], default=(None, None))

            if score is None:
                return None
            else:
                return match

        def match_score(a, b):
            # length of longest common prefix
            i = 0
            while i < min(len(a), len(b)) and a[i] == b[i]:
                i += 1
            return i

        # reset the mapping
        self._ocrd_name_to_slot_idx = dict()

        # generate new mapping
        print('starting generating mapping of names to slots...')
        slot_names = [name.lower() for name in self.gms.ocr_slot_names()]
        print('slot_names:', slot_names)

        for name in self._name_tags_by_name.keys():
            match = best_match(name.lower(), slot_names, threshold=config.getint(
                'LENGTH_NAME_MATCHING_PREFIX'))
            if not match:
                continue
            self._ocrd_name_to_slot_idx[name] = slot_names.index(match)

        self._just_ocrd_name_to_slot = True

    def _arrange_tags_based_on_ocrd_name_to_slot_matching(self):
        print('ocrd_name_to_slot_idx:', self._ocrd_name_to_slot_idx)
        for name, slot_idx in self._ocrd_name_to_slot_idx.items():
            slot_position = self.gms.slot_pos_by_idx(slot_idx)
            self._name_tags_by_name[name].SetPosition(slot_position)

    # nametag updates
    def _update_name_tags(self):
        self._update_name_tag_presences()
        self._update_name_tag_highlight_states()
        self._snap_name_tags_to_slots()

    def _update_name_tag_presences(self):
        prev_names = list(self._name_tags_by_name.keys())

        # add, remove name_tags based on names
        if set(self.state['names']) != set(self._name_tags_by_name.keys()):

            # add name_tags for new names
            new_names = set(self.state['names']) - set(prev_names)
            for name in new_names:
                # assign name_tag to name and move it to the next free ledge position
                self._name_tags_by_name[name] = NameTag(name=name)
                self._name_tags_by_name[name].SetPosition(
                    self._get_next_free_ledge_position_for_name_tag(name))

            # remove name_tags for gone names
            gone_names = set(prev_names) - set(self.state['names'])
            for name in gone_names:
                self._name_tags_by_name[name].Close()
                del self._name_tags_by_name[name]

    def _update_name_tag_highlight_states(self):
        speaker_names = self.state['speaker_names']

        if config.getboolean('EVERYONE_ALWAYS_SPEAKS_TEST_MODE'):
            speaker_names = self._name_tags_by_name.keys()

        non_speaker_names = set(
            self._name_tags_by_name.keys()) - set(speaker_names)

        for name in speaker_names:
            self._name_tags_by_name[name].highlight()
        for name in non_speaker_names:
            self._name_tags_by_name[name].dehighlight()

    def _snap_name_tags_to_slots(self):
        # set the position of nametags that are alone in their slot to a certain position on the slot
        for slot_idx, name in self._names_by_slot().items():
            if name is self.MULTIPLE_NAMES:
                continue
            name_tag = self._name_tags_by_name[name]
            x, y, w, h = self.gms.slot_rect_by_idx(slot_idx)
            snap_pos = (
                x + w // 2 - 100,
                y + h // 2
            )
            if name_tag.GetPosition() != snap_pos:
                name_tag.SetPosition(snap_pos)

    # helper methods
    def _get_next_free_ledge_position_for_name_tag(self, name):
        STEP = 20

        other_tag_rects = [
            self._name_tags_by_name[name].GetRect()
            for name in set(self._name_tags_by_name.keys()) - set([name])
        ]

        ledge_rect = wx.Rect(*LEDGE_RECT)
        cur_rect = self._name_tags_by_name[name].GetRect()

        cur_rect.topLeft = ledge_rect.topLeft
        while ledge_rect.Contains(cur_rect.bottomLeft):
            if not any(cur_rect.Intersects(other_tag_rect) for other_tag_rect in other_tag_rects):
                return cur_rect.topLeft
            cur_rect.Left += STEP
            if cur_rect.Left > ledge_rect.Right:
                cur_rect.Left = ledge_rect.Left
                cur_rect.Top += STEP

        # it's not that important that it is not overlapping, it's probably not worth a crash
        print('didn\'t find a free spot on the ledge, returning default value')
        return LEDGE_RECT.topLeft

    def _names_by_slot(self):
        result = dict()
        for name, tag in self._name_tags_by_name.items():
            slot = self.gms.name_tag_slot_at(tag.GetPosition())
            if slot is None:
                continue
            if result.get(slot, None) is None:
                result[slot] = name
            else:
                result[slot] = self.MULTIPLE_NAMES
        return result


def run_gui(state):
    app = wx.App()
    NameTagController(state)
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
    mp.freeze_support()

    manager = mp.Manager()
    state = manager.dict()

    state['quit'] = False
    state['pause'] = False
    state['names'] = []
    state['speaker_names'] = []

    def quit():
        global state
        print('quitting...')
        state['quit'] = True
    keyboard.add_hotkey(config['QUIT_HOTKEY'], quit)

    try:
        setup(state)
    except Exception:
        state['quit'] = True
