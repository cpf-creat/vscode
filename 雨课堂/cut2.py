import os
import cv2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

big = cv2.imread("images/look.png")      # 2800 x 1260，播完那天的截图
if big is None:
    print("没读到 images/look.png")
    exit()

done = big[636:692, 165:300]             # 只切「已完成」三个字，不带左边那个 ○▶ 图标
cv2.imwrite("images/done.png", done)

print("原图", big.shape, "-> 模板", done.shape)
