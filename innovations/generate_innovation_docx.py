import os
import zipfile
from xml.sax.saxutils import escape

OUTPUT = r"D:\temp_zq\45_huatu\code\code\innovations\UKAN_创新点方案介绍.docx"

content = [
    ("title", "UKAN创新点方案介绍"),
    ("p", "本文档基于 innovations 文件夹中的 edge_aware_ukan 模块整理，旨在对提出的创新点进行结构化说明，便于论文撰写、实验汇报与方案沟通。"),

    ("h1", "1. 创新背景"),
    ("p", "UKAN 作为结合卷积编码器与 Tok-KAN 的分割框架，在遥感语义分割任务中具备较强的语义建模能力。但在解码阶段，原始 UKAN 对跳跃连接采用的是直接相加的融合方式，即将来自浅层编码器的细节特征与来自深层解码器的语义特征进行等权叠加。"),
    ("p", "这种直接相加方式实现简单、计算开销低，但在高分辨率遥感场景中容易出现边界过平滑、细长结构缺失、小目标粘连和建筑轮廓模糊等问题。尤其对于道路边缘、建筑物外轮廓、树木与低植被交界区域，浅层细节与深层语义的贡献并不应被等价处理，因此有必要设计一种更加自适应的跳跃连接融合方式。"),

    ("h1", "2. 创新点名称"),
    ("p", "本创新方案命名为：Edge-Aware Adaptive Skip Fusion（EASF）。在具体实现中，基于该模块构建了改进版解码头 UKAN_EAG（Edge-Aware Gated UKAN）。"),

    ("h1", "3. 核心思想"),
    ("p", "EASF 的核心思想不是单纯再增加一个卷积层或注意力层，而是重新定义解码阶段 skip connection 的融合原则。原始 UKAN 默认浅层特征与深层特征可以通过直接相加完成信息互补，这种设计在多数常规场景下是有效的，但它隐含了一个前提：不同来源的特征在空间位置和语义重要性上具有相同权重。对于遥感语义分割而言，这个前提往往并不成立。"),
    ("p", "遥感图像中的地物边界通常具有高度复杂性：建筑边缘清晰但易受阴影影响，道路狭长且容易被树木遮挡，低植被与树木之间存在大量局部相似纹理，小目标如车辆在高分辨率场景下又要求保留精细轮廓。在这种情况下，如果仍采用“decoder 特征 + skip 特征”的固定融合方式，深层语义与浅层纹理就会被等权叠加，导致边界区域出现过平滑、结构轮廓被稀释、细粒度目标特征被淹没等问题。"),
    ("p", "因此，EASF 提出的根本出发点是：跳跃连接不应是静态融合，而应是边界感知驱动下的动态融合。也就是说，模型需要先判断浅层特征中的哪些区域是具有判别价值的边缘与结构信息，再结合当前 decoder 语义状态，决定应该保留多少高层语义、注入多少浅层细节，而不是简单地让两者直接相加。"),
    ("p", "围绕这一思路，EASF 将 skip 融合分解为三步：首先，从浅层 skip feature 中显式提取高频边界响应，建立局部结构先验；其次，用边界先验去增强浅层特征，使其在轮廓、纹理过渡和小目标位置上具有更高表达强度；最后，再根据 decoder 特征、增强后 skip 特征以及两者之间的差异，生成一个逐像素、逐通道的门控图，实现自适应融合。"),
    ("p", "从本质上讲，EASF 让 skip fusion 从“固定加法”变成了“结构感知的条件组合”。它不再假设每一层、每个像素、每个通道都应采用相同融合策略，而是让模型根据局部上下文动态判断：当前区域究竟更需要深层语义主导，还是更需要浅层边界细节补充。"),
    ("p", "这种思想尤其适合高分辨率遥感场景，因为遥感分割中的难点往往不是“有没有语义”，而是“语义边界是否足够精确”“小结构是否足够完整”“相邻类别之间是否能被清晰分开”。EASF 正是针对这些问题，在 UKAN 原始解码框架上给出的一种针对性增强。"),

    ("h1", "4. 模块设计逻辑"),
    ("h2", "4.1 总体设计逻辑"),
    ("p", "EASF 的设计逻辑可以概括为：边界先验提取 → 浅层结构增强 → 条件门控融合。这个顺序并不是任意堆叠出来的，而是围绕“先识别细节、再增强细节、最后控制细节如何进入解码语义”这一思路组织的。换言之，模块并不是把边界信息和门控机制简单并列使用，而是先通过边界分支把 skip feature 的局部判别性显式化，再把这种显式化后的特征作为门控判断的重要依据。"),
    ("h2", "4.2 边界响应提取"),
    ("p", "在代码实现中，首先对 skip feature 做局部平均池化，并将原特征与池化结果做差，得到高频残差 edge_seed。这个操作的目的在于用一种极轻量方式提取局部高频分量。平均池化代表局部低频背景，原特征减去平滑结果后，保留下来的就是更接近边缘、纹理突变和细粒度轮廓的信息。相比额外引入复杂边缘监督或显式 Sobel/Laplacian 分支，这种方式实现简单、参数量小，而且能够直接嵌入现有特征流。"),
    ("p", "随后，edge_seed 会进入一个轻量卷积模块 edge_conv。该模块由深度卷积、逐点卷积、归一化与 Sigmoid 组成，其目标不是重新生成完整特征，而是预测一个边界响应图 edge_map。这个 edge_map 可以理解为一个结构敏感性权重图：响应越强，说明该区域越可能包含值得保留的轮廓或细节。对应实现位置：edge_aware_ukan.py 中 EdgeAwareGate.forward() 的 pooled、edge_seed 与 edge_map 部分。"),

    ("h2", "4.3 浅层细节增强"),
    ("p", "得到 edge_map 后，模块并不直接把它拿去和 decoder feature 做乘法，而是先用于增强 skip feature：skip_enhanced = skip_feat + skip_feat * edge_map。这里的设计逻辑在于：浅层特征本身已经包含大量空间细节，但其中并不是所有信息都对分割边界有利。通过 edge_map 的逐位置重标定，模块能够突出那些更接近真实边界和结构变化的局部区域，使浅层特征在融合前就具备更强的结构辨识能力。"),
    ("p", "这种增强方式有两个好处。第一，它保持了 skip feature 的主体信息不被破坏，因为增强是残差式的，而不是替换式的；第二，它让增强过程保持稳定，避免因为边界估计不准确而完全覆盖原始浅层信息。也就是说，EASF 不是把 skip 特征强行变成边缘图，而是以边缘为引导对原始浅层细节做选择性强化。"),

    ("h2", "4.4 自适应门控融合"),
    ("p", "在完成 skip 特征增强之后，EASF 才进入真正的融合决策阶段。这里的核心不是简单用 edge_map 当权重，而是构建一个更完整的融合上下文 fusion_context。具体做法是将 decoder feature、增强后的 skip feature，以及两者的绝对差异 |dec_feat - skip_enhanced| 在通道维上拼接。"),
    ("p", "这一步的设计逻辑非常关键。decoder feature 代表当前层的高层语义理解，skip_enhanced 代表浅层结构细节，而二者差异项则代表“当前语义表达与局部细节之间是否存在不一致”。如果没有这个差异项，门控网络只能看到两个输入的静态状态；加入差异项后，门控网络能更好地感知“哪里需要补细节、哪里应该保语义、哪里存在结构与语义冲突”。"),
    ("p", "随后，fusion_context 输入到轻量 gate 网络中，生成逐像素、逐通道门控图 gate。输出形式为：out = dec_feat * (1 - gate) + skip_enhanced * gate。这个公式的意义在于：当 gate 较大时，说明该位置更依赖浅层增强细节；当 gate 较小时，说明该位置更适合保留深层语义。这样就实现了从固定加法到条件融合的转变。"),
    ("p", "从模型行为角度看，门控机制使得不同地物类型可以自动学习到不同的融合偏好。例如，建筑边缘、道路边界、车辆轮廓等区域可能更依赖 skip_enhanced；而大面积同质区域、语义稳定区域则可能更依赖 decoder feature。这样一来，模型能够以更细粒度的方式协调“语义一致性”和“边界锐利性”之间的关系。"),

    ("h2", "4.5 在 UKAN 解码阶段中的插入方式"),
    ("p", "在 UKAN_EAG 中，EASF 被插入到四个层级的 skip fusion 位置，分别由 skip_fuse4、skip_fuse3、skip_fuse2、skip_fuse1 实现。原始 UKAN 在这些位置上采用的是 out + t4、out + t3、out + t2、out + t1 的固定相加形式，而 UKAN_EAG 则统一替换为 self.skip_fuseX(out, tX)。这意味着模块设计并不改变 UKAN 的整体编码器—Tok-KAN—解码器主干流程，而是只在关键的浅深特征交互位置进行增强。"),
    ("p", "这种插入方式具有较强工程优势：它不改变主干特征流尺寸，不引入额外复杂监督，也不需要重写整个 UKAN 框架，因此可作为一个低耦合、可插拔的 skip fusion 改进模块使用。这也使得它非常适合作为结构创新点进行公平对比与消融验证。"),

    ("h1", "5. 相比原始 UKAN 的改进点"),
    ("p", "与原始 UKAN 相比，EASF 的改进不仅仅体现在“把相加改成门控”这一表面形式上，更重要的是它重新定义了跳跃连接在遥感场景中的作用方式。以下从几个角度详细说明这种改进。"),
    ("h2", "5.1 从固定融合到动态融合"),
    ("p", "原始 UKAN 的 skip fusion 本质上是静态的：不同层、不同位置、不同类别区域全部采用同一种融合规则，即直接相加。这种规则的优点是简单，但缺点是缺乏自适应性。EASF 则通过门控图让每个空间位置、每个通道都能根据局部上下文决定融合比例，从而实现真正意义上的动态融合。"),
    ("h2", "5.2 从隐式细节利用到显式边界建模"),
    ("p", "原始 UKAN 虽然通过 skip connection 引入了浅层特征，但这些特征中的边界信息只是被隐式使用，并没有显式建模其重要性。EASF 通过 edge_seed 和 edge_map 把边界响应显式提取出来，再据此增强 skip feature，使模型在融合前就能区分“哪些细节值得保留”。这一步对于边界恢复尤为关键。"),
    ("h2", "5.3 从浅层细节注入到浅深差异协同决策"),
    ("p", "原始 UKAN 中，浅层特征只是被直接加回解码器，相当于一种简单注入；而 EASF 在决策时同时考虑 decoder 特征、增强后的 skip 特征以及二者差异，使得融合不是单向的“补细节”，而是基于浅深信息冲突与互补关系的协同判断。这种设计更符合遥感语义分割中复杂地物结构的真实需求。"),
    ("h2", "5.4 对遥感目标的适配性更强"),
    ("p", "遥感图像中的典型难点包括建筑轮廓、道路边缘、小目标车辆、树木与低植被交界、硬化地表边缘等。原始 UKAN 更偏向语义建模与整体分割，而 EASF 则进一步补足了结构恢复能力。换句话说，原始 UKAN 擅长“分出是什么”，而 EASF 更关注“边界分得是否精确、局部结构是否完整”。这种增强在高分辨率遥感场景中往往更容易转化为实际性能提升。"),
    ("h2", "5.5 工程实现更利于公平对比"),
    ("p", "EASF 没有直接改写原始 UKAN 文件，而是通过注册新模块 UKAN_EAG 的方式实现。这种做法的价值在于：一方面保留了原始 UKAN 的可复现性，另一方面也使得创新点可以作为独立变量进行消融实验。相比直接在原模型内部大幅重构，这种低耦合扩展方式更适合论文实验设计与工程维护。"),
    ("h2", "5.6 预期性能收益更具针对性"),
    ("p", "从预期结果看，EASF 相比原始 UKAN 的提升不会只体现在整体 mIoU 上，更可能表现为边界质量提升、小目标恢复更稳、粘连现象减轻、轮廓更清晰等更细粒度层面。因此它不仅是一种数值优化手段，也是一种更贴近遥感任务痛点的结构改进。"),

    ("h1", "6. 代码实现说明"),
    ("h2", "6.1 核心模块"),
    ("p", "核心实现位于 innovations/edge_aware_ukan/edge_aware_ukan.py。文件中包含两个主要部分："),
    ("p", "（1）EdgeAwareGate：实现边界感知与自适应门控融合；"),
    ("p", "（2）UKAN_EAG：继承自原始 UKAN，并将解码阶段的 skip fusion 替换为四个 EdgeAwareGate 模块。"),

    ("h2", "6.2 解码阶段替换逻辑"),
    ("p", "UKAN_EAG 在 decoder 中分别定义了 skip_fuse4、skip_fuse3、skip_fuse2、skip_fuse1，对应不同层级的跳跃连接融合。原来使用 out + t4、out + t3、out + t2、out + t1 的位置，替换为 self.skip_fuseX(out, tX)，从而实现对四级跳跃连接的统一增强。"),

    ("h2", "6.3 与原版 UKAN 的兼容性"),
    ("p", "该创新实现没有直接改动 mmseg/models/decode_heads/ukan.py 中的原始 UKAN，而是通过自定义模块注册方式新增 UKAN_EAG，并在配置文件中通过 custom_imports 导入。这种做法便于维护，也方便进行消融实验和公平对比。"),

    ("h1", "7. 配置文件说明"),
    ("p", "在 innovations/edge_aware_ukan/configs/ukan_eag_all.py 中，decode_head 被设置为 UKAN_EAG。配置中给出了一个可直接运行的示例："),
    ("p", "type='UKAN_EAG'，edge_reduction=4，num_classes=6，samples_per_gpu=1，crop_size=(256,256)。"),
    ("p", "该配置默认关闭了 da 与 tr 分支（即 tr=False, da=False），更适合作为对 EASF 模块本身的纯净验证基线；后续也可以根据实验需求进一步与改进1、改进2组合。"),

    ("h1", "8. 适用场景与预期收益"),
    ("p", "EASF 特别适用于高分辨率遥感语义分割任务，尤其在以下场景下预期更具优势："),
    ("p", "（1）建筑物边界清晰恢复；"),
    ("p", "（2）道路、细长结构和窄目标的连续性保持；"),
    ("p", "（3）小目标与邻近目标的分离；"),
    ("p", "（4）树木、低植被、硬化地表等类别之间边界更准确。"),
    ("p", "预期收益包括：边界更锐利、局部细节更完整、小目标更稳健，以及在 Potsdam / Vaihingen 等典型遥感数据集上的 mIoU 与边界质量提升。"),

    ("h1", "9. 与现有改进路线的关系"),
    ("p", "当前 innovations 文件夹中的方案主要聚焦于解码阶段跳跃连接融合的增强，与此前 UKAN 的双路编码器改进（Conv + MaxViT）以及底部 BRA/BiFormer 增强属于不同维度的优化。换言之，EASF 可以被理解为一种面向解码与细节恢复的补充性创新点：前两类改进偏向编码特征表达与全局语义建模，而 EASF 则偏向边界感知和局部结构恢复。"),

    ("h1", "10. 实验建议"),
    ("p", "建议围绕以下对比实验展开："),
    ("p", "（1）UKAN baseline；"),
    ("p", "（2）UKAN + EASF；"),
    ("p", "（3）双路编码器 UKAN + EASF；"),
    ("p", "（4）BRA/BiFormer 增强 UKAN + EASF；"),
    ("p", "（5）双路编码器 + BRA/BiFormer + EASF 的完整组合。"),
    ("p", "评价指标可采用 mIoU、mDice、mFscore，并结合定性可视化进一步对边界质量、建筑轮廓和小目标恢复效果进行分析。"),

    ("h1", "11. 总结"),
    ("p", "本文档整理的创新点 EASF（Edge-Aware Adaptive Skip Fusion）本质上是针对原始 UKAN 解码阶段“直接相加式跳跃连接”的针对性改进。它通过边界响应提取、浅层特征增强和门控融合机制，使模型在保持整体框架稳定的同时，提升了对边界与局部结构的表达能力。该方法实现简单、插拔性强、实验可控，适合作为遥感语义分割场景下具有论文价值的结构创新点。"),
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
  <dc:title>UKAN创新点方案介绍</dc:title>
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
    body.append(paragraph_xml(text, style if style in {'title','h1','h2'} else None))

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

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with zipfile.ZipFile(OUTPUT, 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.writestr('[Content_Types].xml', CONTENT_TYPES)
    zf.writestr('_rels/.rels', RELS)
    zf.writestr('docProps/core.xml', CORE)
    zf.writestr('docProps/app.xml', APP)
    zf.writestr('word/_rels/document.xml.rels', DOC_RELS)
    zf.writestr('word/document.xml', DOCUMENT)

print(OUTPUT)
