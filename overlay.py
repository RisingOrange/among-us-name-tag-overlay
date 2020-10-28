import wx

class Overlay(wx.Frame):
    def __init__(self, *args, text=None, **dargs):
        assert text is not None

        style = ( wx.CLIP_CHILDREN | wx.STAY_ON_TOP | wx.FRAME_NO_TASKBAR |
                  wx.NO_BORDER | wx.FRAME_SHAPED  )
        wx.Frame.__init__(self, None, *args, **dargs, style=style)
        self.Bind(wx.EVT_MOTION, self.on_mouse)
        self.SetTransparent(220)

        # put some text with a larger bold font on it
        st = wx.StaticText(self, label=text)
        font = st.GetFont()
        font.PointSize += 5
        font = font.Bold()
        st.SetFont(font)

        self.Show(True)


    def on_mouse(self, event):
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


class Root(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None)
        
        self.overlays = []
        self.on_timer()

    def on_timer(self):
        if len(self.overlays) > 2:
            ov = self.overlays.pop(0)
            ov.Destroy()

        self.overlays.append(Overlay(text='FloatingOrange', size=(200, 30)))
        wx.CallLater(2000, self.on_timer)


def main():
    app = wx.App()
    r = Root()
    app.MainLoop()


if __name__ == '__main__':
    main()