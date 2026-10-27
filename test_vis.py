# vis_standalone.py
import sys
import os

print("1. 导入基本模块...")

# 添加本地 mmseg 代码路径（确保优先使用本地代码）
sys.path.insert(0, 'd:\\作业\\分割\\code')

print("2. 导入 mmcv...")
try:
    import mmcv
    print("   ✓ mmcv 导入成功")
except Exception as e:
    print(f"   ✗ mmcv 导入失败: {e}")

try:
    print("3. 导入 torch...")
    import torch
    print(f"   ✓ torch 导入成功，版本: {torch.__version__}")
    print(f"   ✓ CUDA 可用: {torch.cuda.is_available()}")
except Exception as e:
    print(f"   ✗ torch 导入失败: {e}")

try:
    print("4. 导入 mmseg.apis...")
    from mmseg.apis import init_segmentor, inference_segmentor
    print("   ✓ mmseg.apis 导入成功")
except Exception as e:
    print(f"   ✗ mmseg.apis 导入失败: {e}")

print("5. 测试目录创建...")
out_dir = './vis_results'
try:
    os.makedirs(out_dir, exist_ok=True)
    print(f"   ✓ 目录 {out_dir} 创建成功")
except Exception as e:
    print(f"   ✗ 目录创建失败: {e}")

print("测试完成！")