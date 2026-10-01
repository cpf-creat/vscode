"""
第 01 课：adb 基础 —— 让手机听你的话

目标：用 Python 指挥手机截图、点击、滑动。
跑之前把手机拿在手上，跑的过程中盯着屏幕看，你会看到它自己在动。

运行：python lessons/01_adb_basics.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import adb_kit as adb

# 每一步之间的停顿，留时间让你看手机屏幕
PAUSE = 1.5

# 画面变化超过这个比例，就认为"操作生效了"
CHANGE_THRESHOLD = 0.05


def banner():
    print("=" * 54)
    print("  第 01 课：adb 基础")
    print("=" * 54)


def step(number, title):
    print(f"\n{'-' * 54}")
    print(f"  第 {number} 步：{title}")
    print(f"{'-' * 54}")


def swipe_and_verify(x1, y1, x2, y2, label, retries=2):
    """
    滑动，然后截图对比，确认画面真的变了。
    没变就重试 —— 这是所有自动化脚本都该有的写法。
    """
    for attempt in range(1, retries + 1):
        before = adb.screenshot("images/01_before.png")
        adb.swipe(x1, y1, x2, y2, duration_ms=400)
        time.sleep(1.0)
        after = adb.screenshot("images/01_after.png")

        changed, ratio = adb.screens_differ(before, after, CHANGE_THRESHOLD)
        print(f"  {label} 画面变化 {ratio * 100:5.1f}%  ", end="")
        if changed:
            print("[OK] 生效")
            return True
        print(f"[没变化] 第 {attempt} 次，重试...")

    print()
    print("  [注意] 画面没变，但这【不一定】是命令失败。")
    print("         更常见的原因是：画面本来就没有可变化的空间")
    print("         （比如列表已经滑到最后一条了）。")
    print("         校验只能告诉你「结果没变」，判断原因得靠人看截图。")
    return False


def scroll_to_top(center_x, top_y, bottom_y, times=3):
    """
    把当前列表滑回顶部。

    归位很重要：不归位的话，后面滑动可能因为"已经到底了"
    而毫无变化，让人误以为命令失败。
    """
    for _ in range(times):
        adb.swipe(center_x, top_y, center_x, bottom_y, duration_ms=250)
        time.sleep(0.5)


def main():
    adb.setup_console()

    serial = adb.require_device()
    width, height = adb.screen_size()

    banner()
    print(f"  设备 : {serial}")
    print(f"  屏幕 : {width} x {height} 像素")
    print(f"\n  坐标原点 (0,0) 在【左上角】，右下角是 ({width}, {height})")

    info = adb.device_info()
    print(f"  手机 : {info['品牌']} {info['型号']} / 安卓 {info['安卓']}")

    center_x = width // 2
    top_y = int(height * 0.30)
    bottom_y = int(height * 0.72)

    # ---------- 第 0 步：预热 ----------
    step(0, "预热输入通道")
    print("  首次连接后，手机可能丢弃最初的几条 input 命令。")
    print("  先发一条无副作用的按键把它唤醒。")
    adb.warmup()
    time.sleep(0.5)

    # ---------- 第 1 步：截图 ----------
    step(1, "截图 —— 把手机屏幕存到电脑上")
    path = adb.screenshot("images/01_start.png")
    print(f"  已保存   : {path}")
    print(f"  文件大小 : {os.path.getsize(path) // 1024} KB")
    print("  >>> 用看图软件打开它，就是你手机现在的画面")

    time.sleep(PAUSE)

    # ---------- 第 2 步：回桌面 ----------
    step(2, "按 Home 键回桌面")
    print("  keyevent 3 = HOME 键。看着手机，它跳回桌面了")
    adb.keyevent(3)
    time.sleep(PAUSE)

    # ---------- 第 3 步：打开设置 ----------
    step(3, "打开【设置】—— adb 第一次真正操控手机")
    print("  am start -a android.settings.SETTINGS")
    adb.open_activity("android.settings.SETTINGS")
    time.sleep(2.5)

    adb.screenshot("images/01_settings.png")
    print("  已截图 : images/01_settings.png")
    print("  >>> 手机上应该是【设置】界面")
    time.sleep(PAUSE)

    # ---------- 第 4 步：归位 ----------
    step(4, "先把列表滑回顶部（归位）")
    print("  列表可能停在任意位置。不先归位的话，后面滑动可能")
    print("  因为'已经到底了'而毫无变化，让人误以为命令失败。")
    scroll_to_top(center_x, top_y, bottom_y)
    adb.screenshot("images/01_at_top.png")
    print("  已归位 : images/01_at_top.png")

    # ---------- 第 5 步：滑动并验证 ----------
    step(5, "从顶部向上滑 —— 这次一定有反应")
    print(f"  路线 : ({center_x}, {bottom_y}) → ({center_x}, {top_y})")
    print("  >>> 盯着手机，列表应该自己往上滚")
    swipe_and_verify(center_x, bottom_y, center_x, top_y, "向上滑")

    # ---------- 第 6 步：点击 ----------
    step(6, "点击 —— 点开顶部的搜索框")
    print("  滑动只能证明 adb 能动画面，点击才能证明它真能操控手机。")
    print("  搜索框固定在顶部、不随列表滚动，所以坐标最可靠。")

    tap_x, tap_y = center_x, int(height * 0.145)
    before = adb.screenshot("images/01_before_tap.png")
    print(f"  点击坐标 : ({tap_x}, {tap_y})")
    adb.tap(tap_x, tap_y)
    time.sleep(1.5)
    after = adb.screenshot("images/01_after_tap.png")

    changed, ratio = adb.screens_differ(before, after, CHANGE_THRESHOLD)
    print(f"  画面变化 {ratio * 100:.1f}%  ", end="")
    print("[OK] 点击生效，打开了搜索界面" if changed else "[没变化] 可能点到空白处了")

    # ---------- 第 7 步：收尾 ----------
    step(7, "按两次 Back 退出搜索，再回桌面")
    adb.keyevent(4)   # BACK 关掉搜索/键盘
    time.sleep(0.8)
    adb.keyevent(4)   # BACK 再退一层
    time.sleep(0.8)
    adb.keyevent(3)   # HOME 回桌面
    print("  手机已回到桌面")

    print(f"\n{'=' * 54}")
    print("  第 01 课完成")
    print(f"{'=' * 54}")
    print("  你学会的 adb 操作（都在 adb_kit 里）：")
    print("    screenshot()       截图")
    print("    tap(x, y)          点击坐标")
    print("    swipe(x1,y1,x2,y2) 滑动")
    print("    keyevent(3/4)      按 Home / Back 键")
    print("    open_activity()    打开指定界面")
    print()
    print("  两个更重要的思维习惯：")
    print("    1. 每一步操作后【截图验证】，别假设它成功了")
    print("    2. 校验只说'有没有变化'，不说'为什么'。")
    print("       结果不符合预期时，去【看截图】，别靠猜。")
    print()
    print("  下一课：让 OpenCV 自动在截图里找出按钮坐标，")
    print("         这样就再也不用硬编码 (x, y) 了。")
    print()


if __name__ == "__main__":
    try:
        main()
    except adb.AdbError as exc:
        print(f"\n[出错了] {exc}\n")
        sys.exit(1)
