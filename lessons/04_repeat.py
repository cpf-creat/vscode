import os
import subprocess
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
ADB = os.path.join(ROOT, "tools", "platform-tools", "adb.exe")


def go_home_and_shot(save_path):
    subprocess.run([ADB, "shell", "input", "keyevent", "3"])
    shot = subprocess.run([ADB, "exec-out", "screencap", "-p"], capture_output=True).stdout
    open(save_path, "wb").write(shot)
    print("已截图 ->", save_path)


go_home_and_shot("images/step1.png")
go_home_and_shot("images/step2.png")
print("两次都做完了")
