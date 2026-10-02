# kit.py 在项目根目录，而 Python 只在"脚本自己所在的文件夹"（lessons/）里找模块。
# 少了这两行，import kit 会报 ModuleNotFoundError —— 这一步就是告诉它根目录在哪儿。
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kit

template = kit.load("images/template.png")
screen = kit.shot("images/step1.png")
score, location = kit.find(template, screen)
print(f"相似度 {score:.3f}，位置 {location}")
