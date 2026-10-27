import os
import zipfile
from xml.sax.saxutils import escape

OUTPUT = r"D:\temp_zq\45_huatu\code\code\innovations\UKAN_改进创新3_LightRefine_详细方案介绍.docx"

content = [
    ("title", "UKAN 改进创新3：LightRefine 详细方案介绍"),
    ("p", "本文档围绕当前 innovations 目录中已经实现并完成多轮实验筛选的第三创新点进行系统整理。该创新点最终保留为 LightRefine 方案，即在保留前两个主创新（双路编码器与 BRA/Tok-KAN bottleneck）的基础上，增加一个轻量级的通道—空间联合重标定模块，对解码末端特征进行进一步增强。本文档重点说明其提出背景、核心思想、模块设计逻辑、实现方式、实验筛选过程、与其他候选方案的区别及当前实验结论。"),

    ("h1", "1. 创新提出背景"),
    ("p", "当前 UKAN 主模型已经保留了两项核心改进：第一，前端采用双路编码器结构，将原始 UKAN 的卷积分支与 MaxViT 分支结合，通过融合模块综合局部纹理和变体 Transformer 特征；第二，在网络底部采用 BRA / Tok-KAN bottleneck，以增强对全局语义与长程依赖的建模能力。这两项改进共同构成了当前主模型的主体性能来源。"),
    ("p", "在此基础上，为了进一步提出第三创新点，目标不再是重构整个主干，而是寻找一种低耦合、易插拔、尽量不破坏前两个主创新有效性的补充模块。前期探索中曾尝试过边界增强型 skip 重构、边界辅助强化以及多尺度回流式融合等多个方向，但实验结果表明，改动过大时往往会打乱原有强基线的特征分布，导致总体指标回退。因此，第三创新点的设计原则逐渐收敛为：在不改动主路径语义流的前提下，仅对最终解码特征做轻量重标定。"),
    ("p", "基于这一思路，最终保留下来的创新方案是 LightRefine。它更加侧重于在解码末端进行低成本特征校准，而不是直接替换 skip fusion 或重写多尺度主融合逻辑。这样的定位，使其既有机会带来局部增益，又尽可能避免与前两个主创新产生过强耦合冲突。"),

    ("h1", "2. 创新点名称与定位"),
    ("p", "本创新点可命名为：LightRefine（Lightweight Channel-Spatial Refinement）。从论文表达上，也可将其写作：Lightweight Decoder Feature Recalibration Module，强调其本质是对末端解码特征进行轻量重标定。"),
    ("p", "该创新点在整个模型中的定位不是新的主干网络，也不是新的瓶颈替代结构，而是一个部署在解码末端的补充增强模块。它服务于前两个主创新，目标是进一步提升边界、纹理细节以及类别间响应的区分能力，尤其希望对 Building、Impervious Surface、Tree、Car 这些遥感语义分割中的关键类别带来稳定收益。"),

    ("h1", "3. 核心思想"),
    ("p", "LightRefine 的核心思想可以概括为一句话：在保留强主模型输出结构不变的前提下，对最终 decoder feature 进行通道—空间联合重标定，从而让模型在输出前重新评估“哪些通道更重要、哪些位置更关键”。"),
    ("p", "与方案1那种显式从浅层特征中提取边界响应并直接注入最终特征不同，LightRefine 认为，当双路编码器和 BRA bottleneck 已经把主干表征做强之后，第三创新点更适合做“细调”而不是“重构”。因此，它不去大幅重写主路径，而是把最终解码特征视为一个待校准的高维表示，然后分别从通道维与空间维上进行再加权。"),
    ("p", "从通道维来看，不同通道往往对应不同语义子空间，有的更偏向建筑边缘，有的更偏向植被纹理，有的更偏向车辆小目标响应。若所有通道等权输出，模型可能会把一些冗余或噪声通道保留得过强。LightRefine 通过全局平均池化提取每个通道的统计响应，再经过轻量两层 1×1 卷积生成通道门控系数，强化重要通道，抑制次要通道。"),
    ("p", "从空间维来看，不同位置的重要性也不同。遥感图像中，真正决定分类边界的往往是局部结构过渡区域，而不是大面积平坦区域。LightRefine 将经过通道重标定后的特征再进一步压缩成 avg_map 与 max_map，然后通过一个 7×7 的 spatial gate 生成位置权重图，对关键区域进行空间强化。这样一来，模块不是简单地增加一个卷积层，而是在输出前对“语义通道选择”和“空间位置关注”同时建模。"),
    ("p", "最终，LightRefine 采用残差式输出：refined = x_ch * sp + x。残差式设计的优点在于，不会彻底改变原主模型输出分布，而是在其基础上做温和增强，降低训练不稳定和性能突降的风险。也正因为这一点，LightRefine 更适合叠加到已经很强的“改进1 + 改进2”主模型之上。"),

    ("h1", "4. 模块设计逻辑"),
    ("h2", "4.1 设计原则"),
    ("p", "LightRefine 的设计逻辑遵循三个原则：第一，低耦合，不重写主干的前向主路径；第二，轻量化，不能显著增加计算和显存负担；第三，稳定性优先，采用残差和门控方式，避免像重融合结构那样打破已有特征分布。"),
    ("h2", "4.2 通道重标定分支"),
    ("p", "模块首先对输入特征 x 做自适应平均池化，得到全局通道统计信息。之后通过 1×1 卷积降维、ReLU 激活、再 1×1 卷积升维，最后经过 Sigmoid 得到通道门控向量 ch。其作用是从全局语义角度决定哪些通道值得保留更强响应。"),
    ("p", "在代码中，这部分对应 `_ChannelSpatialRefine` 中的 `avg_pool` 与 `channel_gate`。这里的 reduction 超参数控制中间隐藏通道数，reduction 越小，重标定能力越强，但也会增加参数量。当前主方案中，原版方案2采用 `refine_reduction=4`，优化尝试版中也探索过 `refine_reduction=2`。"),
    ("h2", "4.3 空间重标定分支"),
    ("p", "通道重标定后的特征记为 x_ch。接着，模块分别对 x_ch 做通道平均和通道最大池化，形成 `avg_map` 与 `max_map`，再将二者拼接后输入一个 7×7 卷积生成空间门控图 sp。相比 1×1 的纯位置缩放，7×7 卷积具备更大的局部感受野，更适合捕获建筑边缘、道路连续性和小目标邻域上下文。"),
    ("p", "这一设计说明 LightRefine 并不满足于只判断“哪个通道重要”，还进一步判断“哪些位置重要”。对于遥感语义分割任务而言，这两种重标定是互补的：通道重标定更偏语义选择，空间重标定更偏结构定位。"),
    ("h2", "4.4 残差式输出"),
    ("p", "最终输出采用 `x_ch * sp + x` 的残差形式。这种写法的意义在于：如果重标定学习得好，模块会在关键通道和关键位置上加强原表示；如果训练早期门控还不稳定，残差路径也能保留原始输出，避免模型因为第三创新点而整体退化。这个设计是 LightRefine 能够在前两个强创新基础上保持较好稳定性的关键。"),
    ("h2", "4.5 在主模型中的插入位置"),
    ("p", "在代码实现中，LightRefine 并不接入中间层，也不替换 skip fusion。它被放置在 `_UKANVariantBase._forward_backbone()` 之后、`cls_seg` 之前。也就是说，双路编码器、Tok-KAN 编码、BRA 增强、解码器和原始 skip 融合全部完成后，才对最终 decoder feature 做一次轻量重标定，再送入分割头进行预测。"),
    ("p", "这保证了前两个主创新完整保留，而第三创新点只负责“最后一公里”的校准优化。"),

    ("h1", "5. 与其他创新候选方案的关系"),
    ("h2", "5.1 相比方案1：BoundaryAux"),
    ("p", "方案1的思路是从浅层特征中显式提取边界响应，并以边界图调制最终特征。其优点是边界解释性强，但问题在于对最终特征分布扰动较大，而且边界先验是否稳定、是否与主路径强相关，存在较大不确定性。实验结果显示，方案1在总体指标上不如 LightRefine。"),
    ("h2", "5.2 相比方案3：MultiScaleFusion"),
    ("p", "方案3的思路是让中间特征重新回流并与最终特征做多尺度融合。它理论上有一定吸引力，但工程风险更大：一方面，多尺度特征拼接后通道数和显存占用明显增加；另一方面，它对已有 da+tr 强主模型的特征分布干扰更强，前期实验中还出现了显存/非法访存类问题。因此，方案3并未成为最终保留候选。"),
    ("h2", "5.3 为什么最终保留方案2"),
    ("p", "LightRefine 之所以最终胜出，关键在于它在保持低耦合、低风险的同时，提供了稳定可观的性能增益。它不依赖重写主结构，也不显著增加工程复杂度，且在实验中比方案1和方案3表现更优，因此更适合作为第三创新点写入最终模型。"),

    ("h1", "6. 代码实现说明"),
    ("p", "核心实现位于 `innovations/edge_aware_ukan/variant_heads.py`。其中："),
    ("p", "（1）`_UKANVariantBase`：封装了保留改进1（da=True）与改进2（tr=True）主路径的前向主流程；"),
    ("p", "（2）`_ChannelSpatialRefine`：实现通道重标定 + 空间重标定；"),
    ("p", "（3）`UKAN_LightRefine`：在主路径末端调用 `self.refine(out)`，并输出 `self.cls_seg(out)`。"),
    ("p", "从结构实现上看，LightRefine 是一个标准的低耦合后插式模块，这种实现方式非常适合做论文中的可插拔创新模块。"),

    ("h1", "7. 配置文件与实验版本"),
    ("p", "在当前 innovations 目录中，第三创新点相关配置已经形成一个小型实验族，主要包括："),
    ("p", "（1）`ukan_light_refine_da_tr_vaihingen.py`：方案2主实验配置，也是当前最终保留候选；"),
    ("p", "（2）`ukan_light_refine_transfer_da_tr_vaihingen.py`：把旧主线强训练协议迁移到方案2上的对照版；"),
    ("p", "（3）`ukan_light_refine_da_tr_vaihingen_stratified.py`：采用同 area 分层切分后的实验配置；"),
    ("p", "（4）`ukan_light_refine_da_tr_vaihingen_stratified_quick.py` 与 `..._small.py`：快速验证和小数据子集实验配置。"),
    ("p", "其中最终最重要的主实验配置是 `ukan_light_refine_da_tr_vaihingen.py`，它对应官方 `data/vaihingen`、512×512 patch、保留 da+tr、并启用 LightRefine。"),

    ("h1", "8. 当前实验结果与筛选结论"),
    ("p", "在多轮实验比较中，第三创新点的候选方案经历了如下筛选过程：BoundaryAux、LightRefine、MultiScaleFusion、以及若干 v2 / transfer 变体。实验结果表明，LightRefine 原版始终是最稳定、总体指标最优的方案。其代表性结果已经达到：mIoU 55.67、mDice 69.84、aAcc 76.83，且各类别均未出现训练崩溃或完全塌缩。"),
    ("p", "从 per-class 结果看，LightRefine 对 low_vegetation、building、car 等类别具有较好的稳定性，同时对 clutter/background-like 类别也能维持可用的分割性能。这说明它不是只对单一类别有效，而是在整体类别平衡上更具优势。"),

    ("h1", "9. 适用场景与预期收益"),
    ("p", "LightRefine 特别适合以下场景："),
    ("p", "（1）主模型已经较强，不希望第三创新点大幅破坏现有特征流；"),
    ("p", "（2）需要对解码末端做轻量增强，而不是重写主结构；"),
    ("p", "（3）希望在建筑、植被、道路、小目标等遥感类别之间获得更稳定的通道—空间响应分配。"),
    ("p", "其预期收益主要体现在：提高末端特征利用效率、增强类别响应均衡性、减轻部分区域的误分与漏分，并在不增加过多工程复杂度的前提下为主模型提供增益。"),

    ("h1", "10. 最终定位与论文写作建议"),
    ("p", "从当前实验结论来看，第三创新点最合理的最终定位是：在保留“改进1 + 改进2”主模型的基础上，引入一个轻量级解码末端特征重标定模块，以进一步提升输出特征的判别性与稳定性。"),
    ("p", "论文写作时建议将第三创新点表述为：Lightweight Channel-Spatial Refinement on Top of Dual-Encoder and BRA-Enhanced UKAN。这样可以清楚说明：第三创新点不是替代前两个创新，而是在其基础上的补充增强。"),

    ("h1", "11. 总结"),
    ("p", "综上，改进创新3最终保留下来的核心方案是 LightRefine。它通过一个轻量的通道—空间联合重标定模块，对主模型解码末端特征进行再校准，在不打破原有强结构的前提下提供额外性能增益。相比其他候选方案，LightRefine 具有更低耦合、更高稳定性和更清晰的工程实现路径，因此最适合作为当前 UKAN 三阶段创新体系中的第三创新点。"),
]

CONTENT_TYPES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''

RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''

DOC_RELS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"/>'''

CORE = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>UKAN 改进创新3：LightRefine 详细方案介绍</dc:title>
  <dc:creator>OpenAI Assistant</dc:creator>
  <cp:lastModifiedBy>OpenAI Assistant</cp:lastModifiedBy>
</cp:coreProperties>'''

APP = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties" xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft Office Word</Application>
</Properties>'''


def paragraph_xml(text, style=None):
    txt = escape(text)
    if style == 'title':
        ppr = '<w:pPr><w:pStyle w:val="Title"/></w:pPr>'
    elif style == 'h1':
        ppr = '<w:pPr><w:pStyle w:val="Heading1"/></w:pPr>'
    elif style == 'h2':
        ppr = '<w:pPr><w:pStyle w:val="Heading2"/></w:pPr>'
    else:
        ppr = ''
    return f'<w:p>{ppr}<w:r><w:t xml:space="preserve">{txt}</w:t></w:r></w:p>'

body = []
for style, text in content:
    body.append(paragraph_xml(text, style if style in {'title', 'h1', 'h2'} else None))

DOCUMENT = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:wpc="http://schemas.microsoft.com/office/word/2010/wordprocessingCanvas" xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:wp14="http://schemas.microsoft.com/office/word/2010/wordprocessingDrawing" xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" xmlns:w10="urn:schemas-microsoft-com:office:word" xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" xmlns:wpg="http://schemas.microsoft.com/office/word/2010/wordprocessingGroup" xmlns:wpi="http://schemas.microsoft.com/office/word/2010/wordprocessingInk" xmlns:wne="http://schemas.microsoft.com/office/2006/wordml" xmlns:wps="http://schemas.microsoft.com/office/word/2010/wordprocessingShape" mc:Ignorable="w14 wp14">
  <w:body>
    {''.join(body)}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="708" w:footer="708" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>'''

OUT = r'D:\temp_zq\45_huatu\code\code\innovations\UKAN_改进创新3_LightRefine_详细介绍.docx'
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('[Content_Types].xml', CONTENT_TYPES)
    zf.writestr('_rels/.rels', RELS)
    zf.writestr('docProps/core.xml', CORE)
    zf.writestr('docProps/app.xml', APP)
    zf.writestr('word/_rels/document.xml.rels', DOC_RELS)
    zf.writestr('word/document.xml', DOCUMENT)

print(OUT)
