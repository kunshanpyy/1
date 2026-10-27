# simple_enhanced_visualization.py
import os
import numpy as np
from PIL import Image

# 配置参数
pred_path = 'D:\\作业\\分割\\code\\Potsdam_Vaihingen\\pred\\ukan_all\\top_mosaic_09cm_area1.png'
img_path = 'D:\\作业\\分割\\code\\Potsdam_Vaihingen\\test\\images\\top_mosaic_09cm_area1.png'
out_dir = './vis_results'

# 确保输出目录存在
os.makedirs(out_dir, exist_ok=True)

# 检查文件是否存在
if not os.path.exists(pred_path):
    print(f"错误：预测文件不存在: {pred_path}")
    exit(1)

if not os.path.exists(img_path):
    print(f"错误：原始图像不存在: {img_path}")
    exit(1)

print("加载预测结果...")
pred_img = Image.open(pred_path)
pred_array = np.array(pred_img)
print(f"预测结果尺寸: {pred_array.shape}")
print(f"预测结果数据类型: {pred_array.dtype}")

print("加载原始图像...")
img = Image.open(img_path)
img_np = np.array(img)
print(f"原始图像尺寸: {img_np.shape}")

# 直接保存预测结果的副本
print("保存预测结果副本...")
pred_copy_path = os.path.join(out_dir, 'pred_copy.png')
pred_img.save(pred_copy_path)
print(f"预测结果副本已保存到: {pred_copy_path}")

# 创建叠加效果
print("创建叠加效果...")
if img_np.shape[:2] == pred_array.shape[:2]:
    # 调整透明度
    alpha = 0.3
    overlay = img_np * (1 - alpha) + pred_array * alpha
    overlay = overlay.astype(np.uint8)
    
    overlay_path = os.path.join(out_dir, 'enhanced_overlay.png')
    Image.fromarray(overlay).save(overlay_path)
    print(f"叠加结果已保存到: {overlay_path}")
else:
    print("警告：图像尺寸不匹配，跳过叠加效果")

print("处理完成！")