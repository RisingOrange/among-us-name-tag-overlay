import wx

class NameTag(wx.Frame):
    # a draggable overlay object that has a name on it and can be highlighted
    def __init__(self, *args, text=None, **dargs):
        assert text is not None
        self.text = text

        style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR |
                  wx.NO_BORDER | wx.FRAME_SHAPED )
        wx.Frame.__init__(self, None, *args, **dargs, style=style)
        
        self.SetTransparent(220)

        self.setup_text()
        self._is_highlight_active = False
        self._highlight_colours = [(15, 255, 63), (0, 0, 0)]

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

    def highlight(self, recursive_call=False):

        # ignore non-recursive call, when highlight is already active
        if not recursive_call and self._is_highlight_active:
            return

        # ignore recursive call when hightlight is not active anymore
        if recursive_call and not self._is_highlight_active:
            return

        if not recursive_call:
            self._is_highlight_active = True

        # pop colour from start and then append it back to the end,
        # this way the colours will be rotated
        cur_colour = self._highlight_colours.pop(0)
        self._highlight_colours.append(cur_colour)

        self.st.SetForegroundColour(cur_colour)
        self.st.Refresh()
        wx.CallLater(500, self.highlight, recursive_call=True)

    def dehighlight(self):
        self._is_highlight_active = False
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
    r = NameTag(text='a_name')

    app.MainLoop()


if __name__ == '__main__':
    gui_loop()