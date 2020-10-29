import wx

class NameOverlay(wx.Frame):
    # a draggable overlay object that has a name on it and can be highlighted
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
        self.st.Refresh()

    def dehighlight(self):
        self.st.SetForegroundColour((0, 0, 0))
        self.st.Refresh()

    def on_mouse(self, event):
        # implement dragging
        if not event.Dragging():
            self._dragPos = None
            return
        if not self._dragPos:
            self._dragPos = event.GetPosition()
        else:
            pos = event.GetPosition()
            displacement = self._dragPos - pos
            self.SetPosition( self.GetPosition() - displacement )



def gui_loop():
    app = wx.App()
    r = NameOverlay(text='a_name')
    app.MainLoop()


if __name__ == '__main__':
    gui_loop()