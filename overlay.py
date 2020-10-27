import wx

class Overlay(wx.Frame):
    def __init__(self, *args, text=None, **dargs):
        assert text is not None

        style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR |
                  wx.NO_BORDER | wx.FRAME_SHAPED  )
        wx.Frame.__init__(self, None, *args, **dargs, style=style)
        self.Bind(wx.EVT_KEY_UP, self.OnKeyDown)
        self.Bind(wx.EVT_MOTION, self.OnMouse)
        self.SetTransparent( 220 )

        # put some text with a larger bold font on it
        st = wx.StaticText(self, label=text)
        font = st.GetFont()
        font.PointSize += 5
        font = font.Bold()
        st.SetFont(font)

        self.Show(True)

    def OnKeyDown(self, event):
        """quit if user press q or Esc"""
        if event.GetKeyCode() == 27 or event.GetKeyCode() == ord('Q'): #27 is Esc
            self.Close(force=True)
        else:
            event.Skip()

    def OnMouse(self, event):
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

app = wx.App()
f = Overlay(text='FloatingOrange', size=(200, 30))
app.MainLoop()