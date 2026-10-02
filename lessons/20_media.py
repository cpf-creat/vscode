"""边看屏幕边问系统：视频真的在播的时候，微信到底报不报 media session？

为什么要同时记两样：
  单看 media_session 说"没出现"，证明不了任何事 —— 可能它就是不报，
  也可能我采样的那几秒视频压根没在播。两个原因在这里长得一模一样。

  所以每一轮同时问两个独立的问题：
    ① 屏幕上是什么？   → 用项目自己那三个模板判（待播放 = 停着，认不出 = 在播或陌生页）
    ② 系统说有东西在播吗？→ dumpsys media_session
  对齐了才能下结论："屏幕明明是正在播的视频，系统却一声不吭" —— 这才叫证明。

跑法：python lessons/20_media.py   （跑之前先把手机摆好，跑起来就别碰它）
"""
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import kit

# 就用 text1.py 那三个标志物。注意这里【没有】"播放中" —— 它不是靠模板认出来的，
# 是"在课程里 + 一个标志物都不亮"推出来的。所以视频在播时它会显示"认不出"。
MARKERS = [
    ("列表页", kit.load("images/tab_undone.png"), 0.8),
    ("已播完", kit.load("images/done.png"), 0.8),
    ("待播放", kit.load("images/play_btn.png"), 0.85),
]

ROUNDS = 60          # 60 轮 ≈ 3 分钟（截图本身要花 1 秒左右）
GAP = 2              # 每轮之间歇 2 秒

print("时间      屏幕现在像哪一页        最高分   微信报会话了没   系统说有东西在播吗")
print("-" * 78)
for _ in range(ROUNDS):
    screen = kit.shot("logs/_probe.png")
    page, score = kit.what_page(screen, MARKERS)

    # 问系统。这里【不滤包名】—— 谁报了就原样看到谁，别提前假定是微信。
    raw = subprocess.run(
        [kit.ADB, "shell", "dumpsys", "media_session"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    ).stdout

    wechat = "package=com.tencent.mm" in raw      # 微信建会话了没
    playing = "state=PLAYING" in raw              # 有没有谁在播
    print(f"{time.strftime('%H:%M:%S')}  {page or '认不出（可能正在播）':<16} "
          f"{score:.3f}    {'有' if wechat else '没有':<12} {'有人在播' if playing else '没有'}")
    time.sleep(GAP)
