#第一部分:导入工具
import os
import sys
import time
import cv2
import numpy as np

# kit.py 在项目根目录，而 Python 只在"脚本自己所在的文件夹"（雨课堂/）里找模块。
# 少了这两行，import kit 会报 ModuleNotFoundError —— 这一步就是告诉它根目录在哪儿。
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kit          # 自己写的工具箱：shot / find / load / tap_at / press_back / back_home

THRESHOLD = 0.8
MAX_SECTIONS = 3        # 先跑 3 节试水，确认稳了再往上调


#第二部分:只留【这个项目特有】的判断，通用的都在 kit 里了
def find_topmost(template, screen):
    """同一个东西在屏幕上出现好几遍时，只取【最靠上】的那个。
    minMaxLoc 只给一个"最像的"，位置随机，所以这里得自己把够像的都捞出来再挑。"""
    scores = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    ys, xs = np.where(scores >= THRESHOLD)         # 注意这里返回的是 行号(y)、列号(x)
    if len(xs) == 0:
        return None
    i = ys.argmin()                                # 行号最小的那个 = 最靠上的
    return int(xs[i]), int(ys[i])


def wait_for(template, timeout=10, quiet=False):
    start = time.time()
    while time.time() - start < timeout:
        try:
            screen = kit.shot("images/look.png")
        except RuntimeError as e:
            # kit.shot 自己已经重试过好几次了，还是不行 → 这一轮就当没图。
            # 别让一次抖动把整个脚本带走：跳过这轮继续等，说不定它自己就好了。
            # （等 30 分钟那个场景要是死在这里，前面全白等。）
            print(f"  [{time.time() - start:.1f}s] 截图失败，跳过这轮：{e}")
            continue                       # 回循环开头，再来一轮
        score, location = kit.find(template, screen)
        if not quiet:                      # 等 24 分钟时关掉，不然刷几百行
            print(f"  [{time.time() - start:.1f}s] 相似度 {score:.3f}")
        if score >= THRESHOLD:
            return location
        # time.sleep(0.5)
    return None


#模板只读一次，别放循环里反复读磁盘
#读不到会自己报出是哪个文件 —— 不用再写那 4 行 None 检查了
template = kit.load("images/play_btn.png")      # 大播放按钮 ▶
template2 = kit.load("images/done.png")         # 「已完成」三个字
template3 = kit.load("images/tab_undone.png")   # 「未完成」Tab
template4 = kit.load("images/chip_video.png")   # 每条课程左上角的「视频」小标签

CARD_DY = 194        # 从小标签【顶边】往下量到卡片正中的距离（923 - 729，都是量出来的）


#第三部分:主循环
# 每一轮都从「未完成」列表页出发 —— 跟 06_pipeline 开头先按 Home 是同一个道理：
# 做事之前，先把界面弄到一个【已知】状态，别指望手机碰巧停在哪儿。
cnt = 0
while cnt < MAX_SECTIONS:
    cnt += 1
    print(f"=== 第 {cnt} 节 ===")

    # ① 找「未完成」Tab 并点它。用找图，不写死坐标 —— 坐标会随机型/系统版本变，找图不会
    #    这一步顺便当了守卫：能找到这三个字，说明手机确实停在课程列表页
    tab = wait_for(template3, timeout=8, quiet=True)

    #    找不到？那多半是手机还停在【视频页】上（你手动去看了、或者上轮的返回没生效）。
    #    按一次返回就回到列表了。只退这一次：万一本来就在列表页、只是 Tab 变灰了，
    #    多退会把整个课程退出，越修越远。
    if tab is None:
        print("没看到「未完成」Tab，按一次返回再找")
        kit.press_back()
        time.sleep(2)
        tab = wait_for(template3, timeout=8, quiet=True)

    if tab is None:
        print("按了返回还是没看到列表，手机可能不在课程页，停")
        exit()

    kit.tap_at(tab[0] + template3.shape[1] // 2, tab[1] + template3.shape[0] // 2)
    time.sleep(1.5)

    # ② 进第一项
    #    做完的会自动从「未完成」消失、下一项顶上来 → 第一项【永远】是下一个要做的
    #    每张卡左上角都有个一模一样的「视频」小标签，屏幕上同时有好几个，
    #    取【最靠上】的那个就是第一项 —— 不写死坐标，列表滚了也不怕
    chip = find_topmost(template4, kit.shot("images/look.png"))
    if chip is None:
        print(f"没找到「视频」小标签（相似度都不到 {THRESHOLD}），停")
        exit()
    kit.tap_at(chip[0] + template4.shape[1] // 2, chip[1] + CARD_DY)
    time.sleep(3)

    # ③ 万一进了个已完成的：这不该发生（做完的会从列表消失），所以是异常，停下来看
    score_done, _ = kit.find(template2, kit.shot("images/look.png"))
    if score_done >= THRESHOLD:
        print("这节显示「已完成」，却还留在未完成列表里 —— 情况不对，停下来人工看看")
        exit()

    # ④ 等播放按钮出现
    t0 = time.time()
    location = wait_for(template, timeout=10)
    if location is None:
        print(f"等了 {time.time() - t0:.1f} 秒没出现播放按钮，放弃")
        exit()
    print(f"等到了，耗时 {time.time() - t0:.1f} 秒")

    # ⑤ 点它
    x, y = location
    kit.tap_at(x + template.shape[1] // 2, y + template.shape[0] // 2)
    time.sleep(4)

    # ⑥ 验证：大 ▶ 应该消失
    score2, _ = kit.find(template, kit.shot("images/after_tap.png"))
    print(f"点完后播放按钮相似度 {score2:.3f}")
    if score2 >= THRESHOLD:
        print("按钮还在，没点上，放弃")
        exit()

    # ⑦ 等视频播完
    print("播放中，等它结束……")
    if wait_for(template2, timeout=1800, quiet=True) is None:
        print("等了 30 分钟还没变成「已完成」，放弃")
        exit()
    print("这节播完了")

    # ⑧ 返回列表页，下一轮重新从 ① 开始
    kit.press_back()
    time.sleep(2)

print(f"\n跑完 {MAX_SECTIONS} 节，收工。")
