"""测"视频播到一半被人按了暂停，脚本能不能自己救回来" —— 全程不碰手机。

剧本（假的 shot 每被叫一次吐下一张）：
  列表页 → 列表页(切完Tab) → 待播放 → 播放中 → 【被暂停了】→ 待播放 → 播放中 → 已播完 → 已播完 → 空列表
                               ↑                          ↑
                            第一次进播放          画面不动了，退回去看一眼，
                                                 发现是「待播放」→ 该自己去点播放

注意「列表页」后面跟两张：脚本点完「未完成」Tab 会【重新截一张】再挑卡片，
所以第二张才是它真正下手的依据。

这里直接用假的 kit.wait_for 抛 StuckError，不真跑卡死检测 ——
"wait_for 会不会在画面不动时抛 StuckError"已经在 11_stuck.py 单独验过了。
这个测试只管一件事：**抛出来之后，状态机接不接得住。**
"""
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import kit

NAMES = ["列表页", "列表页(切完Tab)", "待播放", "播放中", "待播放(被暂停了!)", "播放中",
         "已播完", "已播完(给wait_for用)", "空列表"]

canvas = np.full((2800, 1260, 3), 255, np.uint8)
tab = kit.load("images/tab_undone.png")
canvas[500:500 + tab.shape[0], 200:200 + tab.shape[1]] = tab

script = [
    kit.load("images/page_list.png"),
    kit.load("images/page_list.png"),      # ← 点完「未完成」Tab 后重新截的那一张
    kit.load("images/page_paused.png"),
    kit.load("images/page_playing.png"),
    kit.load("images/page_paused.png"),    # ← 暂停就发生在这儿
    kit.load("images/page_playing.png"),
    kit.load("images/page_finished.png"),
    kit.load("images/page_finished.png"),
    canvas,
]

idx, shown = [0], [0]
def fake_shot(name, tries=5, delay=2):
    shown[0] = min(idx[0], len(script) - 1)
    idx[0] += 1
    return script[shown[0]].copy()

# 假 wait_for：第一次抛"画面不动"，第二次当作等到了「已完成」
calls = [0]
def fake_wait_for(template, timeout=10, quiet=False, stuck_after=None, threshold=None):
    calls[0] += 1
    if calls[0] == 1:
        raise kit.StuckError("假装画面卡住了")
    return (100, 100)

log = []
kit.shot = fake_shot
kit.wait_for = fake_wait_for
kit.tap_at = lambda x, y: log.append(("点击", shown[0]))
kit.press_back = lambda: log.append(("返回", shown[0]))
time.sleep = lambda s: None

path = os.path.join(ROOT, "雨课堂", "text1.py")
g = {"__file__": path, "__name__": "__main__"}
try:
    exec(compile(open(path, encoding="utf-8").read(), path, "exec"), g)
except SystemExit:
    print("\n>>> 脚本自己 exit() 了 —— 这条路它没走通")

print("\n--- 它每步干了什么 ---")
for act in log:
    print(f"  {act[0]:<4} 当时屏幕上显示的是：{NAMES[act[1]]}")

# 关键就看这一条：暂停之后，它有没有在「待播放」上自己点一次播放
# 按名字查下标，不写死数字 —— 剧本里加一张图，这行不用跟着改
PAUSED = NAMES.index("待播放(被暂停了!)")
rescued = ("点击", PAUSED) in log
print(f"\n暂停后自己点回了播放（在'{NAMES[PAUSED]}'上点过）—— {'OK' if rescued else 'FAIL'}")
print(f"记账 {g.get('done')} 节，期望 1 节 —— {'OK' if g.get('done') == 1 else 'FAIL'}")
