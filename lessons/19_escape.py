"""测"中途撞进一个不认识的页面，脚本能不能自己退出来" —— 全程不碰手机。

真机上出的 bug（2026-10-02）：
  手机被点到了「我的习题集」—— 一个跟课程毫无关系、而且画面一动不动的页面。
  开局就在陌生页面，它救得回来：那时 in_course 还是 False，走"不认识的页面"分支，按返回。
  但【中途】撞进去时 in_course 已经是 True，它就被一直判成"播放中"：
    等 60 秒 → 卡死 → "退回去看看" → 还是认不出 → 又判成"播放中" → …… 死循环。
  第 4 次撞完，老代码直接 exit()，整轮就断死在这个页面上。

这个测试就排这个剧本，只看两件事：
  1. 它有没有从那个页面上按返回走开（而不是死守到底）
  2. 它有没有半路 exit() —— 应该一路跑到「收工」才对

注意剧本里【先是真视频页】：得先点一下播放，把 in_course 弄成 True，
才复现得出"中途撞进去"这个前提。开局就在陌生页面是另一条路（那条一直是好的）。
"""
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import kit

# 随便一张"跟课程无关、又一动不动"的页面。先用 14_whatpage 验过的噪声样本。
FOREIGN = kit.load("images/page_noise_settings.png")

# 先自检：这张图上【什么标志物都不亮】，否则"陌生页面"这个前提就不成立，测个寂寞
print("陌生页面自检（四个标志物都得低于各自的线）：")
for nm, th in (("play_btn", 0.85), ("done", 0.8), ("tab_undone", 0.8), ("chip_video", 0.8)):
    s, _ = kit.find(kit.load(f"images/{nm}.png"), FOREIGN)
    assert s < th, f"{nm} 在这张图上 {s:.3f} ≥ {th} —— 它就不算陌生页面了"
    print(f"  {nm:<11} {s:.3f} < {th}  OK")
print()

# 造一张"空列表"：白底 + 只贴一个「未完成」Tab，一个「视频」标签都没有 → 该收工
canvas = np.full((2800, 1260, 3), 255, np.uint8)
tab = kit.load("images/tab_undone.png")
canvas[500:500 + tab.shape[0], 200:200 + tab.shape[1]] = tab

# 剧本（假的 shot 每被叫一次吐下一张）：
#   待播放 → 陌生的页面（×5，一直不动）→ 空列表
N_FOREIGN = 5
script = [kit.load("images/page_paused.png")] + [FOREIGN] * N_FOREIGN + [canvas]
NAMES = ["待播放(先在这点一下播放)"] + ["陌生的页面"] * N_FOREIGN + ["空列表"]

idx, shown = [0], [0]
def fake_shot(name, tries=5, delay=2):
    shown[0] = min(idx[0], len(script) - 1)      # 剧本演完了就停在最后一张
    idx[0] += 1
    return script[shown[0]].copy()

def fake_wait_for(template, timeout=10, quiet=False, stuck_after=None, threshold=None):
    raise kit.StuckError("假装画面一直一动不动")

log = []
kit.shot = fake_shot
kit.wait_for = fake_wait_for
kit.tap_at = lambda x, y: log.append(("点击", shown[0]))
kit.press_back = lambda: log.append(("返回", shown[0]))
time.sleep = lambda s: None

exited = [False]
path = os.path.join(ROOT, "雨课堂", "text1.py")
g = {"__file__": path, "__name__": "__main__"}
try:
    exec(compile(open(path, encoding="utf-8").read(), path, "exec"), g)
except SystemExit:
    exited[0] = True

print("\n--- 它每步干了什么 ---")
for act in log:
    print(f"  {act[0]:<4} 当时屏幕上显示的是：{NAMES[act[1]]}")

foreign = [i for i, n in enumerate(NAMES) if n == "陌生的页面"]
escaped = any(("返回", i) in log for i in foreign)
print()
print(f"从陌生页面上按了返回（自己逃出来）—— {'OK' if escaped else 'FAIL'}")
print(f"没有半路 exit() —— {'OK' if not exited[0] else 'FAIL'}")
