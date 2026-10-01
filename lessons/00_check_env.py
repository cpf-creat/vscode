"""
第 00 课：环境自检

作用：一键检查你的电脑是否具备了写自动化脚本的全部条件。
运行：python lessons/00_check_env.py

如果全部显示 [OK]，就可以进入第 01 课了。
"""
import os
import subprocess
import sys

# 让中文在 Windows 控制台正常显示
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 项目根目录：本文件在 lessons/ 下，所以往上一级
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB = os.path.join(ROOT, "tools", "platform-tools", "adb.exe")

LINE = "=" * 54


def check_python():
    """检查 Python 和三个核心库是否装好"""
    print(f"\n{LINE}\n[1/2] Python 环境\n{LINE}")
    print(f"  Python   : {sys.version.split()[0]}")
    print(f"  解释器   : {sys.executable}")

    all_ok = True
    for label, module_name in [("OpenCV", "cv2"), ("numpy", "numpy"), ("Pillow", "PIL")]:
        try:
            module = __import__(module_name)
            print(f"  {label:<9}: {getattr(module, '__version__', '?')}")
        except ImportError:
            print(f"  {label:<9}: [缺失]  请运行 pip install {module_name}")
            all_ok = False
    return all_ok


def run_adb(*args):
    """调用 adb 命令，统一处理编码和超时"""
    return subprocess.run(
        [ADB, *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )


def parse_devices(output):
    """把 adb devices 的输出解析成 [(序列号, 状态), ...]"""
    devices = []
    for line in output.splitlines()[1:]:
        line = line.strip()
        if not line or line.startswith("*"):
            continue
        parts = line.split()
        if len(parts) >= 2:
            devices.append((parts[0], parts[1]))
    return devices


def check_adb():
    """检查 adb 程序，并列出当前连接的手机"""
    print(f"\n{LINE}\n[2/2] adb 与手机连接\n{LINE}")

    if not os.path.exists(ADB):
        print(f"  adb      : [缺失] 找不到文件\n             {ADB}")
        return False
    print(f"  adb      : [OK]")

    try:
        version_out = run_adb("version").stdout
        print(f"  版本     : {version_out.strip().splitlines()[0]}")
    except Exception as exc:
        print(f"  版本     : [失败] {exc}")
        return False

    # 列出设备
    try:
        output = run_adb("devices").stdout
    except Exception as exc:
        print(f"  设备检测 : [失败] {exc}")
        return False

    devices = parse_devices(output)
    if not devices:
        print("  已连手机 : 没有检测到设备")
        print("\n  >>> 请按下面 3 步连接你的手机：")
        print("      1. 手机用数据线插到电脑（注意：有些线只能充电）")
        print("      2. 手机设置里打开【USB 调试】")
        print("      3. 手机弹出【允许 USB 调试吗？】→ 点【允许】")
        return False

    all_ok = True
    for serial, status in devices:
        if status == "device":
            print(f"  已连手机 : [OK] {serial}")
        elif status == "unauthorized":
            print(f"  已连手机 : [未授权] {serial}")
            print("             >>> 看手机屏幕，点【允许 USB 调试】")
            all_ok = False
        elif status == "offline":
            print(f"  已连手机 : [离线] {serial}")
            print("             >>> 拔掉数据线重插一次")
            all_ok = False
        else:
            print(f"  已连手机 : [{status}] {serial}")
            all_ok = False
    return all_ok


def main():
    print("\n" + LINE)
    print("   环境自检 —— adb + OpenCV 自动化")
    print(LINE)

    python_ok = check_python()
    adb_ok = check_adb()

    print(f"\n{LINE}\n[结果]\n{LINE}")
    print(f"  Python 环境 : {'[OK] 通过' if python_ok else '[X] 有问题，见上方提示'}")
    print(f"  手机连接    : {'[OK] 通过' if adb_ok else '[X] 还没连上，见上方提示'}")

    if python_ok and adb_ok:
        print("\n  全部就绪，可以开始第 01 课了。")
    else:
        print("\n  按上面的提示修好后，重新运行本脚本即可。")
    print()


if __name__ == "__main__":
    main()
