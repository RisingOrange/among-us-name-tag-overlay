import math

import cv2

from util import ocr_outline_font, screenshot

RECT_OF_FIRST_SLOT = (275, 222, 625, 110)
SLOTS_HORIZONTAL_DISTANCE = 30
SLOTS_VERTICAL_DISTANCE = 25
SLOT_AMOUNT = 10

VECTOR_FROM_SLOT_TO_NAME = (120, 0)
NAME_WIDTH = 300
NAME_HEIGHT = 53


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
    x, y, _, _ =  slot_rect_by_idx(idx)
    return (x, y)


def slot_rect_by_idx(idx):
    return _slot_rect_by_idx_dict()[idx]
    

def _slot_rect_by_idx_dict():
    amount_slots_in_first_col = math.ceil(SLOT_AMOUNT / 2)

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
    for i in range(SLOT_AMOUNT - amount_slots_in_first_col):
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
