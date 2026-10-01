"""量卡片边界：取画面右侧一条没有字的横带，逐行算平均色。卡片=浅紫，缝=纯白。"""
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

img = cv2.imread("images/temp.png")
print("shape", img.shape)

Y0, Y1 = 400, 1750          # 只看列表这一竖段
X0, X1 = 880, 1050          # 卡片右侧空白，躲开标题和右边那个时钟图标
strip = img[Y0:Y1, X0:X1].mean(axis=1)      # 每行一个平均色 (B, G, R)

start = 0
last = strip[0]
for i in range(1, len(strip)):
    if np.abs(strip[i] - last).max() > 3:
        b, g, r = last
        print(f"  y {Y0 + start:>4} ~ {Y0 + i - 1:>4}   RGB({r:3.0f},{g:3.0f},{b:3.0f})")
        start, last = i, strip[i]
b, g, r = last
print(f"  y {Y0 + start:>4} ~ {Y0 + len(strip) - 1:>4}   RGB({r:3.0f},{g:3.0f},{b:3.0f})")
