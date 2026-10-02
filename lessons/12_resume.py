"""测"未完成列表跑空 → 收工"这条路径。

全程用假的屏幕和空操作的按键，一次都不会碰手机。
假屏幕 = 白底 + 贴一个「未完成」Tab：
  - 步骤① wait_for(template3) 能过（找到 Tab）
  - 步骤② find_topmost(template4) 找不到（没有「视频」小标签）→ 该判定"全部做完"
"""
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import kit

# 造假屏幕
canvas = np.full((2800, 1260, 3), 255, np.uint8)
tab = kit.load("images/tab_undone.png")
canvas[500:500 + tab.shape[0], 200:200 + tab.shape[1]] = tab
print(f"假屏幕做好：{canvas.shape}，「未完成」Tab 贴在 (200, 500)")

# 先确认这张假屏幕上真的没有「视频」小标签 —— 不然测个寂寞
chip_tpl = kit.load("images/chip_video.png")
scores = cv2.matchTemplate(canvas, chip_tpl, cv2.TM_CCOEFF_NORMED)
print(f"假屏幕上「视频」小标签的最高相似度：{np.nanmax(scores):.3f}（要 < 0.8 才有意义）\n")


def fake_shot(name, tries=5, delay=2):
    return canvas.copy()


# 全部换成假货 —— 绝不碰手机
kit.shot = fake_shot
kit.tap_at = lambda x, y: None
kit.press_back = lambda: None
kit.back_home = lambda: None

path = os.path.join(ROOT, "雨课堂", "text1.py")
g = {"__file__": path, "__name__": "__main__"}
exec(compile(open(path, encoding="utf-8").read(), path, "exec"), g)
