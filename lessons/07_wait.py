import os
import subprocess
import time

import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
ADB = os.path.join(ROOT, "tools", "platform-tools", "adb.exe")
THRESHOLD = 2


def shot(name):
    raw = subprocess.run([ADB, "exec-out", "screencap", "-p"], capture_output=True).stdout
    open(name, "wb").write(raw)
    return cv2.imread(name)


def back_home():
    subprocess.run([ADB, "shell", "input", "keyevent", "3"])
    time.sleep(1.5)


def find(template, screen):
    scores = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, score, _, location = cv2.minMaxLoc(scores)
    return score, location

def wait_for(template, timeout=10):
    start = time.time()
    while time.time() - start < timeout:
        screen = shot("images/wait_temp.png")
        score, location = find(template, screen)
        print(f"  [{time.time() - start:.1f}s] 相似度 {score:.3f}")
        if score >= THRESHOLD:
            return location
        #time.sleep(0.5)
    return None

template = cv2.imread("images/template.png")
back_home()
t0 = time.time()
location = wait_for(template, timeout=10)
if location is None:
    print(f"等了 {time.time() - t0:.1f} 秒没出现，放弃")
    exit()
print(f"等到了，耗时 {time.time() - t0:.1f} 秒")


x, y = location
cx, cy = x + template.shape[1] // 2, y + template.shape[0] // 2
subprocess.run([ADB, "shell", "input", "tap", str(cx), str(cy)])
time.sleep(1.5)


