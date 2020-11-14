import unittest

import cv2
from game_meeting_screen import (RECT_OF_FIRST_SLOT,
                                 SLOTS_HORIZONTAL_DISTANCE_VECTOR,
                                 SLOTS_VERTICAL_DISTANCE_VECTOR,
                                 GameMeetingScreen)


class TestGameMeetingScreen(unittest.TestCase):

    def setUp(self):
        self.gms = GameMeetingScreen()

    def test_name_tag_slot_at(self):
        self.assertEqual(self.gms.name_tag_slot_at((370, 675)), 6)
        self.assertEqual(self.gms.name_tag_slot_at((1115, 270)), 1)
        self.assertEqual(self.gms.name_tag_slot_at((855, 405)), 2)

    def test_slot_rect_by_idx(self):

        # check fist slot rect
        self.assertEqual(self.gms.slot_rect_by_idx(0), RECT_OF_FIRST_SLOT)

        # check last slot rect
        x1, y1, w, h = RECT_OF_FIRST_SLOT
        last_slot_rect_should_be = (
            x1 + w + SLOTS_HORIZONTAL_DISTANCE_VECTOR[0],
            y1 + 4 * (h + SLOTS_VERTICAL_DISTANCE_VECTOR[1]),
            w,
            h
        )
        self.assertEqual(self.gms.slot_rect_by_idx(9),
                         last_slot_rect_should_be)

    def test_slot_names_2(self):
        # test if normal names recognized, only one so it
        img = cv2.imread('images/screenshot_2.png')
        self.assertEqual(
            self.gms._slot_names_from_img(img, 1),
            'felix'.split()
        )

    def test_slot_names_red_name(self):
        # test if impostor names are recognized
        img = cv2.imread('images/screenshot_6.png')
        self.assertEqual(
            self.gms._slot_names_from_img(img, 1),
            ['jakub']
        )

    def test_slot_colours_1(self):
        img = cv2.imread('images/screenshot_1.png')
        retrieved_colours = self.gms._slot_colours_from_img(img)
        self.assertEqual(retrieved_colours, [
                         'white', 'red', 'blue', 'dark-green', 'pink', 'orange', 'yellow'])

    def test_slot_colours_2(self):
        img = cv2.imread('images/screenshot_2.png')
        retrieved_colours = self.gms._slot_colours_from_img(img)
        self.assertEqual(retrieved_colours, [
                         'brown', 'white', 'yellow', 'red', 'orange', 'light-green'])

    def test_slot_colours_3(self):
        img = cv2.imread('images/screenshot_3.png')
        retrieved_colours = self.gms._slot_colours_from_img(img)
        self.assertEqual(retrieved_colours, [
                         'orange', 'cyan', 'brown', 'blue', 'light-green', 'pink'])

    def test_slot_colours_4(self):
        img = cv2.imread('images/screenshot_4.png')
        retrieved_colours = self.gms._slot_colours_from_img(img)
        self.assertEqual(retrieved_colours, [
                         'cyan', 'red', 'blue', 'dark-green', 'pink'])

    def test_slot_colours_5(self):
        img = cv2.imread('images/screenshot_5.png')
        retrieved_colours = self.gms._slot_colours_from_img(img)
        self.assertEqual(retrieved_colours, [
                         'purple', 'red', 'blue', 'dark-green', 'pink'])

    def test_active_slots_amount_1(self):
        img = cv2.imread('images/screenshot_1.png')
        self.assertEqual(self.gms._active_slots_amount_from_img(img), 7)

    def test_active_slots_amount_2(self):
        img = cv2.imread('images/screenshot_2.png')
        self.assertEqual(self.gms._active_slots_amount_from_img(img), 6)

    def test_active_slots_amount_3(self):
        img = cv2.imread('images/screenshot_3.png')
        self.assertEqual(self.gms._active_slots_amount_from_img(img), 6)

    def test_is_meeting_active_from_img_1(self):
        self.assertEqual(
            self.gms._is_voting_or_end_phase_of_meeting_from_img(
                cv2.imread('images/screenshot_1.png')),
            True
        )

    def test_is_meeting_active_from_img_2(self):
        self.assertEqual(
            self.gms._is_voting_or_end_phase_of_meeting_from_img(
                cv2.imread('images/screenshot_2.png')),
            True
        )

    def test_is_meeting_active_from_img_3(self):
        self.assertEqual(
            self.gms._is_voting_or_end_phase_of_meeting_from_img(
                cv2.imread('images/screenshot_7.png')),
            False
        )

    def test_is_meeting_active_from_img_4(self):
        self.assertEqual(
            self.gms._is_voting_or_end_phase_of_meeting_from_img(
                cv2.imread('images/screenshot_8.png')),
            False
        )


if __name__ == '__main__':
    unittest.main()
