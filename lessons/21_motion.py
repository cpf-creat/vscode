"""量一件事：视频【真在播】的时候，相邻两帧到底差多少？

为什么必须量：老代码用 wait_for(..., stuck_after=60) 判"卡死"，
意思是"画面连续 60 秒一动不动 → 当成被暂停了"。
但这个信号成立的前提是"在播就一定在动" —— 而雨课堂的视频是录屏 PPT，
播到一页静止的课件时，画面本来就几乎不动。前提一破，它就会误判，
然后白按一次返回，把一个【正在播】的视频退掉。

所以要边量边打标签：每一轮同时算两个数
  ① 屏幕现在像哪一页   → 这是"标签"，告诉我们当时的真实状态
  ② 跟上一帧差多少     → 这是"读数"
标签和读数对上了，才能说"播放中的画面差多少"。

两个统计量一起看，因为它们问的问题不一样：
  mean  = 平均每个像素变了几个灰度    → 一小块在动会被整屏摊薄
  占比  = 变化超过 10 的像素占多少    → 少数像素大变 / 整屏微抖 分得开
"""
import os
import sys
import time

import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import kit

MARKERS = [
    ("列表页", kit.load("images/tab_undone.png"), 0.8),
    ("已播完", kit.load("images/done.png"), 0.8),
    ("待播放", kit.load("images/play_btn.png"), 0.85),
]

ROUNDS = 60      # 60 轮
GAP = 3          # 每轮睡 3 秒 → 相邻两帧正好隔 3 秒左右

groups = {}      # 标签 → [(mean, 占比), ...]，最后按标签分组看
prev = None

print(f"{'时间':<9}{'屏幕现在像哪一页':<14}{'最高分':<8}{'mean':<9}{'占比>10'}")
print("-" * 52)
for _ in range(ROUNDS):
    s = kit.shot("logs/_motion.png")          # 写 logs/ 而不是 images/，不碰脚本用的 look.png
    page, score = kit.what_page(s, MARKERS)
    label = page or "认不出"                   # 「播放中」就是"在课程里但认不出"

    if prev is not None:
        d = cv2.absdiff(s, prev)
        mean = float(d.mean())
        ratio = float((d.max(axis=2) > 10).mean())
        groups.setdefault(label, []).append((mean, ratio))
        print(f"{time.strftime('%H:%M:%S')}  {label:<14}{score:.3f}   {mean:8.3f} {ratio * 100:7.2f}%")

    prev = s
    time.sleep(GAP)

print("\n=== 按标签分组 ===")
for label, vals in groups.items():
    ms = sorted(v[0] for v in vals)
    rs = sorted(v[1] for v in vals)
    n = len(vals)
    print(f"{label:<14} n={n:<3}  mean 最小 {ms[0]:7.3f}  中位 {ms[n // 2]:7.3f}  最大 {ms[-1]:7.3f}"
          f"   |   占比 最小 {rs[0] * 100:6.2f}%  中位 {rs[n // 2] * 100:6.2f}%  最大 {rs[-1] * 100:6.2f}%")
print(f"\n现在的判定线：MOVE_EPS = {kit.MOVE_EPS}（比的是 mean）")
