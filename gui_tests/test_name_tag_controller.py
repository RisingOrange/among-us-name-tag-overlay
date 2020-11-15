import sys
sys.path.append("..")

import wx

from main import NameTagController

app = wx.App()

state = dict()
state['quit'] = False
state['pause'] = False
state['names'] = [f'foo#{i}' for i in range(50)]
state['speaker_names'] = []

ntc = NameTagController(state)

app.MainLoop()