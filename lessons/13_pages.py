"""量一量：4 个模板在每一张真截图上分别打多少分。

做"页面识别"之前必须先知道这个 —— 页面识别能不能成立，
全看这几个分数在【不同的页面】上分不分得开：
要是列表页和视频页上「未完成」Tab 都打 0.9，那它就区分不了页面，方案得换。

只挑 2MB 以下的截图：早期用 bash 的 > 重定向存的那批（01_start.png 等 4.8MB）
已经被 \\n→\\r\\n 改坏了（README「环境类」那条坑），读出来是 None，混进来没意义。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

TEMPLATES = {
    "未完成Tab": "images/tab_undone.png",
    "视频小标签": "images/chip_video.png",
    "大播放按钮": "images/play_btn.png",
    "已完成字样": "images/done.png",
}
SKIP = {p.replace("/", os.sep) for p in TEMPLATES.values()}

tpls = {name: kit.load(path) for name, path in TEMPLATES.items()}

header = f"{'截图':<20}" + "".join(f"{n:>13}" for n in tpls)
print(header)
print("-" * len(header))

for f in sorted(os.listdir("images")):
    path = os.path.join("images", f)
    if not f.endswith(".png") or path in SKIP or os.path.getsize(path) > 2_000_000:
        continue
    try:
        screen = kit.load(path)
    except FileNotFoundError as e:
        print(f"{f:<20}  跳过：{e}")
        continue
    # 模板比图还大，matchTemplate 直接报 cv2.error（不是 None！）——
    # 说明这个文件压根不是整屏截图，是个局部裁剪，比不了
    if any(screen.shape[0] < t.shape[0] or screen.shape[1] < t.shape[1]
           for t in tpls.values()):
        print(f"{f:<20}  跳过：{screen.shape[1]}x{screen.shape[0]} 比模板还小，是局部裁剪")
        continue
    # 够 0.8 就打个星号，一眼看出哪几个是"真的找到了"而不是"最像的那个"
    scores = [kit.find(t, screen)[0] for t in tpls.values()]
    cells = "".join(f"{s:>12.3f}{'*' if s >= kit.THRESHOLD else ' '}" for s in scores)
    print(f"{f:<20}{cells}")
