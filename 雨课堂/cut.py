import os
import cv2
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

big = cv2.imread("images/vedio.jpg")     # 177 x 177，四角带底色
if big is None:
    print("没读到 images/vedio.jpg，检查文件名")
    exit()

small = big[28:148, 28:148]              # 正中间切 120 x 120，只留蓝圆 + 白三角
cv2.imwrite("images/play_btn.png", small)

print("原图", big.shape, "-> 模板", small.shape)
