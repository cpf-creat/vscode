#第一部分:导入工具
import os
import sys
import time

# kit.py 在项目根目录，而 Python 只在"脚本自己所在的文件夹"（雨课堂/）里找模块。
# 少了这两行，import kit 会报 ModuleNotFoundError —— 这一步就是告诉它根目录在哪儿。
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kit          # 工具箱：shot / find / load / tap_at / press_back / back_home
                    #         find_topmost / wait_for / THRESHOLD
                    # 凡是"跟哪个 App 无关"的都在 kit 里，这里只留雨课堂特有的

MAX_SECTIONS = 50       # 安全上限，不是目标：正常靠"「未完成」列表跑空"退出。
                        # while 循环 + "真的会去点你手机"的副作用 = 必须装个刹车，
                        # 万一哪天判定逻辑出问题，最多做 50 节就自己停。

STUCK_AFTER = 600       # 给 kit.wait_for 的卡死阈值：画面连续这么多秒一动没动就放弃。
                        # ⚠ 这是拍的估计值，没实测过：视频播到静止课件时画面本来就不动。
                        #   等下次有视频在播，量一下"播放时相邻帧的真实差异"再定。


#第二部分:模板和这个项目特有的参数（判断逻辑都搬进 kit 了）
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
done = 0          # 真正【做完】了几节 —— 只在整节跑完后才 +1，中途停的节不算数
while done < MAX_SECTIONS:
    print(f"=== 第 {done + 1} 节 ===")

    # ① 找「未完成」Tab 并点它。用找图，不写死坐标 —— 坐标会随机型/系统版本变，找图不会
    #    这一步顺便当了守卫：能找到这三个字，说明手机确实停在课程列表页
    tab = kit.wait_for(template3, timeout=8, quiet=True)

    #    找不到？那多半是手机还停在【视频页】上（你手动去看了、或者上轮的返回没生效）。
    #    按一次返回就回到列表了。只退这一次：万一本来就在列表页、只是 Tab 变灰了，
    #    多退会把整个课程退出，越修越远。
    if tab is None:
        print("没看到「未完成」Tab，按一次返回再找")
        kit.press_back()
        time.sleep(2)
        tab = kit.wait_for(template3, timeout=8, quiet=True)

    if tab is None:
        print("按了返回还是没看到列表，手机可能不在课程页，停")
        exit()

    kit.tap_at(tab[0] + template3.shape[1] // 2, tab[1] + template3.shape[0] // 2)
    time.sleep(1.5)

    # ② 进第一项
    #    做完的会自动从「未完成」消失、下一项顶上来 → 第一项【永远】是下一个要做的
    #    每张卡左上角都有个一模一样的「视频」小标签，屏幕上同时有好几个，
    #    取【最靠上】的那个就是第一项 —— 不写死坐标，列表滚了也不怕
    chip = kit.find_topmost(template4, kit.shot("images/look.png"))
    if chip is None:
        time.sleep(3)          # 也可能只是页面还没加载完 —— 给它第二次机会，别急着下结论
        chip = kit.find_topmost(template4, kit.shot("images/look.png"))
    if chip is None:
        # 一个「视频」小标签都找不到 = 「未完成」列表空了 = 全部做完。
        # 这就是断点续跑免费的原因：做完的课会从列表消失，重启后第一项自动是没做的那节。
        print("「未完成」列表里一个「视频」标签都找不到了 —— 全部做完，收工")
        break                  # 注意 done 没有 +1：这一节压根没做
    kit.tap_at(chip[0] + template4.shape[1] // 2, chip[1] + CARD_DY)
    time.sleep(3)

    # ③ 万一进了个已完成的：这不该发生（做完的会从列表消失），所以是异常，停下来看
    score_done, _ = kit.find(template2, kit.shot("images/look.png"))
    if score_done >= kit.THRESHOLD:
        print("这节显示「已完成」，却还留在未完成列表里 —— 情况不对，停下来人工看看")
        exit()

    # ④ 等播放按钮出现
    t0 = time.time()
    location = kit.wait_for(template, timeout=10)
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
    if score2 >= kit.THRESHOLD:
        print("按钮还在，没点上，放弃")
        exit()

    # ⑦ 等视频播完
    print("播放中，等它结束……")
    # quiet=True：30 分钟能跑一千多轮，不关掉会刷一千多行，把有用的信息全冲走
    # 超时/卡死都不再写死"30 分钟"，改成实报耗时 —— 因为卡死检测会提前返回
    t_end = time.time()
    if kit.wait_for(template2, timeout=1800, quiet=True, stuck_after=STUCK_AFTER) is None:
        print(f"等了 {time.time() - t_end:.0f} 秒还没变成「已完成」，放弃")
        exit()
    print("这节播完了")

    # ⑧ 这一节真做完了，才记账；然后回列表页，下一轮重新从 ① 开始
    done += 1
    
    kit.press_back()
    time.sleep(2)

print(f"\n收工，这次一共做了 {done} 节。")
