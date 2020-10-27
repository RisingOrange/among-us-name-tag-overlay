import cv2
import keyboard
import numpy as np
import pyautogui

# threshold for matching avatars, this seems to be a good value
THRESHOLD = 0.8


def active_speaker_indices(avatars):
    # given the avatars of the users in the voice-channel, return the indeces of
    # the useres of which the avatar is highlighted in the overlay

    # make a screenshot
    screenshot_img_path = 'screenshot.png'
    pyautogui.screenshot(screenshot_img_path)
    screenshot = cv2.imread(screenshot_img_path, 1)

    avatar_present = [False] * len(avatars)
    # for each avatar
    for i, avatar in enumerate(avatars):
    #   calculate the region where the avatar is (possibly highlighted) based on its index
        cropped = screenshot[(25 + i*45) : (25 + (i+1)*45), 30 : 100]

        

        # cv2.imshow('.', cropped)
        # cv2.waitKey(0)
        
        
        # compare the region with the avatar
        small_avatar = cv2.resize(avatar, (40, 40))
        small_avatar = small_avatar[5:35, 5:35]

        # cv2.imwrite('cropped.png', cropped)
        # cv2.imwrite('small_avatar.png', small_avatar)

        match_result = cv2.matchTemplate(cropped, small_avatar, cv2.TM_CCOEFF_NORMED)

        # cv2.imshow('match', match_result)
        # cv2.waitKey(0)

        loc = np.where(match_result >= THRESHOLD)

        if len(loc[0]) != 0:
            avatar_present[i] = True

    return [i for i, present in enumerate(avatar_present) if present]
    





if __name__ == '__main__':

    # testing with default avatars
    while True:
        if keyboard.is_pressed('ctrl+r'):
            default_avatar = cv2.imread('avatar.png')
            indeces = active_speaker_indices([default_avatar, default_avatar])
            print(indeces)
