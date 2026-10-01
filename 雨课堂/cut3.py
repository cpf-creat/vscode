"""切出「视频」小标签当模板，并当场自测：用切它的那张图去匹配，应该回到原点、满分。"""
import os

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

big = cv2.imread("images/temp.png")
if big is None:
    print("没读到 images/temp.png")
    exit()

Y0, Y1, X0, X1 = 729, 792, 112, 238
chip = big[Y0:Y1, X0:X1]
cv2.imwrite("images/chip_video.png", chip)
print("模板 images/chip_video.png", chip.shape, "= (高, 宽, 通道)")

# 自测：拿同一张图去匹配，应该只有一份满分答案在 (X0, Y0)
scores = cv2.matchTemplate(big, chip, cv2.TM_CCOEFF_NORMED)
ys, xs = np.where(scores >= 0.8)
print(f"整屏匹配到 {len(xs)} 处（应该等于屏幕上卡片数）：")
for i in np.argsort(ys):
    print(f"  y={ys[i]:>4}  x={xs[i]:>4}   分数 {scores[ys[i], xs[i]]:.3f}")
