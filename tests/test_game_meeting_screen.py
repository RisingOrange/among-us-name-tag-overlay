import unittest
import pprint

import game_meeting_screen as gms

class TestGameMeetingScreen(unittest.TestCase):

    def test_name_tag_slot_at(self):
        self.assertEqual(gms.name_tag_slot_at((370, 675)), 6)
        self.assertEqual(gms.name_tag_slot_at((1115, 270)), 1)
        self.assertEqual(gms.name_tag_slot_at((855, 405)), 2)

    def test_slot_rect_by_idx(self):
        # pprint.pprint(gms._slot_rect_by_idx())

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

    def test_mouth_pos_for_slot(self):
        self.assertEqual(gms.mouth_pos_for_slot(0), gms.POS_OF_FIST_MOUTH)

        _, _, _, rh = gms.RECT_OF_FIRST_SLOT
        x1, y1 = gms.POS_OF_FIST_MOUTH
        mouth_idx_2_should_be = (
            x1,
            y1 + rh + gms.SLOTS_VERTICAL_DISTANCE
        )
        self.assertEqual(gms.mouth_pos_for_slot(2), mouth_idx_2_should_be)


if __name__ == '__main__':
    unittest.main()