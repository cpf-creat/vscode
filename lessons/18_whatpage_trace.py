"""把 what_page 跑一遍，每算一个模板就报一次分数 —— 看它内部到底怎么走的。

不复制代码：把 kit.find 换成"会说话的"版本，what_page 自己就会一路报数。
（what_page 内部那句 find(...) 是去 kit 自己的名字表里查的，所以换 kit.find 它一定吃得上）
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

real_find = kit.find                    # 先把真的 find 收好

def chatty_find(template, screen):      # 再造一个"会说话"的
    score, loc = real_find(template, screen)
    print(f"        算出 {score:.3f}")
    return score, loc                   # 返回值一模一样，只是中间插了一句打印

kit.find = chatty_find                  # 换掉

MARKERS = [
    ("列表页", kit.load("images/tab_undone.png"), 0.8),
    ("已播完", kit.load("images/done.png"),       0.8),
    ("待播放", kit.load("images/play_btn.png"),   0.85),
]

for path in ["images/page_list.png",        # 真的是列表页
             "images/page_noise_vivo.png",  # 屏幕上啥标志都没有
             "images/page_playing.png"]:    # 同上
    print(f"=== 看这张：{os.path.basename(path)} ===")
    name, score = kit.what_page(kit.load(path), MARKERS)
    print(f"  → 结论：{name}，最高分 {score:.3f}\n")
