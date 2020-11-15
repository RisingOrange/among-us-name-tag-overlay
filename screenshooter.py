import cv2
import d3dshot

class Screenshooter():

    def __init__(self):
        print('creating Screenshoter instance...')
        # the frame_buffer_size is set to 3 to ensure thath the
        # screenshot returned by the method screenshot_from_second_ago 
        # is at least a second old
        self.d3d = d3dshot.create(capture_output='numpy', frame_buffer_size=4)

    def start(self):
        self.d3d.screenshot_every(1)

    def screenshot(self):
        return cv2.cvtColor(self.d3d.screenshot(), cv2.COLOR_RGB2BGR)

    def screenshot_from_second_ago(self):
        if len(self.d3d.frame_buffer) >= 4:
            return cv2.cvtColor(self.d3d.get_frame(3), cv2.COLOR_RGB2BGR)
        else:
            return self.screenshot()

    def stop(self):
        self.d3d.stop()
