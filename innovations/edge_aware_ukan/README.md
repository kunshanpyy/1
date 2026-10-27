# Edge-Aware Adaptive Skip Fusion for UKAN

## 创新点
当前 `UKAN` 在解码阶段对跳跃连接采用的是**直接相加**：
- `out + t4`
- `out + t3`
- `out + t2`
- `out + t1`

这种设计简单有效，但对于遥感语义分割里常见的**细长边界、建筑轮廓、道路边缘、小目标粘连**等问题，直接相加会把浅层细节和深层语义等权混合，容易导致边界过平滑。

这里新增了一个改进版：**UKAN_EAG (Edge-Aware Gated UKAN)**。

核心思想：
1. 从 skip feature 中提取一个轻量边界响应；
2. 用边界响应增强浅层细节；
3. 用 decoder 特征、增强后的 skip 特征以及两者差异，预测一个逐像素门控图；
4. 用自适应门控替代原来的直接相加。

## 方法名称
**Edge-Aware Adaptive Skip Fusion (EASF)**

## 文件说明
- `edge_aware_ukan.py`: 改进版 decode head 实现
- `configs/ukan_eag_all.py`: 可直接训练的配置文件示例

## 预期收益
- 更清晰的边界恢复
- 更稳健的小目标分割
- 在 Potsdam / Vaihingen 这类高分辨率遥感场景下更适合建筑、道路等结构化目标

## 运行方式
请在项目根目录下进入 `code` 目录后运行：

### 训练
```bash
python tools/train.py innovations/edge_aware_ukan/configs/ukan_eag_all.py
```

### 测试
```bash
# 切换到项目目录
cd D:\作业\分割\code

# 克隆完整的MMSegmentation
git clone https://github.com/open-mmlab/mmsegmentation.git mmsegmentation_full

# 使用其中的配置文件
# 然后修改你的代码指向正确的路径
```

## 备注
这个创新实现**没有改动你现有的 UKAN 源文件**，而是以新模块方式注册，通过 `custom_imports` 加载，便于你和原版做公平对比实验。
