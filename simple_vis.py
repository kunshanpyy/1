# simple_vis.py
import os
import numpy as np
from PIL import Image

# 测试图像路径
img_path = 'D:\\作业\\分割\\code\\Potsdam_Vaihingen\\test\\images\\top_mosaic_09cm_area1.png'

# 保存结果
out_dir = './vis_results'
os.makedirs(out_dir, exist_ok=True)

# 加载图像
print("加载图像...")
img = Image.open(img_path)
width, height = img.size
print(f"图像尺寸: {width}x{height}")

# 创建示例分割结果（模拟6个类别的分割）
print("创建分割结果...")
seg_map = np.zeros((height, width), dtype=np.int32)

# 为不同区域分配不同的类别（模拟分割结果）
seg_map[0:height//2, 0:width//2] = 0  # 不渗透表面 - 白色
seg_map[0:height//2, width//2:] = 1   # 建筑物 - 蓝色
seg_map[height//2:, 0:width//3] = 2   # 低矮植被 - 浅蓝色
seg_map[height//2:, width//3:2*width//3] = 3  # 树木 - 绿色
seg_map[height//2:, 2*width//3:] = 4  # 车辆 - 黄色
# 背景类别 5 可以根据需要添加

# 六个类别的颜色映射
color_map = {
    0: [255, 255, 255],      # 不渗透表面 - 白色
    1: [0, 0, 255],          # 建筑物 - 蓝色
    2: [0, 255, 255],        # 低矮植被 - 浅蓝色
    3: [0, 255, 0],          # 树木 - 绿色
    4: [255, 255, 0],        # 车辆 - 黄色
    5: [255, 0, 0],          # 背景 - 红色
}

# 创建彩色掩码
print("创建彩色掩码...")
color_mask = np.zeros((height, width, 3), dtype=np.uint8)
for label, color in color_map.items():
    color_mask[seg_map == label] = color

# 保存结果
result_path = os.path.join(out_dir, 'result.png')
Image.fromarray(color_mask).save(result_path)
print(f"可视化结果已保存到: {result_path}")

# 保存叠加图像
print("创建叠加图像...")
img_np = np.array(img)
overlay = img_np * 0.7 + color_mask * 0.3
overlay = overlay.astype(np.uint8)
overlay_path = os.path.join(out_dir, 'overlay.png')
Image.fromarray(overlay).save(overlay_path)
print(f"叠加结果已保存到: {overlay_path}")

print("处理完成！")