# debug_imports.py
import sys
import os

print("Python path:")
for path in sys.path:
    print(f"  - {path}")

print("\nCurrent directory:", os.getcwd())

# 测试 1: 基础导入
print("\n1. 测试基础模块...")
try:
    import os
    import sys
    print("   ok: 基础模块导入成功")
except Exception as e:
    print(f"   error: {e}")

# 测试 2: numpy
print("\n2. 测试 numpy...")
try:
    import numpy
    print(f"   ok: numpy 导入成功，版本: {numpy.__version__}")
except Exception as e:
    print(f"   error: {e}")

# 测试 3: PIL
print("\n3. 测试 PIL...")
try:
    from PIL import Image
    print("   ok: PIL 导入成功")
except Exception as e:
    print(f"   error: {e}")

# 测试 4: torch
print("\n4. 测试 torch...")
try:
    import torch
    print(f"   ok: torch 导入成功，版本: {torch.__version__}")
    print(f"   CUDA 可用: {torch.cuda.is_available()}")
except Exception as e:
    print(f"   error: {e}")

# 测试 5: mmcv
print("\n5. 测试 mmcv...")
try:
    import mmcv
    print(f"   ok: mmcv 导入成功，版本: {mmcv.__version__}")
except Exception as e:
    print(f"   error: {e}")

# 测试 6: mmseg.apis
print("\n6. 测试 mmseg.apis...")
try:
    from mmseg.apis import init_segmentor, inference_segmentor
    print("   ok: mmseg.apis 导入成功")
except Exception as e:
    print(f"   error: {e}")

print("\n测试完成！")