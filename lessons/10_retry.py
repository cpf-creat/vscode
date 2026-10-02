import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import kit

# 注意：别用 emoji（比如 ❌ ✅）。Windows 控制台是 GBK 编码，编不出来就直接崩
# UnicodeEncodeError —— 而且会崩在 except 块里，把你的错误处理自己搞死。
print("开始截图…")
try:
    img = kit.shot("images/retry_test.png")
    print(f"成功，尺寸 {img.shape}")
except RuntimeError as e:
    print(f"最终失败：{e}")
    print("   ↑ 这里是【调用者】。决定权在我手上：重试整段？跳过？还是就此停下？")
