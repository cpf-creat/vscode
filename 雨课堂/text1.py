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


# ── 日志：把 print 的出口一分为二，屏幕一份、文件一份 ──
class Tee:
    """同时往【屏幕】和【文件】写。

    为什么不每处 print 后面再补一句写文件：跑一晚上，终端滚过去就没了。
    半夜崩了，手里没有任何记录 —— 停在第几步、当时判成了哪
    一页、等了多久，
    全不知道。而 print 一共十几处，漏一处就漏一块真相。

    最省事的办法是换掉 sys.stdout：代码里所有 print 一个字都不用改，
    出口却变成了两份 —— 连 kit 内部那些打印也一起收进来了。
    """
    def __init__(self, path):
        self.screen = sys.stdout        # ← 先存下【真正的屏幕】再说
                                        #   下面一句 sys.stdout 就被换成 Tee 自己了。
                                        #   要是这里直接写 self.screen = sys.stdout 之外的
                                        #   任何形式去"稍后再读"，拿到的就是它自己 ——
                                        #   然后 flush() 一调就无限递归。
        self.file = open(path, "a", encoding="utf-8")

    def write(self, text):
        self.screen.write(text)
        self.file.write(text)
        self.file.flush()               # 立刻落盘：被 Ctrl+C 打断也不丢最后几行

    def flush(self):
        self.screen.flush()
        self.file.flush()


os.makedirs("logs", exist_ok=True)      # kit 导入时已经 chdir 到项目根了
sys.stdout = Tee("logs/run.log")        # 从这一行起，下面所有 print 都自动写文件
sys.stderr = sys.stdout                 # 报错也走同一个出口。
                                        # 少了这一行，脚本一旦抛异常崩掉，那行 traceback
                                        # 只打在终端上、日志里没有 —— 事后翻日志只知道
                                        # "停在哪儿"，不知道"为什么停"。
                                        # （2026-10-02 就被这个坑卡住过一次破案）

print("=" * 60)
print(f"=== 新一次运行 {time.strftime('%Y-%m-%d %H:%M:%S')} ===")
print("=" * 60)


MAX_SECTIONS = 50       # 安全上限，不是目标：正常靠"「未完成」列表跑空"退出。
                        # while 循环 + "真的会去点你手机"的副作用 = 必须装个刹车，
                        # 万一哪天判定逻辑出问题，最多做 50 节就自己停。

MAX_STEPS = 200         # 总步数刹车。改成状态机之后，"一轮"可能只做半件事，
                        # 出口不像以前那么直观（比如点了播放但没点上，下一轮还是"待播放"），
                        # 所以给整个循环再上一道保险。

STUCK_AFTER = 30       # 给 kit.wait_for 的卡死阈值：画面连续这么多秒一动没动就抛异常。
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
PLAY_BTN_SCORE = 0.85   # 播放按钮的达标线。
                        # 抽出来是因为它要在【两个地方】用：认页面的 MARKERS，
                        # 和"待播放"分支里真正去点它时的 find_topmost。
                        # 两处写两个数，早晚会改了一处忘了另一处 —— 那时候
                        # what_page 说"认出来了"，find_topmost 却按老阈值找不到，返回 None，
                        # 下一行 loc[0] 当场崩。

MARKERS = [
    ("列表页", template3, 0.8),             # 「未完成」Tab 在 = 课程列表页
    ("已播完", template2, 0.8),             # 「已完成」在 = 这节播完了
    ("待播放", template,  PLAY_BTN_SCORE),  # 大播放按钮在 = 停着没播（刚进来，或被人暂停了）
]
# 播放按钮这个模板单独用 0.85，不跟别人共用 0.8 —— 它是最容易认错的一个。
# 手头的实测数据（都是全屏真截图）：
#   噪声（屏幕上压根没有播放按钮时的最高分）：蓝心小V 页 0.814、
#       手机「设置」页 0.719、其余十来张 0.58~0.72
#   真命中：0.923（真机上抓到的）、0.972（另一张暂停截图）
# 也就是说噪声摸得到 0.814，真命中低得到 0.923，中间只有 0.109 宽，线画哪儿都紧。
# 0.85 是把它放中间：离噪声 0.036，离真命中 0.073。
#
# ⚠ 这个模板本身就不是个好的标志物：播放按钮是【半透明】叠在视频上的，
#   底下画面不同它就长得不一样 —— 0.923 和 0.972 的差别就是这么来的。
#   以后要更稳，得换条路子（比如按颜色找那个蓝色圆），别在阈值上抠小数点。


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

    # 带上钟点。日志里光有"第几步"看不出"等了多久" ——
    # 23:15 写着"播放中"，下一条 23:52 才出现，中间 37 分钟就是那段等待。
    print(f"[{time.strftime('%H:%M:%S')}] === 第 {done + 1} 节 | 第 {steps} 步 | "
          f"现在在：{page or '不认识的页面'}（最高分 {score:.3f}）===")

    if page == "列表页":
        # ── 先把自己要的状态摆好：切到「未完成」页 ──
        # 「未完成 (40)」这几个字不选中也印在 tab 栏上，所以 tab_undone 连
        # 「学习日志」页也认 —— 它只能证明"这是课程页"，证明不了"这是未完成页"。
        # 不点这一下，下面就会拿「学习日志」里的第一条当目标，而那条是已完成的：
        # 点进去 → 已播完 → 退回来 → 再点同一条，原地打转。
        # 已经在「未完成」页时再点一次没有副作用，所以不用先判断自己在哪一页。
        tab = kit.find_topmost(template3, screen)
        if tab is not None:
            kit.tap_at(tab[0] + template3.shape[1] // 2, tab[1] + template3.shape[0] // 2)
            time.sleep(2)                              # 等列表换过来
            screen = kit.shot("images/look.png")       # 换了一批内容，得重新看一眼再挑

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
        loc = kit.find_topmost(template, screen, PLAY_BTN_SCORE)
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
                # 四分钟一动不动，"退回去看一眼"也看不出是暂停 —— 那就不是暂停，
                # 是路上撞进了一个压根不认识的页面（比如被点到了「我的习题集」）。
                # 【以前这里直接 exit()，整轮就断死在这个页面上】。
                # 现在按一次返回走开，并且把 in_course 清掉 ——
                # 关键就是清掉它：不清的话下一轮又会被判成"播放中"，
                # 转一圈回到同一句话上。清掉之后它才会被当成"陌生页面"接着往回退。
                print(f"连着 {stuck_count} 次画面都不动，不像是暂停 —— 按返回退出去重来")
                kit.press_back()
                in_course = False
                played = False
                stuck_count = 0
                time.sleep(2)
                continue
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

