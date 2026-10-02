"""用真截图验证 what_page 判页面对不对 —— 全程不碰手机。

样本固定在 images/page_*.png。为什么要专门复制一份，不直接用 look.png：
look.png 是 text1.py 的【临时截图文件】，下次一跑就被覆盖，拿它当样本迟早会坏。

其中三张是故意放进来、【应该认不出来】的：
  - 播放中的视频页：界面上光秃秃的，模板全都不亮
  - 手机的「设置」页：噪声样本
  - vivo「蓝心小V」页：噪声样本里的【最坏情况】，下面专门有一段讲它
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kit

template_play = kit.load("images/play_btn.png")
template_done = kit.load("images/done.png")
template_tab = kit.load("images/tab_undone.png")

# 顺序就是优先级。播放按钮排最后，是因为它最容易认错 —— 所以它【不跟别人共用 0.8】，
# 单独用一个 PLAY_BTN_SCORE（text1.py 里那个，同值 0.85）。
# 为什么非得单独提一档，看文件末尾的对照实验，那儿是拿数说话。
PLAY_BTN_SCORE = 0.85

MARKERS = [
    ("列表页", template_tab, 0.8),
    ("已播完", template_done, 0.8),
    #空下来因为下面一部分代码的作用是寻找这个最优值
    ("待播放", template_play, PLAY_BTN_SCORE),
]

SAMPLES = [
    ("images/page_list.png",           "列表页"),
    ("images/page_paused.png",         "待播放"),
    ("images/page_finished.png",       "已播完"),
    ("images/page_playing.png",        None),   # 播放中：本来就该认不出
    ("images/page_noise_settings.png", None),   # 手机设置页：噪声
    ("images/page_noise_vivo.png",     None),   # 蓝心小V 页：噪声里最狠的一张
]



#判断检测的准确不准确
fails = 0
for path, expect in SAMPLES:
    #每次循环从sample取一张图片，然后看makers中哪一个图片最符合这个图片
    #相当于拿一张图片和makers里的每一张图片一一比对，每次比对会有一个分数，分数超过阈值的会比对成功
    got, score = kit.what_page(kit.load(path), MARKERS)
    ok = got == expect
    fails += not ok
    print(f"{'OK  ' if ok else 'FAIL'} {os.path.basename(path):<24} 判成 {str(got):<8}"
          f" 最高分 {score:.3f}   期望 {expect}")

print(f"\n{len(SAMPLES) - fails}/{len(SAMPLES)} 判对")



# ---------- 对照实验：这条线到底该画哪儿 ----------
# 光说"0.85 判对了"没有意义 —— 0.8 也判对了，0.9 更判得对。得问：
# 往下能松到哪儿？ 把播放按钮的阈值一档档往下放，看哪一档开始把噪声当成待播放。
print("\n--- 对照：播放按钮阈值往下松，松到哪一档开始出错 ---")

noise_vivo = kit.load("images/page_noise_vivo.png")
noise_set = kit.load("images/page_noise_settings.png")
hit_paused = kit.load("images/page_paused.png")

#寻找makers里的阈值的最优值
for th in (0.85, 0.8, 0.7):
    # 三张图同一个阈值下的表现，一行看全
    #what_page返回名字和位置，未匹配到返回None
    v, _ = kit.what_page(noise_vivo, [("待播放", template_play, th)])
    s, _ = kit.what_page(noise_set,  [("待播放", template_play, th)])
    h, _ = kit.what_page(hit_paused, [("待播放", template_play, th)])
    flag = "  ← 噪声越线了！" if (v or s) else ""
    #这个测试是找一个相似的图片，如果v返回None表示未匹配成功，即相似图片与模板未匹配,此时这个阈值是健康的，如果在某一个阈值下匹配成功了
    #那么这个阈值是不健康的，需要调整
    print(f"  阈值 {th:.2f}   蓝心小V {'误判成待播放' if v else '认不出  '}"
          f"   设置页 {'误判成待播放' if s else '认不出  '}"
          f"   真·暂停页 {'认得出' if h else '认不出'}{flag}")

print("""
读法：真命中最低 0.923（真机抓的），噪声最高 0.814（蓝心小V 页）。
     中间的缝只有 0.109 宽。
     → 0.70、0.80 都会把蓝心小V 页当成"待播放"，然后在上面乱点一通。
     → 0.85 是缝里偏下的位置：离噪声远一点，离真命中近一点。

【注意】别忘了这个缝为什么这么窄：播放按钮是【半透明】叠在视频上的，
  底下画面不一样它就长得不一样。往 0.85 上抠小数点是治标 ——
  真想稳，得换个标志物（比如按颜色找那个蓝色圆环）。
""")
