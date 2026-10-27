# test_imports.py
print("开始测试导入...")

# 测试 1: 基础导入
print("1. 测试基础模块...")
import os
import sys
print("   ok: 基础模块导入成功")

# 测试 2: mmcv
print("2. 测试 mmcv...")
try:
    import mmcv
    print("   ok: mmcv 导入成功")
except Exception as e:
    print(f"   error: mmcv 导入失败: {e}")

# 测试 3: torch
print("3. 测试 torch...")
try:
    import torch
    print("   ok: torch 导入成功")
except Exception as e:
    print(f"   error: torch 导入失败: {e}")

print("测试完成！")