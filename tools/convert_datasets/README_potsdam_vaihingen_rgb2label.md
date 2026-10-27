# Potsdam/Vaihingen RGB 标签转单通道 label id

这个脚本用于把 Potsdam/Vaihingen 风格的 RGB 彩色标签：

- 白色 `(255,255,255)`
- 蓝色 `(0,0,255)`
- 青色 `(0,255,255)`
- 绿色 `(0,255,0)`
- 黄色 `(255,255,0)`
- 红色 `(255,0,0)`

转换成 mmseg 可直接训练的单通道类别索引图 `0~5`。

## 脚本位置
```bash
tools/convert_datasets/potsdam_vaihingen_rgb2label.py
```

## 用法
在项目根目录 `code/code` 下执行：

```bash
python tools/convert_datasets/potsdam_vaihingen_rgb2label.py ./Potsdam_Vaihingen
```

默认会转换：
- `train/labels -> train/labels_labelid`
- `test/labels -> test/labels_labelid`

## 转完后配置应改为
```python
train=dict(
    img_dir='train/images',
    ann_dir='train/labels_labelid',
    ...),
val=dict(
    img_dir='test/images',
    ann_dir='test/labels_labelid',
    ...),
test=dict(
    img_dir='test/images',
    ann_dir='test/labels_labelid',
    ...),
```

## 说明
如果你的类别语义和当前映射注释略有差别，也没关系；
关键是颜色到类别 id 的映射要与你数据集定义、评估类别顺序保持一致。
