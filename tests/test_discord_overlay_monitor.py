import unittest

import cv2
import discord_overlay_monitor as dom


class TestDicordOverlayMonitor(unittest.TestCase):

    def test_active_speaker_names_1(self):
        img = cv2.imread('tests/images/screenshot_2.png')
        dummy_names = map(str, range(9))
        self.assertEqual(
            dom._active_speaker_names_from_img(img, dummy_names), 
            ["7"]
        )

    def test_active_speaker_names_2(self):
        img = cv2.imread('tests/images/screenshot_3.png')
        dummy_names = map(str, range(10))
        self.assertEqual(
            dom._active_speaker_names_from_img(img, dummy_names), 
            ["0", "8"]
        )
