"""
adb 工具模块 —— 你的"手机遥控器"

把常用的 adb 命令封装成 Python 函数。
以后每一课都会 import 它，不用重复写命令。

用法：
    import adb_kit as adb
    adb.tap(600, 1400)
"""
import os
import subprocess
import sys
import time

# 项目根目录（本文件在 lessons/ 里，往上一级）
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADB = os.path.join(ROOT, "tools", "platform-tools", "adb.exe")
IMAGES = os.path.join(ROOT, "images")

DEFAULT_TIMEOUT = 30

# PNG 文件的开头和结尾固定是这两段字节，用来自检数据有没有损坏
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
PNG_END = b"IEND\xaeB`\x82"


class AdbError(RuntimeError):
    """adb 操作失败时抛出，带中文提示"""


def setup_console():
    """让中文在 Windows 控制台正常显示（每个脚本开头调一次）"""
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass


def _run(args, timeout=DEFAULT_TIMEOUT):
    """执行 adb 命令，返回原始 bytes（截图是二进制，不能当文本处理）"""
    try:
        return subprocess.run([ADB, *args], capture_output=True, timeout=timeout)
    except FileNotFoundError:
        raise AdbError(f"找不到 adb 程序：{ADB}")
    except subprocess.TimeoutExpired:
        raise AdbError(f"adb 命令超时（超过 {timeout} 秒）：{' '.join(args)}")


def shell(command, timeout=DEFAULT_TIMEOUT, retries=2):
    """
    执行 adb shell 命令，返回文本结果。

    如果检测到手机掉线（adb 服务卡死），自动重启服务并重试一次。
    """
    for attempt in range(1, retries + 1):
        result = _run(["shell", command], timeout)
        stderr = result.stderr.decode("utf-8", errors="replace")

        # adb 服务卡死时的两种典型报错
        if "no devices" in stderr or "device offline" in stderr:
            if attempt < retries:
                restart_server()
                continue
            raise AdbError(
                f"adb 掉线，命令无法执行：{command}\n"
                "    请检查数据线，或拔插一次后重跑"
            )

        return result.stdout.decode("utf-8", errors="replace").strip()
    return ""


def device_serial():
    """返回已连接手机的序列号；没连上返回 None"""
    output = _run(["devices"]).stdout.decode("utf-8", "replace")
    for line in output.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            return parts[0]
    return None


def require_device():
    """确保手机已连接并授权，否则抛出带排查步骤的错误"""
    serial = device_serial()
    if serial is None:
        raise AdbError(
            "没有检测到已授权的手机。排查：\n"
            "    1. 数据线是否插好（有些线只能充电，不能传数据）\n"
            "    2. 手机屏幕下拉，点 USB 通知，选【允许】\n"
            "    3. 跑一下 lessons/00_check_env.py 看详细状态"
        )
    return serial


def screen_size():
    """返回屏幕分辨率 (宽, 高)，例如 (1260, 2800)"""
    text = shell("wm size")
    # 输出形如：Physical size: 1260x2800
    for line in text.splitlines():
        if "size:" in line:
            width, height = line.split(":")[-1].strip().split("x")
            return int(width), int(height)
    raise AdbError(f"无法解析屏幕分辨率，wm size 输出为：{text!r}")


def _is_valid_png(data):
    """检查字节流是不是完整的 PNG：开头对得上、结尾有 IEND"""
    return data.startswith(PNG_MAGIC) and data.endswith(PNG_END)


def restart_server():
    """
    重启 adb 服务（电脑端的小程序，不是手机）。

    连接卡死时这是最有效的一招：手机明明插着，但 adb 就是
    返回 "no devices/emulators found" 或者半截数据。
    放心，重启它不会影响手机里的任何东西。
    """
    try:
        _run(["kill-server"], timeout=15)
    except AdbError:
        pass
    time.sleep(1.0)
    _run(["start-server"], timeout=30)
    time.sleep(1.5)


def screenshot(path=None, retries=3, timeout=DEFAULT_TIMEOUT):
    """
    截屏保存为 PNG，返回文件路径。

    adb 截图并非 100% 可靠 —— 服务卡死时会返回空数据或截断的数据。
    所以这里带自动重试和服务自愈，这正是自动化脚本该有的健壮性。
    """
    if path is None:
        path = os.path.join(IMAGES, "screen.png")
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    problems = []
    for attempt in range(1, retries + 1):
        # exec-out 直接传二进制，避免 shell 的换行符转换把图片搞坏
        data = _run(["exec-out", "screencap", "-p"], timeout).stdout

        if _is_valid_png(data):
            with open(path, "wb") as fp:
                fp.write(data)
            return path

        problems.append(f"第 {attempt} 次只拿到 {len(data)} 字节的无效数据")

        # 服务卡死是最常见的原因，重启后通常立刻恢复
        if device_serial() is None:
            problems.append("手机已不在线，重启 adb 服务")
            restart_server()

        time.sleep(0.8)

    raise AdbError(
        f"截图连续失败 {retries} 次：\n    " + "\n    ".join(problems) + "\n"
        "    排查顺序：\n"
        "      1. 手机屏幕是否亮着、有没有锁屏\n"
        "      2. 拔插数据线，或换一根（有些线只能充电，不能传数据）\n"
        "      3. 在项目目录执行 tools/platform-tools/adb.exe kill-server 后重跑"
    )


def tap(x, y):
    """点击屏幕坐标 (x, y)，原点在左上角"""
    shell(f"input tap {int(x)} {int(y)}")


def swipe(x1, y1, x2, y2, duration_ms=300):
    """从 (x1,y1) 滑动到 (x2,y2)，duration_ms 是滑动耗时，越大越"慢" """
    shell(f"input swipe {int(x1)} {int(y1)} {int(x2)} {int(y2)} {int(duration_ms)}")


def keyevent(code):
    """发送按键。常用：3=Home 回桌面，4=Back 返回，26=电源键"""
    shell(f"input keyevent {int(code)}")


def open_activity(action):
    """用 intent 打开界面，例如 android.settings.SETTINGS 打开设置"""
    shell(f"am start -a {action}")


def warmup():
    """
    预热输入通道。

    实测发现：首次连接后，部分手机（尤其国产 ROM）会静默丢弃最初的
    input 命令 —— 不报错，但屏幕上什么都不发生。
    先发一条无副作用的按键把通道唤醒，后面就稳定了。
    """
    shell("input keyevent 0")  # KEYCODE_UNKNOWN：合法但不产生任何界面变化


def screens_differ(path_a, path_b, threshold=0.01):
    """
    比较两张截图，返回 (是否明显不同, 差异比例)。

    自动化里"命令没报错"不等于"操作成功了"。
    用这个函数校验结果，别靠猜。
    """
    import numpy as np
    from PIL import Image, ImageChops

    image_a = Image.open(path_a).convert("RGB")
    image_b = Image.open(path_b).convert("RGB")
    if image_a.size != image_b.size:
        return True, 1.0

    diff = np.asarray(ImageChops.difference(image_a, image_b).convert("L"))
    ratio = float((diff > 20).sum()) / diff.size
    return ratio > threshold, ratio


def device_info():
    """返回手机基本信息"""
    return {
        "品牌": shell("getprop ro.product.brand"),
        "型号": shell("getprop ro.product.model"),
        "安卓": shell("getprop ro.build.version.release"),
    }
