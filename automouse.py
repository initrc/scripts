import pyautogui
import random
import time

r = lambda: random.randint(0, 1) * 2 - 1
while True:
    pyautogui.move(r(), r())
    time.sleep(298)

