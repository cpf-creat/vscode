import subprocess

#存储工具位置
ADB = r"D:\adb + OpenCV自动化脚本\tools\platform-tools\adb.exe"


#执行home键返回主页面命令
#subprocess.run([ADB, "shell", "input", "keyevent", "3"])
print("手机应该返回桌面")


#执行tap键实施点击操作，“600”,"2000"是点击位置
#subprocess.run([ADB, "shell", "input", "tap", "600","2000"])
print("手机应该打开了一个app")
