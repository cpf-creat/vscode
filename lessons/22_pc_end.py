"""盯一件事：视频播完的那一刻，「完成度：NN%」会自己变成「已完成」吗？

pc.py 整套逻辑都押在这上面 —— 如果它不变，脚本会在视频页上一直等下去。
这个只能真跑一个视频看到尾才知道，所以专门写个探针。

它【只读】：一个鼠标事件都不发。你手动把视频点开、让它播，
这里只负责每隔 20 秒打一行。视频播到头的时候看最后几行就行。

上一版这个探针里我用 kit.tap_at 去"挪鼠标" —— tap_at 是【点击】不是移动，
等于在视频正中间点了一下，把视频点停了，整轮数据全废。记着这一笔。

跑法：python lessons/22_pc_end.py
"""
import os
import sys
import time

import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "雨课堂"))
import kit
import pc

GAP = 20
ROUNDS = 120          # 120 轮 × 20 秒 = 40 分钟

print("这个探针不动鼠标。请自己把视频点开播着，让它播到完。")
print()
print(f"{'时间':<10}{'轮':<5}{'标签':>8}{'已完成':>9}{'播放键':>9}   说明")
print("-" * 68)

prev = None
for i in range(ROUNDS):
    s = kit.shot("images_pc/look.png")
    v = pc.score_in(pc.TAG_VIDEO, s, pc.TAG_REGION)
    d = pc.score_in(pc.DONE_ALL, s, pc.DONE_REGION)
    p = pc.score_in(pc.PLAY_TPL, s, pc.PLAY_REGION)

    note = ""
    if prev is not None and prev < kit.THRESHOLD <= d:
        note = "★ 「已完成」刚刚出现了！"
    elif prev is not None and prev >= kit.THRESHOLD > d:
        note = "「已完成」又没了"
    prev = d

    print(f"{time.strftime('%H:%M:%S'):<10}{i:<5}{v:>8.3f}{d:>9.3f}{p:>9.3f}   {note}", flush=True)
    time.sleep(GAP)
