import cv2
import d3dshot
import numpy as np
import pytesseract
from PIL import Image, ImageColor, ImageDraw
import win32gui

d3d = None


def get_d3d():
    global d3d
    if d3d is None:
        d3d = d3dshot.create()
    return d3d


def active_window_title():
    return win32gui.GetWindowText(win32gui.GetForegroundWindow())


def screenshot():
    # returns an cv2-format screenshot
    return pil_to_cv(get_d3d().screenshot())


def pil_to_cv(pil_img):
    open_cv_image = np.array(pil_img)
    return open_cv_image[:, :, ::-1]


def cv_to_pil(cv_img):
    img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    return Image.fromarray(img)


def ocr_outline_font(name_img):
    # gets text with outline font from an image

    # filter out font
    img = cv2.inRange(name_img, np.array(
        [100, 100, 100]), np.array([255, 255, 255]))
    img = cv_to_pil(img)

    # fill background
    point_inside_digit = (0, 0)
    ImageDraw.floodfill(img, point_inside_digit,
                        ImageColor.getrgb("black"), thresh=200)

    # invert
    img = pil_to_cv(img)
    img = cv2.inRange(img, np.array([0, 0, 0]), np.array([50, 50, 50]))
    img = cv_to_pil(img)

    # apply image to string
    return pytesseract.image_to_string(img).strip()


def similiar_colour(bgr, bgr_2, h_diff_thresh=5, s_diff_thresh=30, v_diff_thresh=30):
    h, s, v = map(int, bgr_to_hsv(bgr))
    h_2, s_2, v_2, = map(int, bgr_to_hsv(bgr_2))
    return (
        abs(h - h_2) < h_diff_thresh and
        abs(s - s_2) < s_diff_thresh and
        abs(v - v_2) < v_diff_thresh
    )


def bgr_to_hsv(bgr):
    single_pixel_bgr_frame = np.uint8([[[*bgr]]])
    single_pixel_hsv_frame = cv2.cvtColor(
        single_pixel_bgr_frame, cv2.COLOR_BGR2HSV)
    return single_pixel_hsv_frame[0, 0]


def main():
    img = cv2.imread('cropped_names/2.png')
    print(ocr_outline_font(img))


if __name__ == '__main__':
    main()
