import wx

from main import Overlay


if __name__ == '__main__':
    app = wx.App()
    ov = Overlay(text='hiajsldkfjaskldfjaslköfd')
    # ov.highlight()
    # ov.dehighlight()
    app.MainLoop()
