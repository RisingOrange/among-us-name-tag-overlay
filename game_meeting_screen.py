import configparser
import math
from functools import lru_cache

import cv2
import numpy as np
import pytesseract
from cachetools import TTLCache, cached

from pyinstaller_utils import resource_path
from screenshooter import Screenshooter
from utils import ocr_outline_font, similiar_colour

config = configparser.ConfigParser()
config.read(resource_path('config.ini'))
config = config['DEFAULT']


RECT_OF_FIRST_SLOT = (275, 222, 625, 110)
SLOTS_HORIZONTAL_DISTANCE_VECTOR = (30, 0)
SLOTS_VERTICAL_DISTANCE_VECTOR = (0, 25)
MAX_SLOT_AMOUNT = 10

NAME_DIMENSIONS = (300, 53)

SLOT_TO_NAME_VECTOR = (120, 0)
SLOT_TO_COLOUR_SPOT_VECTOR = (28, 75)
SLOT_TO_ACTIVE_SLOT_CHECK_VECTOR = (1, 0)

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

# for checking if in meeting
TABLET_BUTTON_IMG = cv2.imread(resource_path('tablet_button.png'))
TABLET_BUTTON_RECT = (1600, 480, 110, 100)
# the lower, the harder, 0.001 didn't work anymore
TABLET_BUTTON_MATCH_THRESH = 0.01
DISCUSS_SPLASH_SCREEN_GREEN_POS = (950, 520)
DISCUSS_SPLASH_SCREEN_GREEN_BGR = (83, 238, 171)


class GameMeetingScreen:

    def __init__(self):
        self.scr = Screenshooter()
        self.scr.start()

    # users of the class have to close it, when their done with it
    def close(self):
        self.scr.stop()

    # name_tag slot positions
    def name_tag_slot_at(self, position):
        # returns the idx of the name tag slot at the position or None if there is no slot there
        for slot_idx, slot_rect in self._slot_rect_by_idx_dict().items():
            if self._is_inside_rect(position, slot_rect):
                return slot_idx
        return None

    def _is_inside_rect(self, position, rect):
        x, y = position
        rx, ry, rw, rh = rect
        return (
            rx <= x <= (rx+rw) and
            ry <= y <= (ry+rh)
        )

    def slot_pos_by_idx(self, idx):
        x, y, _, _ = self.slot_rect_by_idx(idx)
        return (x, y)

    def slot_rect_by_idx(self, idx):
        return self._slot_rect_by_idx_dict()[idx]

    @lru_cache(1)
    def _slot_rect_by_idx_dict(self, ):
        amount_slots_in_first_col = math.ceil(MAX_SLOT_AMOUNT / 2)

        x1, y1, w, h = RECT_OF_FIRST_SLOT

        first_row = []
        for i in range(amount_slots_in_first_col):
            first_row.append((
                x1,
                y1 + i * (h + SLOTS_VERTICAL_DISTANCE_VECTOR[1]),
                w,
                h
            ))

        second_row = []
        for i in range(MAX_SLOT_AMOUNT - amount_slots_in_first_col):
            second_row.append((
                x1 + w + SLOTS_HORIZONTAL_DISTANCE_VECTOR[0],
                y1 + i * (h + SLOTS_VERTICAL_DISTANCE_VECTOR[1]),
                w,
                h
            ))

        result_list = []
        for a, b in zip(first_row, second_row):
            result_list.extend([a, b])

        return {
            idx: rect for idx, rect in enumerate(result_list)
        }

    # ocr slot names
    def ocr_slot_names(self):
        # returns the in-game names in the order they appear on the slots
        screenshot_img = self.scr.screenshot()
        return self._slot_names_from_img(screenshot_img, self._active_slots_amount_from_img(screenshot_img))

    def _slot_names_from_img(self, img, active_slot_amount):

        def ocr_impostor_name(img):
            mask = mask_impostor_red(img)

            # invert, so that the font is black and the background white
            inverted = cv2.inRange(mask, 0, 50)
            return pytesseract.image_to_string(inverted).strip()

        def mask_impostor_red(img):
            # returns a mask of the image, all pixels matching the red shade of the impostor name
            # are equal to 255, all other 0
            img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
            result = cv2.inRange(img_hsv, np.array(
                [120, 100, 150]), np.array([200, 300, 300]))
            return result

        def contains_impostor_red(img):
            return 255 in mask_impostor_red(img)

        results = []
        for idx, slot_rect in sorted(list(self._slot_rect_by_idx_dict().items()))[:active_slot_amount]:
            sx, sy, _, _ = slot_rect
            dx, dy = SLOT_TO_NAME_VECTOR
            nx, ny = sx+dx, sy+dy

            cropped = img[ny: ny+NAME_DIMENSIONS[1], nx: nx+NAME_DIMENSIONS[0]]

            if contains_impostor_red(cropped):
                name = ocr_impostor_name(cropped)
            else:
                name = ocr_outline_font(cropped)

            name = name.lower()
            results.append(name)

            if config.getboolean('GAME_MEETING_SCREEN_DEBUG_MODE'):
                cv2.imwrite(f'cropped_names/{idx}.png', cropped)

        return results

    # slot colours
    def slot_colours(self):
        return self._slot_colours_from_img(self.scr.screenshot())

    def slot_colours_from_second_ago(self):
        return self._slot_colours_from_img(self.scr.screenshot_from_second_ago())

    def _slot_colours_from_img(self, img):
        results = []
        for slot_idx in range(self._active_slots_amount_from_img(img)):
            sx, sy = self.slot_pos_by_idx(slot_idx)
            dx, dy = SLOT_TO_COLOUR_SPOT_VECTOR
            x, y = (sx+dx, sy+dy)

            if config.getboolean('GAME_MEETING_SCREEN_DEBUG_MODE'):
                cropped = img[y:y+100, x:x+100]
                cv2.imwrite(f'images/colour_spots/{slot_idx}.png', cropped)

            colour = img[y, x]
            colour_name = self._get_colour_name(colour)
            results.append(colour_name)

            if config.getboolean('GAME_MEETING_SCREEN_DEBUG_MODE'):
                print(x, y, tuple(img[y, x]), colour_name)

        return results

    def _get_colour_name(self, bgr):
        for bgr_2, name in BGR_TO_COLOUR_NAME.items():
            if similiar_colour(bgr, bgr_2, h_diff_thresh=8, s_diff_thresh=120, v_diff_thresh=30):
                return name
        return None

    def _active_slots_amount_from_img(self, img):
        STEP = 5

        for slot_idx in range(MAX_SLOT_AMOUNT):
            slot_x, slot_y = self.slot_pos_by_idx(slot_idx)
            stripe_x = slot_x + SLOT_TO_ACTIVE_SLOT_CHECK_VECTOR[0]
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

    # is meeting active
    @cached(cache=TTLCache(maxsize=1, ttl=0.8))
    def is_voting_or_end_phase_of_meeting(self):
        return self._is_voting_or_end_phase_of_meeting_from_img(self.scr.screenshot())

    def _is_voting_or_end_phase_of_meeting_from_img(self, img):

        # amount of active slots can't be below 3, because there has to be at least one impostor and
        # at least one more impostor than crewmate, else the game ends

        return (
            self._is_tablet_button_visible_from_img(img)
            and self._active_slots_amount_from_img(img) >= 3
            and not self._is_discuss_splash_screen_visible_from_img(img)
        )

    def _is_tablet_button_visible_from_img(self, img):
        rx, ry, rw, rh = TABLET_BUTTON_RECT
        cropped = img[ry:ry+rh, rx:rx+rw]
        match_result = cv2.matchTemplate(
            cropped, TABLET_BUTTON_IMG, cv2.TM_SQDIFF_NORMED)
        match_locations = np.where(match_result <= TABLET_BUTTON_MATCH_THRESH)

        if config['GAME_MEETING_SCREEN_DEBUG_MODE']:
            cv2.imwrite('images/cropped_tablet_button.png', cropped)

        return len(match_locations[0]) > 0

    def _is_discuss_splash_screen_visible_from_img(self, img):

        # checks for the greentone that is in the middle of the screen,
        # when the slpash screen is shown
        x, y = DISCUSS_SPLASH_SCREEN_GREEN_POS
        return similiar_colour(
            img[y, x],
            DISCUSS_SPLASH_SCREEN_GREEN_BGR
        )


if __name__ == '__main__':
    scr = Screenshooter()
    img = scr.screenshot()
    cv2.imshow('', img)
    cv2.waitKey(0)
    print(GameMeetingScreen()._is_voting_or_end_phase_of_meeting_from_img(img))
    scr.stop()
