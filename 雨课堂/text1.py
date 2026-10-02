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

STUCK_AFTER = 60       # 给 kit.wait_for 的卡死阈值：画面连续这么多秒一动没动就抛异常。
                        # ⚠ 这是拍的估计值，没实测过：视频播到静止课件时画面本来就不动。
                        #   等下次有视频在播，量一下"播放时相邻帧的真实差异"再定。

MAX_STUCK = 3           # "画面不动"最多忍几次。理由是：这个信号分不清两件事 ——
                        #   a) 视频真被暂停了  → 回去看会看到「待播放」，点一下就救回来（好事）
                        #   b) 视频在放静止课件 → 回去看还是「播放中」，什么也做不了（白等）
                        # 两种都拦着不给放弃，碰上 b 就会无限空转。所以给个次数上限。
                        # 每忍一次要等满 STUCK_AFTER 秒，3 次 ≈ 5 分钟，不冤。


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
in_course = False   # 我在不在某个课程里。专门用来解那个"认不出来的页面"：
                    # 课程里屏幕上一片空白 = 正在播；不在课程里还认不出 = 陌生页面，该退回去。
played = False      # 这一节【我点过播放没有】。专门用来决定记账算不算数：
                    # 启动时手机要是正好停在一个播完的页面上，那是上一轮做完的，不是我做的。
done = 0            # 真正【做完】了几节
steps = 0           # 走了多少步（防呆）
stuck_count = 0     # 连着几次"画面不动"了。每次真的做成了点什么（点了播放/换了页）就清零
while done < MAX_SECTIONS and steps < MAX_STEPS:
    steps += 1
    screen = kit.shot("images/look.png")
    page, score = kit.what_page(screen, MARKERS)
    if page is None and in_course:
        page = "播放中"      # 课程里标志物全不亮，那只能是正在播 —— 靠记忆补出来

    # 「待播放」只可能出现在课程里（播放按钮就长在视频上）。所以看到它就等于确认
    # "我在课程里" —— 不必非得是我自己点进去的才知道。
    # 少了这一句，手机本来就停在课程里时（上一轮的遗留、或者你手动点进去看了看），
    # 点完播放屏幕变成一片空白，就会被当成"陌生页面"退出课程，白跑一趟。
    if page == "待播放":
        in_course = True

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
        played = False      # 新的一节，还没播过
        time.sleep(3)

    elif page == "待播放":
        # 走到这儿有两种可能：刚点进课程还没开始播；或者播到一半被人按了暂停。
        # 两种都该做同一件事 —— 点它。所以"暂停自救"不用另写代码，它就是这一步。
        loc = kit.find_topmost(template, screen, 0.9)
        # 这里不查 loc is None：what_page 刚用同一个模板、同一个阈值在这张图上认出了
        # "待播放"，那 find_topmost 必然也找得到。同一个计算不用查两遍。
        print("点播放")
        kit.tap_at(loc[0] + template.shape[1] // 2, loc[1] + template.shape[0] // 2)
        in_course = True    # 播放按钮就长在视频上，点得到它就说明在课程里
        played = True       # 这一节是我点起来的，等会儿播完要记账
        stuck_count = 0     # 真的做了点什么 = 有进展，之前那些"画面不动"一笔勾销
        time.sleep(4)

    elif page == "播放中":
        print("播放中，等它结束……")
        try:
            found = kit.wait_for(template2, timeout=1800, quiet=True, stuck_after=STUCK_AFTER)
        except kit.OfflineError as e:
            # 手机掉了。这种自救没意义 —— 连屏幕都拍不到，还能点什么？
            # 重试也没用：shot() 内部已经 reconnect 过 5 次了，扛不住的是物理断连。
            print(f"手机掉了：{e}")
            exit()
        except kit.StuckError as e:
            # 画面不动了。最常见的原因就是【视频被人按了暂停】——
            # 而暂停的时候，大播放按钮是会显出来的。
            # 所以别在这儿急着下结论，退回去重新看一眼页面：
            # 真要是暂停了，上面的「待播放」分支会自己把播放点回去。
            # 自救不需要单独写一段代码，它就是"再看一眼"。
            stuck_count += 1
            if stuck_count > MAX_STUCK:
                print(f"连着 {stuck_count} 次画面都不动，不像是暂停，放弃")
                exit()
            print(f"画面不动了（第 {stuck_count}/{MAX_STUCK} 次）—— 退回去看看在哪一页")
            continue
        if found is None:
            print("等满 30 分钟还没变成「已完成」，放弃")
            exit()
        stuck_count = 0     # 等到了，说明这回是真播完了

    elif page == "已播完":
        stuck_count = 0
        if played:
            # 只有【我点过播放的】才记账。启动时手机要是正好停在一个播完的页面上，
            # 那是上一轮做完的，记了就成了虚报。
            # 用 played 而不是 in_course：手机本来就停在课程里时 in_course 也可能是 True，
            # 但那不表示这一节是我做的。
            done += 1
            print(f"这节做完了，累计 {done} 节")
        kit.press_back()
        in_course = False
        played = False
        time.sleep(2)

    else:
        # 既没有页面标志，也不在课程里 —— 手机不知道停在哪个界面上了。
        # 按一次返回：这是【有把握】的那一步（跟以前"只退一次"是同一个道理）。
        print("这个页面不认识，按一次返回看看")
        kit.press_back()
        in_course = False
        played = False
        time.sleep(2)

print(f"\n收工，这次一共做了 {done} 节。")
