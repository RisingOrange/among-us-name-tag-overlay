import cv2
import d3dshot

import numpy as np


# settings for matching avatars, these seem to work
IMG_MATCH_METHOD = cv2.TM_SQDIFF_NORMED # with this method, better matches are represented by lower numbers
IMG_MATCH_THRESHOLD = 0.6

OVERLAY_X = 45
OVERLAY_Y = 25
OVERLAY_ROWS_HEIGHT_AND_DISTANCE = 48


d3d = None

def get_d3d():
    global d3d
    if d3d is None:
        d3d = d3dshot.create()
    return d3d

    
def active_speaker_names(names, avatars):
    # given the avatars of the users in the voice-channel, return the names of
    # the users of which the avatar is highlighted in the overlay

    screenshot_img = screenshot()

    results = []
    for i, name_and_avatar in enumerate(sorted_names_and_avatars(names, avatars)):
        name, avatar = name_and_avatar

        # calculate the region where the avatar is (possibly highlighted) based on its index
        cropped = screenshot_img[
            (OVERLAY_Y + i*OVERLAY_ROWS_HEIGHT_AND_DISTANCE) : (OVERLAY_Y + (i+1)*OVERLAY_ROWS_HEIGHT_AND_DISTANCE), 
            OVERLAY_X : 100
        ]

        # compare the region with the avatar
        small_avatar = cv2.resize(avatar, (40, 40))
        small_avatar = small_avatar[5:35, 5:35]

        match_result = cv2.matchTemplate(cropped, small_avatar, IMG_MATCH_METHOD)

        match_locations = np.where(match_result <= IMG_MATCH_THRESHOLD)
        if len(match_locations[0]) != 0:
            results.append(name)

    return results

def sorted_names_and_avatars(names, avatars):
    # return names and avatars in the order they appear on the overlay
    return sorted(zip(names, avatars), key=lambda x: x[0].lower())


def screenshot():
    result_pil = get_d3d().screenshot()
    result_cv2 = np.array(result_pil)

    # convert RGB to BGR
    return result_cv2[:, :, ::-1]


if __name__ == '__main__':

    import keyboard

    # testing with default avatars
    while True:
        if keyboard.is_pressed('ctrl+r'):
            avatar = cv2.imread('avatar.png')
            names = active_speaker_names(
                ['FloatingOrange', '2nd name'], 
                [avatar, avatar]
            )
            # print(names)

    
