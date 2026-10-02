"""电脑版雨课堂（www.yuketang.cn）的自动播放脚本。

跟手机版 text1.py 是【兄弟，不是替代】—— text1.py 一个字没动，两个可以并存。
两边共用 kit.py 里匹配那一层（find / what_page / wait_for），
差别只在 kit.BACKEND：手机走 adb，电脑走屏幕截图 + 鼠标。

── 这一版换了走法 ────────────────────────────────────────────────
上一版是"回列表页 → 点最上面一行 → 播完 → 再回列表"，来回跑。
这一版【不跑列表页了】：右上角有个 `>`，点一下就进下一节，顺着课往下走。

于是整个脚本只需要两个判断：
    1. 左上角那个类型标签，是不是「视频」？
    2. 右上角那个完成状态，是不是「已完成」？
其余的一律归到"不是视频 → 直接跳"，所以作业、讨论、
以及以后可能加的直播、测验，都不用各准备一个模板。

跑之前得先自己做好的事（脚本代替不了）：
  1. Edge 打开雨课堂，【点进任意一节】停在里面，并且已经登录
     （停在列表页不行 —— 脚本会告诉你，不会乱点）
  2. 别让别的窗口盖住 Edge —— kit.shot 会先把 Edge 提到最前，
     但前提是它找得到（找不到会直接报错，不会闷头截错窗口）
  3. 跑起来之后别动鼠标键盘 —— 鼠标是脚本在用的

跑法：python 雨课堂/pc.py
"""
import os
import sys
import time

import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import kit

# ── 区域：全部是程序量出来的，别凭感觉改 ────────────────────────────
# 格式是 (y0, y1, x0, x1)。为什么非得圈区域，看 score_in 的注释。
TAG_REGION  = (195, 240, 440, 720)      # 左上角类型标签那一格
DONE_REGION = (200, 235, 1680, 1745)    # 右上角「已完成」那一小格
NEXT_REGION = (198, 238, 1700, 1900)    # 右上角 详情 / < / > 那一带
PLAY_REGION = (590, 652, 458, 540)      # 视频底栏最左边那个播放键
TITLE_BOX   = (204, 228, 535, 1400)     # 标题那一行，用来判断"节换了没有"

SCREEN = "images_pc/look.png"

# ── 四个模板 ───────────────────────────────────────────────────
TAG_VIDEO = kit.load("images_pc/tag_video.png")     # 「视频」蓝标签   55x30
DONE_ALL  = kit.load("images_pc/done_all.png")      # 「已完成」       52x17
NEXT_TPL  = kit.load("images_pc/next_arrow.png")    # `>` 箭头         10x17
PLAY_TPL  = kit.load("images_pc/play_bar.png")      # 底栏播放键       64x46

# ── 节奏 ───────────────────────────────────────────────────────
POLL      = 4        # 视频在播时，每轮隔几秒看一眼
WAIT_PLAY = 3        # 点完播放键之后
WAIT_JUMP = 5        # 点完 `>` 之后，等新的一节加载出来
SAME_EPS  = 1.0      # 标题差小于它就算"节没换"。实测：同一节 0.00，不同节 31.93
STALL_MAX = 3        # 连点这么多下标题都不变，就认为这一节跳不过去
MAX_ROUNDS = 3000    # 纯粹是个"永不无限循环"的兜底，不是节奏控制


def score_in(template, screen, region, threshold=kit.THRESHOLD):
    """在 screen 的【指定区域】里找 template，只要"像不像"，不要坐标。

    为什么非圈区域不可：「已完成」和「完成度：62%」前两个字一模一样。
    不圈区域的话，一个根本没做完的视频页也能在 `完成度` 那儿拿到 0.788 ——
    离 0.8 的及格线只差 0.012。那不叫余量，那叫巧合，换一天就翻车。

    圈到 x >= 1680 就干净了：「已完成」是【右对齐】的，右端钉死在 1740，
    所以已经完成的时侯它从 1689 起、从不往左越过 1680；而没完成时的
    `完成度：62%` 从 1632 起，整段都在框外。
    实测：已完成页 1.000，没做完的视频页 0.209，列表页 0.017。
    """
    y0, y1, x0, x1 = region
    score, _ = kit.find(template, screen[y0:y1, x0:x1])
    return score


def find_next(screen):
    """右上角那个 `>` 在哪、有多像。返回 (得分, 全屏坐标)。

    这里必须把区域的偏移【加回去】：kit.find 是在切出来的小图上找的，
    它返回的坐标是相对那张小图的。忘了加回去的后果非常阴 ——
    脚本照样"有点击、有坐标、不报错"，只是点在屏幕左上角某个不相干的地方。
    """
    y0, y1, x0, x1 = NEXT_REGION
    score, (bx, by) = kit.find(NEXT_TPL, screen[y0:y1, x0:x1])
    return score, (bx + x0, by + y0)


def title_of(screen):
    """标题那一行的像素。用来判断"这一节换了没有"。"""
    y0, y1, x0, x1 = TITLE_BOX
    return screen[y0:y1, x0:x1]


def main():
    stall = 0                          # 连点 `>` 但标题不动，攒了几次

    for i in range(MAX_ROUNDS):
        screen = kit.shot(SCREEN)

        # ① 右上角有没有 `>`？这一条同时管两件事：
        #    在列表页/别的页面上没有它（实测 0.270），课程走到头大概也没有。
        nscore, (nx, ny) = find_next(screen)
        if nscore < kit.THRESHOLD:
            print(f"右上角找不到 `>`（最高只有 {nscore:.3f}，需要 {kit.THRESHOLD}）。")
            print("两种情况：① 你得先【点进某一节】再跑，别停在列表页；")
            print("          ② 课已经走到最后一节了。")
            return

        video  = score_in(TAG_VIDEO, screen, TAG_REGION)
        done   = score_in(DONE_ALL,  screen, DONE_REGION)
        paused = score_in(PLAY_TPL,  screen, PLAY_REGION)

        is_video = video >= kit.THRESHOLD
        is_done  = done  >= kit.THRESHOLD
        print(f"[{i:>4}] 标签 {video:.3f} 已完成 {done:.3f} 播放键 {paused:.3f} "
              f"| {'视频' if is_video else '非视频'} / {'已完成' if is_done else '没做完'}")

        # ② 只有【是视频，而且还没做完】才值得停下来等。其余一律往下走。
        if is_video and not is_done:
            if paused >= kit.THRESHOLD:
                # 认得出播放键 = 它是停着的。点它正中间 —— 模板给的是左上角，
                # 64x46 的图差 30 像素就点到旁边了。
                _, (px, py) = kit.find(PLAY_TPL, screen)
                h, w = PLAY_TPL.shape[:2]
                print("       └ 它是停着的，点一下播放")
                kit.tap_at(px + w // 2, py + h // 2)
                time.sleep(WAIT_PLAY)
            # 认不出播放键 = 底栏收起来了 = 正在播。这才是正常的等待状态，什么都不做。
            time.sleep(POLL)
            continue

        # ③ 走到这儿就是该跳了：非视频（作业/讨论/…），或者视频已经完成。
        print(f"       └ {'已完成' if is_done else '不是视频'}，点 `>` 进下一节")
        kit.tap_at(nx + NEXT_TPL.shape[1] // 2, ny + NEXT_TPL.shape[0] // 2)
        time.sleep(WAIT_JUMP)

        # ④ 跳过去没有？拿标题比一比。实测同一节 0.00、不同节 31.93，差得非常远，
        #    所以这个 SAME_EPS 是量的不是猜的。
        after = kit.shot(SCREEN)
        if cv2.absdiff(title_of(screen), title_of(after)).mean() < SAME_EPS:
            stall += 1
            print(f"       └ 标题没变（第 {stall}/{STALL_MAX} 次）—— 这一节没跳过去")
            if stall >= STALL_MAX:
                print("连点几下都不动，停。大概是这一节必须自己手动做完才让跳。")
                return
        else:
            stall = 0

    print("轮数跑满了（这只是防死循环的兜底）。停下来看看是不是卡住了。")


if __name__ == "__main__":
    main()
