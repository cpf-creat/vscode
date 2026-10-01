import os
import subprocess
import time

import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
ADB = os.path.join(ROOT, "tools", "platform-tools", "adb.exe")


def shot(name):
    raw = subprocess.run([ADB, "exec-out", "screencap", "-p"], capture_output=True).stdout
    open(name, "wb").write(raw)
    return cv2.imread(name)


subprocess.run([ADB, "shell", "input", "keyevent", "3"])
time.sleep(1.5)

before = shot("images/before.png")
subprocess.run([ADB, "shell", "input", "tap", "600", "2000"])
time.sleep(1)
after = shot("images/after.png")

print("画面变化程度:", round(cv2.absdiff(before, after).mean(), 1))
