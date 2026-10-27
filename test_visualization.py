# test_visualization.py
import os
import numpy as np
from PIL import Image

# 保存结果
out_dir = './vis_results'
os.makedirs(out_dir, exist_ok=True)

# 创建一个示例分割结果（6个类别）
height, width = 256, 256
seg_map = np.zeros((height, width), dtype=np.int32)

# 为不同区域分配不同的类别
seg_map[0:85, 0:85] = 0  # 不渗透表面 - 白色
seg_map[0:85, 85:170] = 1  # 建筑物 - 蓝色
seg_map[0:85, 170:256] = 2  # 低矮植被 - 浅蓝色
seg_map[85:170, 0:85] = 3  # 树木 - 绿色
seg_map[85:170, 85:170] = 4  # 车辆 - 黄色
seg_map[85:170, 170:256] = 5  # 背景 - 红色
seg_map[170:256, :] = 0  # 不渗透表面 - 白色

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
color_mask = np.zeros((seg_map.shape[0], seg_map.shape[1], 3), dtype=np.uint8)
for label, color in color_map.items():
    color_mask[seg_map == label] = color

# 保存结果
result_path = os.path.join(out_dir, 'test_result.png')
Image.fromarray(color_mask).save(result_path)
print(f"测试可视化结果已保存到: {result_path}")

# 创建颜色图例
legend_height = 50
legend_width = width
legend = np.ones((legend_height, legend_width, 3), dtype=np.uint8) * 255

# 绘制颜色图例
class_names = ['不渗透表面', '建筑物', '低矮植被', '树木', '车辆', '背景']
class_colors = [color_map[i] for i in range(6)]

for i, (color, name) in enumerate(zip(class_colors, class_names)):
    start_x = int(i * (legend_width / 6))
    end_x = int((i + 1) * (legend_width / 6))
    legend[:, start_x:end_x] = color

# 保存图例
legend_path = os.path.join(out_dir, 'legend.png')
Image.fromarray(legend).save(legend_path)
print(f"颜色图例已保存到: {legend_path}")

print("测试完成！")