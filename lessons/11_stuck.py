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


def run(title, timeout, expect, **kw):
    """跑一种情况，看它是不是抛出了【该抛的那个】异常。

    expect 是要期待的异常类；expect=None 表示"该正常等满超时、什么都不抛"。
    光看"抛了异常"不够 —— 抛错类型等于把'手机掉了'当成'画面卡住'去自救，白忙。
    """
    print(f"--- {title} ---")
    t0 = time.time()
    try:
        result = wait_for(template, timeout=timeout, quiet=True, **kw)
        got, detail = None, f"返回 {result}（正常等满超时）"
    except kit.WaitFailed as e:
        got, detail = type(e), f"抛出 {type(e).__name__}：{e}"
    ok = got is expect
    want = expect.__name__ if expect else "None（正常超时，不抛）"
    print(f"    {detail}")
    print(f"    {'OK  ' if ok else 'FAIL'} 耗时 {time.time() - t0:.1f} 秒，期望 {want}\n")
    return ok


# A. 手机一直截不到图 —— 该抛 OfflineError（这种自救没用，只能 reconnect）
def shot_dead(name, tries=5, delay=2):
    raise RuntimeError("假装掉线")

kit.shot = shot_dead
passed = [run("A. 一直截不到图（timeout=600）", 600, kit.OfflineError)]

# 拿一张真截图造两张有"纹理"的假画面：缩小再放大，形状糊掉但纹路还在，
# 免得纯黑/纯白图让 matchTemplate 算出乱七八糟的分数。
#
# 底图必须挑【确定没有播放按钮】的：这里用列表页（实测播放按钮只有 0.309）。
# 别用 look.png —— 它是"暂停的视频页"，上面就有个播放按钮，
# 模糊一下照样匹配得上，那 B、C 就变成在测"找到播放按钮"了，测了个寂寞。
base = kit.load("images/page_list.png")
small = cv2.resize(base, (base.shape[1] // 4, base.shape[0] // 4))
blurry = cv2.resize(small, (base.shape[1], base.shape[0]))
moved = np.roll(blurry, 120, axis=1)          # 往右挪 120 像素 = 画面"动过"

# 自检：先证明这张假画面上真的没有播放按钮，证明不了就别往下测。
# （README 里那条 —— 曾经拿 template[:50,:50] 当"假模板"，结果跟原位一模一样，相似度 1.000）
self_check = kit.find(template, blurry)[0]
assert self_check < kit.THRESHOLD, f"假画面自己就含播放按钮（{self_check:.3f}），换个底图"
print(f"假画面自检：播放按钮相似度 {self_check:.3f} < {kit.THRESHOLD}，"
      f"可以作为『找不到』的底图\n")

# B. 画面一动不动 —— 该被卡死检测逮住
def shot_still(name, tries=5, delay=2):
    return blurry.copy()

kit.shot = shot_still
passed.append(run("B. 画面不动（timeout=600, stuck_after=3）", 600, kit.StuckError,
                  stuck_after=3))

# C. 画面一直在动 —— 不该误判成卡死，应该老老实实跑满 timeout
toggle = [0]
def shot_moving(name, tries=5, delay=2):
    toggle[0] += 1
    return (blurry if toggle[0] % 2 else moved).copy()

kit.shot = shot_moving
passed.append(run("C. 画面一直在动（timeout=5, stuck_after=2）", 5, None, stuck_after=2))

print(f"{sum(passed)}/{len(passed)} 符合预期")
