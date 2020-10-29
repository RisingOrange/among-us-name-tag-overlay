import wx

class ShapedImage(wx.Frame):
    def __init__(self, parent, img_path, position):
        wx.Frame.__init__(self, parent, -1,
                            style =
                            wx.FRAME_SHAPED
                            | wx.SIMPLE_BORDER
                            | wx.FRAME_NO_TASKBAR
                            | wx.STAY_ON_TOP
                            )

        self.Bind(wx.EVT_PAINT, self.OnPaint)

        self._setup_shaped_image(img_path)

        self.SetPosition(position)
        self.Show(True)

    def _setup_shaped_image(self, img_path):
        bmp = wx.Bitmap(img_path)
        img = bmp.ConvertToImage()
        img.ConvertAlphaToMask()
        self.bmp = wx.Bitmap(img)

        # Use the bitmap's mask to determine the region
        r = wx.Region(self.bmp)
        self.hasShape = self.SetShape(r)

        dc = wx.ClientDC(self)
        dc.DrawBitmap(self.bmp, 0,0, True)        

    def OnPaint(self, evt):
        dc = wx.PaintDC(self)
        dc.DrawBitmap(self.bmp, 0,0, True)


if __name__ == '__main__':
    app = wx.App()
    img = ShapedImage(None, 'mouth.png', (100, 100))
    app.MainLoop()