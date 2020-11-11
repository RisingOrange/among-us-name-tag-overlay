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
        self.assertEqual(gms.slot_rect_by_idx(0), gms.RECT_OF_FIRST_SLOT)

        # check last slot rect
        x1, y1, w, h = gms.RECT_OF_FIRST_SLOT
        last_slot_rect_should_be = (
            x1 + w + gms.SLOTS_HORIZONTAL_DISTANCE,
            y1 + 4 * (h + gms.SLOTS_VERTICAL_DISTANCE),
            w,
            h
        )
        self.assertEqual(gms.slot_rect_by_idx(9), last_slot_rect_should_be)

    def test_slot_names_2(self):
        # test if normal names recognized, only one so it
        img = cv2.imread('images/screenshot_2.png')
        self.assertEqual(
            gms._slot_names_from_img(img, 1),
            'felix'.split()
        )

    def test_slot_names_red_name(self):
        # test if impostor names are recognized
        img = cv2.imread('images/screenshot_6.png')
        self.assertEqual(
            gms._slot_names_from_img(img, 1),
            ['jakub']
        )

    def test_slot_colours_1(self):
        img = cv2.imread('images/screenshot_1.png')
        retrieved_colours = gms._slot_colours_from_img(img)
        self.assertEqual(retrieved_colours, [
                         'white', 'red', 'blue', 'dark-green', 'pink', 'orange', 'yellow'])

    def test_slot_colours_2(self):
        img = cv2.imread('images/screenshot_2.png')
        retrieved_colours = gms._slot_colours_from_img(img)
        self.assertEqual(retrieved_colours, [
                         'brown', 'white', 'yellow', 'red', 'orange', 'light-green'])

    def test_slot_colours_3(self):
        img = cv2.imread('images/screenshot_3.png')
        retrieved_colours = gms._slot_colours_from_img(img)
        self.assertEqual(retrieved_colours, [
                         'orange', 'cyan', 'brown', 'blue', 'light-green', 'pink'])

    def test_slot_colours_4(self):
        img = cv2.imread('images/screenshot_4.png')
        retrieved_colours = gms._slot_colours_from_img(img)
        self.assertEqual(retrieved_colours, [
                         'cyan', 'red', 'blue', 'dark-green', 'pink'])

    def test_slot_colours_5(self):
        img = cv2.imread('images/screenshot_5.png')
        retrieved_colours = gms._slot_colours_from_img(img)
        self.assertEqual(retrieved_colours, [
                         'purple', 'red', 'blue', 'dark-green', 'pink'])

    def test_active_slots_amount_1(self):
        img = cv2.imread('images/screenshot_1.png')
        self.assertEqual(gms._active_slots_amount_from_img(img), 7)

    def test_active_slots_amount_2(self):
        img = cv2.imread('images/screenshot_2.png')
        self.assertEqual(gms._active_slots_amount_from_img(img), 6)

    def test_active_slots_amount_3(self):
        img = cv2.imread('images/screenshot_3.png')
        self.assertEqual(gms._active_slots_amount_from_img(img), 6)



if __name__ == '__main__':
    unittest.main()
