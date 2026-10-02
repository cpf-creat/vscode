#第一部分:导入工具
import os
import sys
import time

# kit.py 在项目根目录，而 Python 只在"脚本自己所在的文件夹"（雨课堂/）里找模块。
# 少了这两行，import kit 会报 ModuleNotFoundError —— 这一步就是告诉它根目录在哪儿。
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kit          # 工具箱：shot / find / load / tap_at / press_back / back_home
                    #         find_topmost / wait_for / what_page / THRESHOLD
                    # 凡是"跟哪个 App 无关"的都在 kit 里，这里只留雨课堂特有的

MAX_SECTIONS = 50       # 安全上限，不是目标：正常靠"「未完成」列表跑空"退出。
                        # while 循环 + "真的会去点你手机"的副作用 = 必须装个刹车，
                        # 万一哪天判定逻辑出问题，最多做 50 节就自己停。

MAX_STEPS = 200         # 总步数刹车。改成状态机之后，"一轮"可能只做半件事，
                        # 出口不像以前那么直观（比如点了播放但没点上，下一轮还是"待播放"），
                        # 所以给整个循环再上一道保险。

STUCK_AFTER = 100       # 给 kit.wait_for 的卡死阈值：画面连续这么多秒一动没动就抛异常。
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

# 认页面的名单：(页面名, 模板, 阈值)。顺序就是优先级，从上往下比，谁先达标算谁。
# 名单在这里给，不在 kit 里 —— kit 不认识雨课堂，"哪张图代表哪一页"只有这里知道。
MARKERS = [
    ("列表页", template3, 0.8),     # 「未完成」Tab 在 = 课程列表页
    ("已播完", template2, 0.8),     # 「已完成」在 = 这节播完了
    ("待播放", template,  0.9),     # 大播放按钮在 = 停着没播（刚进来，或被人暂停了）
]
# 放最后那行阈值是 0.9 而不是 0.8：这个模板最容易认错 —— 实测在手机「设置」页
# 能蒙到 0.719，离 0.8 只剩 0.08。真出现时是 0.972，所以卡到 0.9 才安全。


#第三部分:主循环 —— 每轮【看一眼在哪个页面，只做一件事】
# 跟上一版最大的区别：不再是"从头到尾走一遍固定流程"，而是"看现在在哪 → 做该做的那一步 → 再回头看"。
# 好处是中途被打断、或者跑之前手机就已经停在视频页，它都能自己接上，不用退出去重来。
in_course = False   # 是不是【点进某个课程里了】。专门用来解那个"认不出来的页面"：
                    # 课程里屏幕上一片空白 = 正在播；不在课程里还认不出 = 陌生页面，该退回去。
done = 0            # 真正【做完】了几节
steps = 0           # 走了多少步（防呆）
while done < MAX_SECTIONS and steps < MAX_STEPS:
    steps += 1
    screen = kit.shot("images/look.png")
    page, score = kit.what_page(screen, MARKERS)
    if page is None and in_course:
        page = "播放中"      # 课程里四个标志物全不亮，那只能是正在播 —— 靠记忆补出来
    print(f"=== 第 {done + 1} 节 | 第 {steps} 步 | 现在在：{page or '不认识的页面'}"
          f"（最高分 {score:.3f}）===")

    if page == "列表页":
        # 做完的会自动从「未完成」消失、下一项顶上来 → 第一项【永远】是下一个要做的
        chip = kit.find_topmost(template4, screen)
        if chip is None:
            time.sleep(3)               # 也可能只是页面还没加载完，给第二次机会
            chip = kit.find_topmost(template4, kit.shot("images/look.png"))
        if chip is None:
            print("列表上一个「视频」标签都没有了 —— 全部做完，收工")
            break                       # 注意 done 没有 +1：这一节压根没做
        kit.tap_at(chip[0] + template4.shape[1] // 2, chip[1] + CARD_DY)
        in_course = True
        time.sleep(3)

    elif page == "待播放":
        # 走到这儿有两种可能：刚点进课程还没开始播；或者播到一半被人按了暂停。
        # 两种都该做同一件事 —— 点它。所以"暂停自救"不用另写代码，它就是这一步。
        loc = kit.find_topmost(template, screen, 0.9)
        # 这里不查 loc is None：what_page 刚用同一个模板、同一个阈值在这张图上认出了
        # "待播放"，那 find_topmost 必然也找得到。同一个计算不用查两遍。
        print("点播放")
        kit.tap_at(loc[0] + template.shape[1] // 2, loc[1] + template.shape[0] // 2)
        time.sleep(4)

    elif page == "播放中":
        print("播放中，等它结束……")
        try:
            found = kit.wait_for(template2, timeout=1800, quiet=True, stuck_after=STUCK_AFTER)
        except kit.WaitFailed as e:
            print(f"出事了：{e}")       # ← 第 4 步会在这里接上"先看看是不是暂停了"
            exit()
        if found is None:
            print("等满 30 分钟还没变成「已完成」，放弃")
            exit()

    elif page == "已播完":
        if in_course:
            # 只有【自己点进去的】才记账。启动时手机要是正好停在一个播完的页面上，
            # 那不是这一轮做的，记了就成了虚报。
            done += 1
            print(f"这节做完了，累计 {done} 节")
        kit.press_back()
        in_course = False
        time.sleep(2)

    else:
        # 既没有页面标志，也不在课程里 —— 手机不知道停在哪个界面上了。
        # 按一次返回：这是【有把握】的那一步（跟以前"只退一次"是同一个道理）。
        print("这个页面不认识，按一次返回看看")
        kit.press_back()
        time.sleep(2)

print(f"\n收工，这次一共做了 {done} 节。")
