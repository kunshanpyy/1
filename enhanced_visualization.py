# enhanced_visualization.py
import os
import numpy as np
from PIL import Image

# 配置参数
config = {
    'pred_path': 'D:\\作业\\分割\\code\\Potsdam_Vaihingen\\pred\\ukan_all\\top_mosaic_09cm_area1.png',
    'img_path': 'D:\\作业\\分割\\code\\Potsdam_Vaihingen\\test\\images\\top_mosaic_09cm_area1.png',
    'out_dir': './vis_results',
    'color_map': {
        0: [255, 255, 255],      # 不渗透表面 - 白色
        1: [0, 0, 255],          # 建筑物 - 蓝色
        2: [0, 255, 255],        # 低矮植被 - 浅蓝色
        3: [0, 255, 0],          # 树木 - 绿色
        4: [255, 255, 0],        # 车辆 - 黄色
        5: [255, 0, 0],          # 背景 - 红色
    },
    'overlay_alpha': 0.7,  # 原始图像透明度
    'mask_alpha': 0.3,     # 分割掩码透明度
    'output_prefix': 'enhanced_',
}

# 确保输出目录存在
os.makedirs(config['out_dir'], exist_ok=True)

# 检查文件是否存在
for path_key in ['pred_path', 'img_path']:
    path = config[path_key]
    if not os.path.exists(path):
        print(f"错误：文件不存在: {path}")
        exit(1)

print("加载预测结果...")
pred_img = Image.open(config['pred_path'])
pred_array = np.array(pred_img)
print(f"预测结果尺寸: {pred_array.shape}")

print("加载原始图像...")
img = Image.open(config['img_path'])
img_np = np.array(img)
print(f"原始图像尺寸: {img_np.shape}")

# 处理预测结果
print("处理预测结果...")
height, width = pred_array.shape[:2]

# 创建类别映射
seg_map = np.zeros((height, width), dtype=np.int32)
color_mask = np.zeros((height, width, 3), dtype=np.uint8)

if len(pred_array.shape) == 2:
    # 单通道类别索引
    seg_map = pred_array
    # 应用颜色映射
    for label, color in config['color_map'].items():
        color_mask[seg_map == label] = color
elif len(pred_array.shape) == 3:
    # RGB格式，需要转换为类别索引
    # 反向映射：颜色 -> 类别
    color_to_label = {tuple(color): label for label, color in config['color_map'].items()}
    
    # 遍历每个像素
    for i in range(height):
        for j in range(width):
            pixel_color = tuple(pred_array[i, j])
            # 找到对应的类别
            for color, label in color_to_label.items():
                if pixel_color == color:
                    seg_map[i, j] = label
                    color_mask[i, j] = color
                    break
else:
    print("错误：预测结果格式不正确")
    exit(1)

# 计算类别统计
print("计算类别统计...")
class_counts = {}
for label, color in config['color_map'].items():
    count = np.sum(seg_map == label)
    class_counts[label] = count
    print(f"类别 {label}: {count} 像素")

# 保存彩色分割结果
result_path = os.path.join(config['out_dir'], f"{config['output_prefix']}result.png")
Image.fromarray(color_mask).save(result_path)
print(f"彩色分割结果已保存到: {result_path}")

# 调整原始图像尺寸以匹配预测结果
if img_np.shape[:2] != (height, width):
    print("调整原始图像尺寸...")
    img = img.resize((width, height))
    img_np = np.array(img)

# 创建叠加效果
print("创建叠加效果...")
overlay = img_np * config['overlay_alpha'] + color_mask * config['mask_alpha']
overlay = overlay.astype(np.uint8)
overlay_path = os.path.join(config['out_dir'], f"{config['output_prefix']}overlay.png")
Image.fromarray(overlay).save(overlay_path)
print(f"叠加结果已保存到: {overlay_path}")

# 创建边缘增强效果
print("创建边缘增强效果...")
try:
    from scipy import ndimage
    # 计算边缘
    edges = np.zeros_like(seg_map, dtype=bool)
    for label in config['color_map'].keys():
        label_mask = seg_map == label
        edges |= ndimage.laplace(label_mask.astype(float)) != 0
    
    # 创建边缘图像
    edge_image = np.array(color_mask)
    edge_image[edges] = [255, 255, 255]  # 白色边缘
    
    edge_path = os.path.join(config['out_dir'], f"{config['output_prefix']}edges.png")
    Image.fromarray(edge_image).save(edge_path)
    print(f"边缘增强结果已保存到: {edge_path}")
except ImportError:
    print("scipy 未安装，跳过边缘增强")

# 创建颜色图例
print("创建颜色图例...")
legend_height = 100
legend_width = 600
legend = np.ones((legend_height, legend_width, 3), dtype=np.uint8) * 255

# 绘制颜色图例
class_names = ['不渗透表面', '建筑物', '低矮植被', '树木', '车辆', '背景']
class_colors = [config['color_map'][i] for i in range(6)]

for i, (color, name) in enumerate(zip(class_colors, class_names)):
    start_x = int(i * (legend_width / 6))
    end_x = int((i + 1) * (legend_width / 6))
    legend[:, start_x:end_x] = color

# 保存图例
legend_path = os.path.join(config['out_dir'], f"{config['output_prefix']}legend.png")
Image.fromarray(legend).save(legend_path)
print(f"颜色图例已保存到: {legend_path}")

print("处理完成！")
print(f"所有结果已保存到: {config['out_dir']}")