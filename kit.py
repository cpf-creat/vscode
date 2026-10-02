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

ROOT = os.path.dirname(os.path.abspath(__file__))   # kit.py 躺在项目根，自己所在的文件夹就是根
os.chdir(ROOT)
ADB = os.path.join(ROOT, "tools", "platform-tools", "adb.exe")


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

if __name__ == "__main__":
      # 只有【直接跑 kit.py】时才执行这里
      # import kit 的时候，整段被跳过
      print("我在测试 load 函数")
      img = load("images/template.png")
      print(img.shape)
