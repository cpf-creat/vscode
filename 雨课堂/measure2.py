"""量「视频」「计分」两个小标签的边界：在小窗口里找非白像素的连续行列。"""
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

img = cv2.imread("images/temp.png")

Y0, Y1 = 690, 800           # 第一项那两个小标签所在的一小条
X0, X1 = 80, 420
win = img[Y0:Y1, X0:X1].astype(int)
ink = np.abs(win - 255).max(axis=2) > 12       # 不是纯白 = 有东西


def runs(counts, offset):
    out, i = [], 0
    while i < len(counts):
        if counts[i] > 0:
            s = i
            while i < len(counts) and counts[i] > 0:
                i += 1
            out.append((offset + s, offset + i - 1))
        else:
            i += 1
    return out


for a, b in runs(ink.sum(axis=0), X0):
    print(f"  列 {a:>4} ~ {b:>4}   宽 {b - a + 1}")
for a, b in runs(ink.sum(axis=1), Y0):
    print(f"  行 {a:>4} ~ {b:>4}   高 {b - a + 1}")
