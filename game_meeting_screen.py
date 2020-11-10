import math
from functools import lru_cache

import cv2

from utils import ocr_outline_font, screenshot, similiar_colour

DEBUG_MODE = True

RECT_OF_FIRST_SLOT = (275, 222, 625, 110)
SLOTS_HORIZONTAL_DISTANCE = 30
SLOTS_VERTICAL_DISTANCE = 25
MAX_SLOT_AMOUNT = 10

NAME_WIDTH = 300
NAME_HEIGHT = 53

VECTOR_FROM_SLOT_TO_NAME = (120, 0)
VECTOR_FROM_SLOT_TO_COLOUR_SPOT = (28, 75)
DX_FROM_SLOT_TO_ACTIVE_SLOT_CHECK_X = 1

LEDGE_RECT = (270, 35, 1155, 155)


BGR_TO_COLOUR_NAME = {
    (75, 80, 116): 'brown',
    (203, 164, 145): 'white',
    (83, 152, 188): 'yellow',
    (100, 57, 134): 'red',
    (76, 99, 181): 'orange',
    (117, 163, 81): 'light-green',
    (165, 69, 54): 'blue',
    (94, 111, 54): 'dark-green',
    (186, 83, 170): 'pink',
    (88, 76, 69): 'black',
    (191, 169, 36): 'cyan',
    (153, 70, 91): 'purple'
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
        name = ocr_outline_font(cropped)
        name = name.lower()
        results.append(name)

        if DEBUG_MODE:
            cv2.imwrite(f'cropped_names/{idx}.png', cropped)

    return results


def slot_colours():
    return _slot_colours_from_img(screenshot())


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
            print(x, y, tuple(img[y, x]), colour_name)

    return results


def _get_colour_name(bgr):
    for bgr_2, name in BGR_TO_COLOUR_NAME.items():
        if similiar_colour(bgr, bgr_2, h_diff_thresh=8, s_diff_thresh=120, v_diff_thresh=30):
            return name
    return None


def _active_slots_amount_from_img(img):
    STEP = 5

    for slot_idx in range(MAX_SLOT_AMOUNT):
        slot_x, slot_y = slot_pos_by_idx(slot_idx)
        stripe_x = slot_x + DX_FROM_SLOT_TO_ACTIVE_SLOT_CHECK_X
        stripe = [
            tuple(img[y, stripe_x])
            for y in range(slot_y, slot_y + RECT_OF_FIRST_SLOT[3], STEP)
        ]

         # two very similiar-looking white shades can have vastly different hues,
        # thats's why the h_diff_tresh is set so high here
        if not any(
            similiar_colour(colour, (255, 255, 255), h_diff_thresh=1000)
            for colour in
            stripe
        ):
            return slot_idx

    return MAX_SLOT_AMOUNT

