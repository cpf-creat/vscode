"""只测不点：看一眼模板在当前屏幕上的相似度。用来做正/负样本测试。"""
import os
import subprocess

import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
ADB = os.path.join(ROOT, "tools", "platform-tools", "adb.exe")
def shot(name):
    raw = subprocess.run([ADB, "exec-out", "screencap", "-p"], capture_output=True).stdout
    open(name, "wb").write(raw)


def find(template, screen):
    scores = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, score, _, location = cv2.minMaxLoc(scores)
    return score, location


template = cv2.imread("images/done.png")
if template is None:
    print("模板没读到，检查 images/done.png")
    exit()

shot("images/test_now.png")
screen = cv2.imread("images/test_now.png")

score, location = find(template, screen)
print(f"「已完成」相似度 = {score:.3f}")
print(f"它指的位置     = {location}")
