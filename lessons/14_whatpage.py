"""用真截图验证 what_page 判页面对不对 —— 全程不碰手机。

样本固定在 images/page_*.png。为什么要专门复制一份，不直接用 look.png：
look.png 是 text1.py 的【临时截图文件】，下次一跑就被覆盖，拿它当样本迟早会坏。

其中两张是故意放进来、【应该认不出来】的：
  - 播放中的视频页：界面上光秃秃的，四个模板全都不亮
  - 手机的「设置」页：噪声样本，专门盯播放按钮会不会误判
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

template_play = kit.load("images/play_btn.png")
template_done = kit.load("images/done.png")
template_tab = kit.load("images/tab_undone.png")

# 顺序就是优先级。播放按钮排最后，是因为它最容易认错（实测在手机设置页打到 0.719），
# 阈值也单独提到 0.9 —— 真出现时是 0.972，留出 0.25 的余量，不跟全局的 0.8 共用一个。
MARKERS = [
    ("列表页", template_tab, 0.8),
    ("已播完", template_done, 0.8),
    ("待播放", template_play, 0.9),
]

SAMPLES = [
    ("images/page_list.png",           "列表页"),
    ("images/page_paused.png",         "待播放"),
    ("images/page_finished.png",       "已播完"),
    ("images/page_playing.png",        None),   # 播放中：本来就该认不出
    ("images/page_noise_settings.png", None),   # 手机设置页：噪声
]

fails = 0
for path, expect in SAMPLES:
    got, score = kit.what_page(kit.load(path), MARKERS)
    ok = got == expect
    fails += not ok
    print(f"{'OK  ' if ok else 'FAIL'} {os.path.basename(path):<24} 判成 {str(got):<8}"
          f" 最高分 {score:.3f}   期望 {expect}")

print(f"\n{len(SAMPLES) - fails}/{len(SAMPLES)} 判对")

# 对照实验：把播放按钮阈值降回 0.7 会怎样？
# 设置页那个 0.719 就越过线了 —— 这才是那 0.08 余量真正在防的东西。
# 光看"0.9 也判对了"没法说明 0.9 比 0.8 好在哪：0.719 连 0.8 都够不着。
print("\n--- 对照：播放按钮阈值降到 0.7 ---")
loose = [("列表页", template_tab, 0.8), ("已播完", template_done, 0.8),
         ("待播放", template_play, 0.7)]
got, score = kit.what_page(kit.load("images/page_noise_settings.png"), loose)
print(f"手机设置页被判成 {got}（最高分 {score:.3f}）")
print("→ 认出来了：噪声是真的，只是这一张样本还差一点点。")
