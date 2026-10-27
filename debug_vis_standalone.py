# debug_vis_standalone.py
import sys
import os

# 添加本地 mmseg 代码路径
sys.path.insert(0, 'd:\\作业\\分割\\code')

print("1. 导入模块...")
try:
    import mmcv
    import torch
    from mmseg.apis import init_segmentor, inference_segmentor
    print("   ✓ 模块导入成功")
except Exception as e:
    print(f"   ✗ 模块导入失败: {e}")
    sys.exit(1)

print("2. 检查配置文件...")
config = 'd:\\train_config.py'
if os.path.exists(config):
    print(f"   ✓ 配置文件存在: {config}")
else:
    print(f"   ✗ 配置文件不存在: {config}")
    sys.exit(1)

print("3. 检查测试图像...")
img_path = 'D:\\作业\\分割\\code\\Potsdam_Vaihingen\\test\\images\\top_mosaic_09cm_area1.png'
if os.path.exists(img_path):
    print(f"   ✓ 测试图像存在: {img_path}")
else:
    print(f"   ✗ 测试图像不存在: {img_path}")
    sys.exit(1)

print("4. 加载模型...")
try:
    model = init_segmentor(config, None, device='cpu')
    print("   ✓ 模型加载成功")
except Exception as e:
    print(f"   ✗ 模型加载失败: {e}")
    sys.exit(1)

print("5. 推理...")
try:
    result = inference_segmentor(model, img_path)
    print(f"   ✓ 推理成功，结果类型: {type(result)}")
    print(f"   ✓ 结果长度: {len(result)}")
    if result:
        print(f"   ✓ 分割图形状: {result[0].shape}")
except Exception as e:
    print(f"   ✗ 推理失败: {e}")
    sys.exit(1)

print("6. 保存结果...")
out_dir = './vis_results'
try:
    os.makedirs(out_dir, exist_ok=True)
    print(f"   ✓ 目录创建成功: {out_dir}")
except Exception as e:
    print(f"   ✗ 目录创建失败: {e}")
    sys.exit(1)

print("7. 可视化...")
try:
    img = mmcv.imread(img_path)
    seg_map = result[0]
    print(f"   ✓ 图像加载成功，形状: {img.shape}")
    print(f"   ✓ 分割图形状: {seg_map.shape}")
except Exception as e:
    print(f"   ✗ 可视化失败: {e}")
    sys.exit(1)

print("测试完成！")