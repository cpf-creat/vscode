"""测 wait_for 的三种"卡住"信号 —— 全程用假 shot，不碰手机。

以前 wait_for 是写在 text1.py 里的，这里得靠"只执行主循环之前那段"把它捞出来。
现在它住在 kit.py —— 工具函数本来就该放工具箱，测试直接 import 就行，
不用再对着 text1.py 玩切片了。
"""
import os
import sys
import time

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import kit

# 下面把 kit.shot 换成假函数（换的是 kit 里那个【名字】）。wait_for 内部那句 shot(...)
# 是去 kit 自己的名字表里查的，所以你换 kit.shot 它就一定吃得上。
# 真正的坑在另一头：如果这里写成 from kit import shot 再换本地那个，wait_for 完全不理会，
# 照样去截手机 —— 换名字，要换被调用方看得见的那个名字。
wait_for = kit.wait_for

template = kit.load("images/play_btn.png")


def run(title, timeout, **kw):
    print(f"--- {title} ---")
    t0 = time.time()
    result = wait_for(template, timeout=timeout, quiet=True, **kw)
    print(f"    -> 返回 {result}，实际耗时 {time.time() - t0:.1f} 秒\n")


# A. 手机一直截不到图 —— 不该白等满 timeout
def shot_dead(name, tries=5, delay=2):
    raise RuntimeError("假装掉线")

kit.shot = shot_dead
run("A. 一直截不到图（timeout=600）", 600)

# 拿一张真截图造两张有"纹理"的假画面：缩小再放大，形状糊掉但纹路还在，
# 免得纯黑/纯白图让 matchTemplate 算出乱七八糟的分数
base = kit.load("images/look.png")
small = cv2.resize(base, (base.shape[1] // 4, base.shape[0] // 4))
blurry = cv2.resize(small, (base.shape[1], base.shape[0]))
moved = np.roll(blurry, 120, axis=1)          # 往右挪 120 像素 = 画面"动过"

# B. 画面一动不动 —— 该被卡死检测逮住
def shot_still(name, tries=5, delay=2):
    return blurry.copy()

kit.shot = shot_still
run("B. 画面不动（timeout=600, stuck_after=3）", 600, stuck_after=3)

# C. 画面一直在动 —— 不该误判成卡死，应该老老实实跑满 timeout
toggle = [0]
def shot_moving(name, tries=5, delay=2):
    toggle[0] += 1
    return (blurry if toggle[0] % 2 else moved).copy()

kit.shot = shot_moving
run("C. 画面一直在动（timeout=5, stuck_after=2）", 5, stuck_after=2)
