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
shot("images/temp.png")