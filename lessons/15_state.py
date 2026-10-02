"""把状态机放在不同的"开局"下跑一跑 —— 全程不碰手机。

玩法：把几张真截图排成一个剧本，假的 shot 每被调用一次就吐下一张，
脚本自己就一路走了过去。我们只看两件事：
  1. 它每步干了什么（点卡片？点播放？按返回？）
  2. 最后记账记了几节

剧本是按【shot 被调用的顺序】排的 —— 注意 wait_for 内部也会截图（它要一遍遍轮询），
所以"播放中"后面还得跟一张，别漏了。

场景二是个真机上抓到的 bug：手机【本来就停在课程里】的时候，
"我在课程里"这件事以前要靠"我自己点过卡片"才知道，于是判断不出来，白退一趟。
"""
import os
import sys
import time

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import kit

real_wait_for = kit.wait_for        # 留着，场景一要用真的

# 造一张"空列表"：白底 + 只贴一个「未完成」Tab，一个「视频」小标签都没有 → 该收工
canvas = np.full((2800, 1260, 3), 255, np.uint8)
tab = kit.load("images/tab_undone.png")
canvas[500:500 + tab.shape[0], 200:200 + tab.shape[1]] = tab

s = kit.find(kit.load("images/chip_video.png"), canvas)[0]
assert s < kit.THRESHOLD, f"空列表上居然有「视频」标签（{s:.3f}），收不了工"
print(f"空列表自检：「视频」小标签最高分 {s:.3f} < {kit.THRESHOLD}\n")

F = kit.load("images/page_finished.png")


def play(title, names, script):
    """把剧本演一遍，返回 (它干了什么, 最后记账了几节)。"""
    print(f"========== {title} ==========")
    idx, shown = [0], [0]
    def fake_shot(name, tries=5, delay=2):
        shown[0] = min(idx[0], len(script) - 1)      # 剧本演完了就停在最后一张
        idx[0] += 1
        return script[shown[0]].copy()

    log = []
    kit.shot = fake_shot
    kit.wait_for = real_wait_for
    kit.tap_at = lambda x, y: log.append(("点击", shown[0]))
    kit.press_back = lambda: log.append(("返回", shown[0]))

    path = os.path.join(ROOT, "雨课堂", "text1.py")
    g = {"__file__": path, "__name__": "__main__"}
    try:
        exec(compile(open(path, encoding="utf-8").read(), path, "exec"), g)
    except SystemExit:
        print(">>> 脚本自己 exit() 了 —— 这条路它没走通")

    print("\n--- 它每步干了什么 ---")
    for act in log:
        print(f"  {act[0]:<4} 当时屏幕上显示的是：{names[act[1]]}")
    return log, g.get("done")


def check(what, ok):
    print(f"  {'OK  ' if ok else 'FAIL'}  {what}")
    return ok


# ---------- 场景一：正常做一节 ----------
script1 = [
    kit.load("images/page_list.png"),      # ① 列表页 → 点第一张卡
    kit.load("images/page_paused.png"),    # ② 进了课程但停着 → 点播放
    kit.load("images/page_playing.png"),   # ③ 播起来了 → 等「已完成」
    F,                                     #    （这张被 wait_for 内部吃掉）
    F,                                     # ④ 等到了 → 记账 + 返回
    canvas,                                # ⑤ 列表空了 → 收工
]
names1 = ["列表页", "待播放", "播放中", "已播完(给wait_for用)", "已播完", "空列表"]
log, done = play("场景一：正常做一节", names1, script1)
results = [
    check(f"动作顺序 {[a[0] for a in log]} == ['点击', '点击', '返回']",
          [a[0] for a in log] == ["点击", "点击", "返回"]),
    check(f"记账 {done} 节 == 1 节", done == 1),
]

# ---------- 场景二：启动时手机已经停在课程里（视频暂停着） ----------
# 这一步之后屏幕上什么都不亮 —— 必须认出"这是在播放"，不能当成陌生页面退出去。
script2 = [
    kit.load("images/page_paused.png"),    # ① 手机本来就停在课程里，暂停着 → 点播放
    kit.load("images/page_playing.png"),   # ② 播起来了 → 该认出「播放中」，绝不能按返回
    F,                                     #    （被 wait_for 吃掉）
    F,                                     # ③ 等到了 → 记账 + 返回
    F,
    canvas,
]
names2 = ["待播放(启动时就在这)", "播放中", "已播完(给wait_for用)", "已播完", "已播完", "空列表"]
log, done = play("场景二：启动时手机已经停在课程里", names2, script2)
results += [
    check("播放中那一步没有误按返回", ("返回", 1) not in log),
    check(f"记账 {done} 节 == 1 节", done == 1),
]

print(f"\n===== {sum(results)}/{len(results)} 通过 =====")
