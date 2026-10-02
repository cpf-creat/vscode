"""adb + OpenCV 的公共工具箱。全项目的脚本都从这里拿函数，别再各自复制一份。

怎么用：
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import kit

    screen = kit.shot("images/x.png")
    score, location = kit.find(template, screen)
"""
import os
import subprocess
import time

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.abspath(__file__))   # kit.py 躺在项目根，自己所在的文件夹就是根
os.chdir(ROOT)
ADB = os.path.join(ROOT, "tools", "platform-tools", "adb.exe")

THRESHOLD = 0.8        # 相似度及格线。matchTemplate 永远会返回一个"最像的"，哪怕只有三分像
MOVE_EPS = 0.5         # 相邻两张截图差异小于它 = 画面没动（完全静止是 0.0，在播时远大于它）
MAX_SHOT_FAIL = 5      # wait_for 里连续这么多次截不到图就别等了（手机像是真掉了）
SCREEN_PATH = "images/look.png"   # wait_for 的临时截图存这儿（kit 导入时已 chdir 到项目根）


def shot(name, tries=5, delay=2):
    """截图。手机偶尔会丢一两次 screencap，所以内建重试：失败了先 reconnect 再试。

    重试节奏（tries / delay）是 shot 自己的事 —— "再试一次"本来就包含"等一下"。
    而 back_home 后面要等多久，取决于下一句要干什么，只有调用者知道，所以那个 sleep 留在外面。
    """
    for i in range(tries):
        raw = subprocess.run([ADB, "exec-out", "screencap", "-p"], capture_output=True).stdout
        open(name, "wb").write(raw)
        img = cv2.imread(name)
        if img is not None:
            return img
        print(f"  第 {i+1}/{tries} 次截图失败（只拿到 {len(raw)} 字节），reconnect 后重试…")
        subprocess.run([ADB, "reconnect"], capture_output=True)
        time.sleep(delay)
    raise RuntimeError(f"截了 {tries} 次都失败，手机可能真的掉了")


def find(template, screen):
    scores = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    _, score, _, location = cv2.minMaxLoc(scores)
    return score, location

def tap_at(x, y):
    subprocess.run([ADB, "shell", "input", "tap", str(x), str(y)])


def press_back():
    subprocess.run([ADB, "shell", "input", "keyevent", "4"])


def back_home():
    subprocess.run([ADB, "shell", "input", "keyevent", "3"])

def load(path):
    img = cv2.imread(path)
    if img is None:
        #exit():直接结束
        #raise:把错误说成人话抛出
        raise FileNotFoundError(f"读不到图：{path}（检查文件名和路径）")
    return img

def find_topmost(template, screen, threshold=THRESHOLD):
    """同一个东西在屏幕上出现好几遍时，只取【最靠上】的那个。

    minMaxLoc 只给一个"最像的"，位置随机，所以这里得自己把够像的都捞出来再挑。
    注意捞到的是【一片】位置而不是一个 —— 滑动窗口挪 1 像素画面几乎没变，
    相邻位置分数照样很高，所以别把捞到的个数当成"屏幕上有几个"。
    """
    scores = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    ys, xs = np.where(scores >= threshold)     # 注意这里返回的是 行号(y)、列号(x)
    if len(xs) == 0:
        return None
    i = ys.argmin()                            # 行号最小的那个 = 最靠上的
    return int(xs[i]), int(ys[i])


def what_page(screen, markers):
    """看一眼现在在哪一页。

    markers 是调用者给的名单：[(页面名, 模板, 阈值), ...]
    —— kit 不认识任何 App，页面叫什么名字、拿什么当标志，只有写脚本的人知道。

    返回 (页面名, 得分)：认得出就给页面名，一个都不达标就给 (None, 最高分)。
    认不出也把最高分带出来，是为了分得清"完全不像"和"差一点点" ——
    只返回一个 None 的话，出问题只能靠猜。

    【名单的顺序就是优先级】：从上往下比，谁先达标就返回谁。
    所以"标志物比较容易认错的页面"要往后放。
    """
    best_name, best_score = None, 0.0
    for name, template, threshold in markers:
        score, _ = find(template, screen)
        if score > best_score:
            best_name, best_score = name, score          # 记着目前看到的最像的，认不出时好报告
        if score >= threshold:
            return name, score
    return None, best_score


def wait_for(template, timeout=10, quiet=False, stuck_after=None, threshold=THRESHOLD):
    """等 template 出现，最多等 timeout 秒。找到返回 (x, y)，没等到返回 None。

    timeout 不是"睡这么久"，是"给这个循环这么多秒的额度"：
    它一遍遍地截图→比对，每轮约 1 秒，所以 1800 约等于 1800 轮。

    quiet:       True = 不打印每轮相似度（等 30 分钟会刷一千多行）
    stuck_after: 画面连续这么多秒一动没动 → 认为卡死，提前放弃。None = 不检查。
                 有坑：视频播到静止课件时画面本来就不动，值别设太小。
    """
    start = time.time()
    last_screen = None          # 上一轮的截图，用来判断画面动没动
    last_move = start           # 上一次画面"动过"的时刻
    fails = 0                   # 连续截图失败次数

    while time.time() - start < timeout:
        try:
            screen = shot(SCREEN_PATH)
            fails = 0                          # 截到一次就清零
        except RuntimeError as e:
            # shot 自己已经重试过好几次了，还是不行 → 这一轮就当没图。
            # 别让一次抖动把整个脚本带走：跳过这轮继续等，说不定它自己就好了。
            fails += 1
            print(f"  [{time.time() - start:.1f}s] 第 {fails}/{MAX_SHOT_FAIL} 次截图失败：{e}")
            if fails >= MAX_SHOT_FAIL:
                print(f"  连续 {MAX_SHOT_FAIL} 次都截不到图，手机像是真掉了，不等了")
                return None
            continue                           # 回循环开头，再来一轮

        score, location = find(template, screen)
        if not quiet:                          # 等 30 分钟那种要关掉，不然刷一千多行
            print(f"  [{time.time() - start:.1f}s] 相似度 {score:.3f}")
        if score >= threshold:
            return location

        # 画面动过就把"静止"计时归零。完全静止时 absdiff 是 0.0，在播时远大于 MOVE_EPS
        if last_screen is not None and cv2.absdiff(screen, last_screen).mean() > MOVE_EPS:
            last_move = time.time()
        last_screen = screen

        if stuck_after and time.time() - last_move > stuck_after:
            print(f"  画面已经 {stuck_after} 秒一动没动，像是卡死了，不等了")
            return None

    return None


if __name__ == "__main__":
      # 只有【直接跑 kit.py】时才执行这里
      # import kit 的时候，整段被跳过
      print("我在测试 load 函数")
      img = load("images/template.png")
      print(img.shape)
