import time
import tkinter as tk

import pywintypes
import win32api
import win32con


class XOverlay():

    def __init__(self, x, y):
        self.label = tk.Label(text='X', font=('Times New Roman','20'), fg='red', bg='white')
        self.label.master.overrideredirect(True)
        self.label.master.geometry(f"+{x}+{y}")
        self.label.master.lift()
        self.label.master.wm_attributes("-topmost", True)
        self.label.master.wm_attributes("-disabled", True)
        self.label.master.wm_attributes("-transparentcolor", "white")

        hWindow = pywintypes.HANDLE(int(self.label.master.frame(), 16))
        # http://msdn.microsoft.com/en-us/library/windows/desktop/ff700543(v=vs.85).aspx
        # The WS_EX_TRANSPARENT flag makes events (like mouse clicks) fall through the window.
        exStyle = win32con.WS_EX_COMPOSITED | win32con.WS_EX_LAYERED | win32con.WS_EX_NOACTIVATE | win32con.WS_EX_TOPMOST | win32con.WS_EX_TRANSPARENT
        win32api.SetWindowLong(hWindow, win32con.GWL_EXSTYLE, exStyle)

        self.label.pack()
        self.label.update()

    def hide(self):
        self.label['text'] = ''
        self.label.update()
        self.label.update_idletasks()
        self.label.destroy()


if __name__ == '__main__':
    overlay = XOverlay(1400, 30)
    time.sleep(2)
    overlay.hide()
    time.sleep(2)


