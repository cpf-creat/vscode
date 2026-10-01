import os
import subprocess
import time

import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
ADB = os.path.join(ROOT, "tools", "platform-tools", "adb.exe")
THRESHOLD = 0.8


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


location = None
template = cv2.imread("images/template.png")
for i in range(0,3):

    back_home()
    before = shot("images/pipe_before.png")

    score, location = find(template, before)
    print(f"第{i+1}次尝试;相似度 {score:.3f}")
    if score >= THRESHOLD:
        print("找到，退出")
        break
else:
    print("\n试了 3 次都没找到，放弃。")
    print("注意：这里【不会】硬点，宁可不动也不乱点。")
    exit()

x, y = location
cx, cy = x + template.shape[1] // 2, y + template.shape[0] // 2
subprocess.run([ADB, "shell", "input", "tap", str(cx), str(cy)])
time.sleep(1.5)

after = shot("images/pipe_after.png")
print(f"点击后画面变化 {cv2.absdiff(before, after).mean():.1f}")
