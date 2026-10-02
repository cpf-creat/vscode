import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kit

print("① 开工")
try:
    img = kit.load("images/nothing.png")
    print("② 加载成功")
except FileNotFoundError as e:
    print(f"③ 接住了，它说：{e}")

print("④ 脚本还活着")


import time

# 假截图：前两次装死，第三次才成功 —— 剧本我说了算
count = 0
def fake_shot(name):
    global count          # 函数里要改外面的 count，得先声明 global
    count += 1
    if count < 3:
        raise RuntimeError(f"假装第 {count} 次掉线")
    return f"{name} 的图"


print("--- 测重试 ---")
for i in range(3):
    try:
        img = fake_shot("images/look.png")
        print(f"  第 {i+1} 次成功：{img}")
        break                          # 成功 → 跳出循环
    except RuntimeError as e:
        print(f"  第 {i+1} 次失败：{e}")
        time.sleep(1)                  # 真代码里，这里换成 adb reconnect
else:                                  # 循环跑完都没 break = 三次全失败
    print("  三次都没成功，放弃")