import math

RECT_OF_FIRST_SLOT = (275, 222, 625, 110)
SLOTS_HORIZONTAL_DISTANCE = 30
SLOTS_VERTICAL_DISTANCE = 25
SLOT_AMOUNT = 10


def name_tag_slot_at(position):
    # returns the idx of the name tag slot at the position or None if there is no slot there
    for slot_idx, slot_rect in _slot_rect_by_idx().items():
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

def _slot_rect_by_idx():
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
        idx : rect for idx, rect in enumerate(result_list)
    }
    



def mouth_pos_for_slot(slot_idx):
    # returns position for the bean mouth corresponding to the slot
    pass
