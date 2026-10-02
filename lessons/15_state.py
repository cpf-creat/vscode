"""用一串"排好队的假页面"把状态机跑一遍 —— 全程不碰手机。

思路：把几张真截图排成一个剧本，假的 shot 每被调用一次就吐下一张，
于是脚本自己就一路走了过去。我们只看两件事：
  1. 它每步干了什么（点卡片？点播放？按返回？）
  2. 最后记账记了几节

剧本是按【shot 被调用的顺序】排的 —— 注意"播放中"后面还跟着一张，
那张是给 wait_for 内部用的（它自己也会截图），别漏了这个。
"""
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import kit

NAMES = ["列表页", "待播放", "播放中", "已播完", "已播完(给wait_for用)", "空列表"]

# 造一张"空列表"：白底 + 只贴一个「未完成」Tab，一个「视频」小标签都没有 → 该收工
canvas = np.full((2800, 1260, 3), 255, np.uint8)
tab = kit.load("images/tab_undone.png")
canvas[500:500 + tab.shape[0], 200:200 + tab.shape[1]] = tab

script = [
    kit.load("images/page_list.png"),      # ① 在列表页 → 该点第一张卡
    kit.load("images/page_paused.png"),    # ② 进了课程但停着 → 该点播放
    kit.load("images/page_playing.png"),   # ③ 播起来了 → 该等「已完成」
    kit.load("images/page_finished.png"),  #    （这张被 wait_for 内部吃掉）
    kit.load("images/page_finished.png"),  # ④ 等到了 → 该记账 + 按返回
    canvas,                                # ⑤ 列表空了 → 该收工
]

# 自检：这张"空列表"上真的没有「视频」小标签吗？没有，这个测试才有意义
s = kit.find(kit.load("images/chip_video.png"), canvas)[0]
assert s < kit.THRESHOLD, f"空列表上居然有「视频」标签（{s:.3f}），收不了工"
print(f"空列表自检：「视频」小标签最高分 {s:.3f} < {kit.THRESHOLD}\n")

idx, shown = [0], [0]          # shown = 最近一次吐出去的是剧本里的第几张
def fake_shot(name, tries=5, delay=2):
    shown[0] = min(idx[0], len(script) - 1)      # 剧本演完了就停在最后一张
    idx[0] += 1
    return script[shown[0]].copy()

log = []
kit.shot = fake_shot
kit.tap_at = lambda x, y: log.append(("点击", shown[0], x, y))
kit.press_back = lambda: log.append(("返回", shown[0], 0, 0))
time.sleep = lambda s: None    # 免得测试真等十几秒 —— 这里测的是"决定"，不是耗时

path = os.path.join(ROOT, "雨课堂", "text1.py")
g = {"__file__": path, "__name__": "__main__"}
exec(compile(open(path, encoding="utf-8").read(), path, "exec"), g)

print("\n--- 它每步干了什么 ---")
for act in log:
    print(f"  {act[0]:<4} 当时屏幕上显示的是：{NAMES[act[1]]}")

# 期望：在列表页点卡片 → 在待播放页点播放 → 在已播完页按返回
want = ["点击", "点击", "返回"]
got = [a[0] for a in log]
ok1 = got == want
ok2 = g["done"] == 1
print(f"\n动作顺序 {got}，期望 {want} —— {'OK' if ok1 else 'FAIL'}")
print(f"记账 {g['done']} 节，期望 1 节 —— {'OK' if ok2 else 'FAIL'}")
