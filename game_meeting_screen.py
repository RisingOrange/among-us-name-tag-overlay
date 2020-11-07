import math
from functools import lru_cache

import cv2
import numpy as np

from util import ocr_outline_font, screenshot

DEBUG_MODE = True

RECT_OF_FIRST_SLOT = (275, 222, 625, 110)
SLOTS_HORIZONTAL_DISTANCE = 30
SLOTS_VERTICAL_DISTANCE = 25
MAX_SLOT_AMOUNT = 10

NAME_WIDTH = 300
NAME_HEIGHT = 53

VECTOR_FROM_SLOT_TO_NAME = (120, 0)
VECTOR_FROM_SLOT_TO_COLOUR_SPOT = (70, 80)
VECTOR_FROM_SLOT_TO_PRESENCE_CHECK_SPOT = (1, 50)

BGR_TO_COLOUR_NAME = {
    (81, 107, 132): 'brown',
    (238, 218, 202): 'white',
    (124, 237, 232): 'yellow',
    (72,  66, 194): 'red',
    (74, 138, 207): 'orange',
    (107, 229, 110): 'light-green',
    (216,  87,  61): 'blue',
    (94, 148,  60): 'dark-green',
    (187, 111, 209): 'pink',
    (60, 70, 77): 'black',  # black was not tested yet
}


def name_tag_slot_at(position):
    # returns the idx of the name tag slot at the position or None if there is no slot there
    for slot_idx, slot_rect in _slot_rect_by_idx_dict().items():
        if _is_inside_rect(position, slot_rect):
            return slot_idx
    return None


def _is_inside_rect(position, rect):
    x, y = position
    rx, ry, rw, rh = rect
    return (
        rx <= x <= (rx+rw) and
        ry <= y <= (ry+rh)
    )


def slot_pos_by_idx(idx):
    x, y, _, _ = slot_rect_by_idx(idx)
    return (x, y)


def slot_rect_by_idx(idx):
    return _slot_rect_by_idx_dict()[idx]


@lru_cache(1)
def _slot_rect_by_idx_dict():
    amount_slots_in_first_col = math.ceil(MAX_SLOT_AMOUNT / 2)

    x1, y1, w, h = RECT_OF_FIRST_SLOT

    first_row = []
    for i in range(amount_slots_in_first_col):
        first_row.append((
            x1,
            y1 + i * (h + SLOTS_VERTICAL_DISTANCE),
            w,
            h
        ))

    second_row = []
    for i in range(MAX_SLOT_AMOUNT - amount_slots_in_first_col):
        second_row.append((
            x1 + w + SLOTS_HORIZONTAL_DISTANCE,
            y1 + i * (h + SLOTS_VERTICAL_DISTANCE),
            w,
            h
        ))

    result_list = []
    for a, b in zip(first_row, second_row):
        result_list.extend([a, b])

    return {
        idx: rect for idx, rect in enumerate(result_list)
    }


def ocr_slot_names():
    # returns the in-game names in the order they appear on the slots
    return _slot_names_from_img(screenshot())


def _slot_names_from_img(img):
    results = []
    for idx, slot_rect in _slot_rect_by_idx_dict().items():
        sx, sy, _, _ = slot_rect
        dx, dy = VECTOR_FROM_SLOT_TO_NAME
        nx, ny = sx+dx, sy+dy

        cropped = img[ny: ny+NAME_HEIGHT, nx: nx+NAME_WIDTH]
        cv2.imwrite(f'cropped_names/{idx}.png', cropped)

        name = ocr_outline_font(cropped)
        name = name.lower()

        results.append(name)

    return results


def _slot_colours_from_img(img):
    results = []
    for slot_idx in range(_active_slots_amount_from_img(img)):
        sx, sy = slot_pos_by_idx(slot_idx)
        dx, dy = VECTOR_FROM_SLOT_TO_COLOUR_SPOT
        x, y = (sx+dx, sy+dy)

        if DEBUG_MODE:
            cropped = img[y:y+100, x:x+100]
            cv2.imwrite(f'images/colour_spots/{slot_idx}.png', cropped)

        colour = img[y, x]
        colour_name = _get_colour_name(colour)
        results.append(colour_name)

        if DEBUG_MODE:
            print(x, y, img[y, x], colour_name)

    return results


def _get_colour_name(bgr):
    for bgr_2, name in BGR_TO_COLOUR_NAME.items():
        if _similiar_colour(bgr, bgr_2):
            return name
    return None


def _active_slots_amount_from_img(img):
    for slot_idx in range(MAX_SLOT_AMOUNT):
        sx, sy = slot_pos_by_idx(slot_idx)
        dx, dy = VECTOR_FROM_SLOT_TO_PRESENCE_CHECK_SPOT
        x, y = (sx+dx, sy+dy)
        colour = tuple(img[y, x])
        # two very similiar-looking white shades can have vastly different hues,
        # thats's why the h_diff_tresh is set so high here
        if not _similiar_colour(colour, (255, 255, 255), h_diff_thresh=1000):
            return slot_idx
    return MAX_SLOT_AMOUNT


def _similiar_colour(bgr, bgr_2, h_diff_thresh=5, s_diff_thresh=30, v_diff_tresh=30):

    def bgr_to_hsv(bgr):
        single_pixel_bgr_frame = np.uint8([[[*bgr]]])
        single_pixel_hsv_frame = cv2.cvtColor(
            single_pixel_bgr_frame, cv2.COLOR_BGR2HSV)
        return single_pixel_hsv_frame[0, 0]

    h, s, v = map(int, bgr_to_hsv(bgr))
    h_2, s_2, v_2, = map(int, bgr_to_hsv(bgr_2))
    return (
        abs(h - h_2) < h_diff_thresh and
        abs(s - s_2) < s_diff_thresh and
        abs(v - v_2) < v_diff_tresh
    )
