"""亲手把"及格线"上下挪，看判定结果变 —— 全程不碰手机，只是读图算分。

玩法：改下面 LINE 那一个数 → 重跑 → 看输出变没变。
样本全是真截图，分数是死的，变的只有那条线。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

LINE = 0.85  # ← 只改这一个数，别的别动

play = kit.load("images/play_btn.png")     # 那个蓝底白三角的播放按钮模板

# 每一行是：(图, 这张图上【真的】有没有播放按钮)
SAMPLES = [
    ("images/page_paused.png",         "有"),
    ("images/page_noise_vivo.png",     "没有"),
    ("images/page_noise_settings.png", "没有"),
]

print(f"及格线 LINE = {LINE}\n")
for path, truth in SAMPLES:
    score, _ = kit.find(play, kit.load(path))   # find 返回 (最高分, 位置)，位置这里不用
    says = "有" if score >= LINE else "没有"     # ← 全部逻辑就这一行
    mark = "对" if says == truth else "错（误判！）"
    print(f"  {os.path.basename(path):<26} 分数 {score:.3f}   "
          f"它说：{says}   真的：{truth}   {mark}")
