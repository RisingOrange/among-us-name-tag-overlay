import keyboard
import time

pause = True

def hotkey_loop():
    while True:
        if keyboard.is_pressed('ctrl+alt+y'):
            print('pause toggled')
            global pause
            pause = not pause
        time.sleep(0.5)

hotkey_loop()