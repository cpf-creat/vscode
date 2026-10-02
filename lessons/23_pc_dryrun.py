"""拿手上所有截图，把 pc.py 的【判定逻辑】空跑一遍 —— 一个鼠标事件都不发。

这是新脚本上机之前唯一安全的验证方式：判断对不对，先离线看，
别拿真页面去撞。以后每次改了 pc.py 的判据，都应该再加几张截图进来跑这个。
"""
import os
import sys

import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "雨课堂"))
import kit
import pc

# 截图 → 期望它被判成什么
CASES = [
    ("_z1",        "点播放"),     # 视频页 62%，停着，控制条亮着
    ("_pc_test",   "点播放"),     # 视频页 60%，停着
    ("_pc_row1",   "等（在播）"),  # 视频页 61%，在播，控制条收起来了
    ("_pc_done",   "跳下一节"),   # 视频页 已完成
    ("_m1",        "跳下一节"),   # 视频页 已完成
    ("_pc_list",   "报错停住"),   # 列表页 —— 没有 `>`，应该当场拦住
    ("_pc_filter", "报错停住"),
]


def decide(screen):
    """照抄 pc.main() 里那三步判断，只是不点鼠标。"""
    nscore, _ = pc.find_next(screen)
    if nscore < kit.THRESHOLD:
        return "报错停住", nscore
    is_video = pc.score_in(pc.TAG_VIDEO, screen, pc.TAG_REGION) >= kit.THRESHOLD
    is_done = pc.score_in(pc.DONE_ALL, screen, pc.DONE_REGION) >= kit.THRESHOLD
    if is_video and not is_done:
        paused = pc.score_in(pc.PLAY_TPL, screen, pc.PLAY_REGION) >= kit.THRESHOLD
        return ("点播放" if paused else "等（在播）"), nscore
    return "跳下一节", nscore


print(f"{'截图':<12}{'标签':>7}{'已完成':>8}{'播放键':>8}{'  >  ':>8}{'  判定':<12}期望")
print("-" * 76)

bad = 0
for name, want in CASES:
    s = cv2.imread(f"logs/{name}.png")
    v = pc.score_in(pc.TAG_VIDEO, s, pc.TAG_REGION)
    d = pc.score_in(pc.DONE_ALL, s, pc.DONE_REGION)
    p = pc.score_in(pc.PLAY_TPL, s, pc.PLAY_REGION)
    got, nscore = decide(s)
    mark = "" if got == want else "   <<< 不符"
    bad += got != want
    print(f"{name:<12}{v:>7.3f}{d:>8.3f}{p:>8.3f}{nscore:>8.3f}  {got:<12}{want}{mark}")

print()
print("全部符合" if bad == 0 else f"有 {bad} 张不符，判据还得改")
