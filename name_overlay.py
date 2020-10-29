import wx

class NameOverlay(wx.Frame):
    # a draggable overlay object that has a name on it and can be highlighted
    def __init__(self, *args, text=None, **dargs):
        assert text is not None
        self.text = text

        style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR |
                  wx.NO_BORDER | wx.FRAME_SHAPED )
        wx.Frame.__init__(self, None, *args, **dargs, style=style)
        
        self.SetTransparent(220)

        self.setup_text()

        self.setup_dragging()

        self.Show(True)

    def setup_text(self):
        # put some text with a larger bold font on it
        self.st = wx.StaticText(self, label=self.text)
        font = self.st.GetFont()
        font.PointSize += 5
        font = font.Bold()
        self.st.SetFont(font)

        # resize frame to size of the text
        frame_size = self.st.GetSize()
        self.SetSize(frame_size)

    def setup_dragging(self):
        self.drag_img = wx.DragImage(self.text)
        self.st.Bind(wx.EVT_MOTION, self.on_mouse)
        self.st.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.st.Bind(wx.EVT_LEFT_UP, self.on_left_up)

    def highlight(self):
        self.st.SetForegroundColour((15, 255, 63))
        self.st.Refresh()

    def dehighlight(self):
        self.st.SetForegroundColour((0, 0, 0))
        self.st.Refresh()

    def on_mouse(self, event):
        self.drag_img.Move(event.GetPosition())

    def on_left_down(self, event):
        self._dragStartPos = self.GetPosition()

        self.drag_img.BeginDrag((0, 0), self.st, fullScreen=True)
        self.drag_img.Move(event.GetPosition())
        self.drag_img.Show()

    def on_left_up(self, event):
        displacement = event.GetPosition() + self._dragStartPos
        self.SetPosition(displacement)

        self.drag_img.EndDrag()


def gui_loop():
    app = wx.App()
    r = NameOverlay(text='a_name')

    app.MainLoop()


if __name__ == '__main__':
    gui_loop()