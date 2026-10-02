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
import cv2

ROOT = os.path.dirname(os.path.abspath(__file__))   # kit.py 躺在项目根，自己所在的文件夹就是根
os.chdir(ROOT)
ADB = os.path.join(ROOT, "tools", "platform-tools", "adb.exe")


def shot(name):
    raw = subprocess.run([ADB, "exec-out", "screencap", "-p"], capture_output=True).stdout
    open(name, "wb").write(raw)
    img = cv2.imread(name)
    if img is None:
        print(f"截图失败：只拿到 {len(raw)} 字节。跑 adb devices 看手机是不是 offline")
        exit()
    return img


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
        print(f"读不到图：{path}（检查文件名和路径）")
        exit()
    return img

if __name__ == "__main__":
      # 只有【直接跑 kit.py】时才执行这里
      # import kit 的时候，整段被跳过
      print("我在测试 load 函数")
      img = load("images/template.png")
      print(img.shape)
