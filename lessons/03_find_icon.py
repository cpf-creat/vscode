import os
import subprocess
import time

import cv2

# ---- 相似度及格线 ----
# matchTemplate 永远会返回一个"最像的"结果，哪怕屏幕上根本没这个图标。
# 所以要自己定一条线：分数低于它，就当没找到，绝不点击。
THRESHOLD = 0.8

# ---- 找到项目根目录，并把"当前文件夹"切过去 ----
# 这样不管你在哪个文件夹运行脚本，下面的 images/xxx 都能找对地方。
# OpenCV 的 cv2.imread 读不了带中文的绝对路径，用相对路径可以绕开。
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

ADB = os.path.join(ROOT, "tools", "platform-tools", "adb.exe")

# ---- 要找的图标 ----
template = cv2.imread("images/template.png")
print("模板尺寸:", template.shape)

# ---- 回桌面 -> 截图 -> 找图，找不到就重来 ----
# 为什么要循环？因为 Home 键偶尔会被手机静默忽略，
# 那样截到的就是别的界面，自然找不到图标。
screen = None
location = None

for attempt in range(1, 4):
    # 1. 回桌面
    subprocess.run([ADB, "shell", "input", "keyevent", "3"])
    time.sleep(1.5)

    # 2. 截图
    shot = subprocess.run([ADB, "exec-out", "screencap", "-p"], capture_output=True).stdout
    open("images/screen.png", "wb").write(shot)

    # 3. 在整个屏幕里找图标
    screen = cv2.imread("images/screen.png")
    scores = cv2.matchTemplate(screen, template, cv2.TM_CCOEFF_NORMED)
    min_val, score, min_loc, location = cv2.minMaxLoc(scores)

    print(f"第 {attempt} 次尝试：相似度 {score:.3f}", end="  ")

    # 4. 分数够高才算找到
    if score >= THRESHOLD:
        print("[找到了]")
        break

    print("[不够像，可能没回到桌面，重试]")
else:
    print("\n试了 3 次都没找到，放弃。")
    print("注意：这里【不会】硬点，宁可不动也不乱点。")
    exit()

# ---- 5. 算出图标中心点 ----
# OpenCV 给的是左上角，点击要的是中心，所以要各加一半宽高
x, y = location
center_x = x + template.shape[1] // 2
center_y = y + template.shape[0] // 2
print("图标左上角:", location)
print("图标中心  :", center_x, center_y)

# ---- 6. 点它 ----
subprocess.run([ADB, "shell", "input", "tap", str(center_x), str(center_y)])
print("已点击")

