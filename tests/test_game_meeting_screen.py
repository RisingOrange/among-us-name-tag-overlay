import pprint
import unittest

import cv2
import game_meeting_screen as gms


class TestGameMeetingScreen(unittest.TestCase):

    def test_name_tag_slot_at(self):
        self.assertEqual(gms.name_tag_slot_at((370, 675)), 6)
        self.assertEqual(gms.name_tag_slot_at((1115, 270)), 1)
        self.assertEqual(gms.name_tag_slot_at((855, 405)), 2)

    def test_slot_rect_by_idx(self):

        # check fist slot rect
        slot_by_rect_idx = gms.slot_rect_by_idx()
        self.assertEqual(slot_by_rect_idx[0], gms.RECT_OF_FIRST_SLOT)

        # check last slot rect
        x1, y1, w, h = gms.RECT_OF_FIRST_SLOT
        last_slot_rect_should_be = (
            x1 + w + gms.SLOTS_HORIZONTAL_DISTANCE,
            y1 + 4 * (h + gms.SLOTS_VERTICAL_DISTANCE),
            w,
            h
        )
        self.assertEqual(slot_by_rect_idx[9], last_slot_rect_should_be)

    def test_slot_names_1(self):
        img = cv2.imread('images/screenshot_1.png')
        self.assertEqual(
            gms._slot_names_from_img(img),
            ['floating'] + [f'dummy {x}' for x in range(1, 7)] + ['' for _ in range(3)]
        )

    def test_slot_names_2(self):
        img = cv2.imread('images/screenshot_2.png')
        self.assertEqual(
            gms._slot_names_from_img(img),
            'felix jakub sandy minz naveen baumi noah abdulla crewamate'.split() + ['' for _ in range(3)]
        )

if __name__ == '__main__':
    unittest.main()
