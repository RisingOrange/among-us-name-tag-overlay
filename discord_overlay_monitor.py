import configparser

import cv2

from utils import screenshot, similiar_colour

config = configparser.ConfigParser()
config.read('config.ini')
config = config['DEFAULT']

OVERLAY_X = 45
OVERLAY_Y = 25
OVERLAY_ROWS_HEIGHT_AND_DISTANCE = 48


def active_speaker_names(names):
    return _active_speaker_names_from_img(screenshot(), names)


def _active_speaker_names_from_img(img, names):
    # return the names of the users of which the overlay is highlighted
    # it's by checking there are white pixels there where the name of a user is

    results = []
    for row_idx, name in enumerate(sorted_names(names)):
        stripe_x = OVERLAY_X + 55
        stripe_y = OVERLAY_Y + row_idx * OVERLAY_ROWS_HEIGHT_AND_DISTANCE + 10
        stripe_length = 25
        stripe_width = 15
        stripe = img[stripe_y:stripe_y+stripe_width,
                     stripe_x:stripe_x + stripe_length]

        if config.getboolean("DISCORD_OVERLAY_DEBUG_MODE"):
            cv2.imwrite(
                f'cropped_imgs/overlay_monitor_stripes/{row_idx}.png', stripe)

        found = False
        for row in stripe:
            for pixel in row:
                # two very similiar-looking white shades can have vastly different hues,
                # thats's why the h_diff_tresh is set so high here
                if similiar_colour(tuple(pixel), (255, 255, 255), h_diff_thresh=1000):
                    results.append(name)
                    found = True
                    break
            if found:
                break

    return results


def sorted_names(names):
    # return names in the order they appear on the overlay
    return sorted(names, key=lambda x: x.lower())


if __name__ == '__main__':

    import keyboard

    while True:
        if keyboard.is_pressed('ctrl+r'):
            names = active_speaker_names(['FloatingOrange', 'jakub'])
            print(names)
