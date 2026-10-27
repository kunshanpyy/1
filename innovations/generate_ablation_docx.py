from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

OUTPUT = r"D:\temp_zq\45_huatu\code\code\innovations\UKAN_消融实验过程与结果整理.docx"


def set_cell_shading(cell, fill):
    tc_pr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:fill'), fill)
    tc_pr.append(shd)


def set_doc_style(doc):
    styles = doc.styles
    styles['Normal'].font.name = 'Times New Roman'
    styles['Normal']._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    styles['Normal'].font.size = Pt(11)

    for style_name in ['Title', 'Heading 1', 'Heading 2', 'Heading 3']:
        style = styles[style_name]
        style.font.name = 'Times New Roman'
        style._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体' if style_name != 'Title' else '黑体')

    styles['Title'].font.size = Pt(18)
    styles['Title'].font.bold = True
    styles['Heading 1'].font.size = Pt(15)
    styles['Heading 1'].font.bold = True
    styles['Heading 2'].font.size = Pt(13)
    styles['Heading 2'].font.bold = True
    styles['Heading 3'].font.size = Pt(12)
    styles['Heading 3'].font.bold = True


def add_paragraph(doc, text, style=None, bold=False, color=None, align=None):
    p = doc.add_paragraph(style=style)
    if align is not None:
        p.alignment = align
    run = p.add_run(text)
    run.bold = bold
    run.font.name = 'Times New Roman'
    run._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
    run.font.size = Pt(11 if style is None else 11)
    if color is not None:
        run.font.color.rgb = RGBColor(*color)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.line_spacing = 1.5
    return p


def add_table(doc, title, headers, rows):
    add_paragraph(doc, title, style='Heading 2')
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    for i, h in enumerate(headers):
        hdr_cells[i].text = str(h)
        set_cell_shading(hdr_cells[i], 'D9EAF7')
        for p in hdr_cells[i].paragraphs:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            for r in p.runs:
                r.bold = True
                r.font.name = 'Times New Roman'
                r._element.rPr.rFonts.set(qn('w:eastAsia'), '黑体')
                r.font.size = Pt(10.5)
    for row in rows:
        cells = table.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = str(val)
            for p in cells[i].paragraphs:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER if i > 0 else WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:
                    r.font.name = 'Times New Roman'
                    r._element.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
                    r.font.size = Pt(10.5)
    doc.add_paragraph('')


def main():
    doc = Document()
    set_doc_style(doc)

    sec = doc.sections[0]
    sec.top_margin = Pt(72)
    sec.bottom_margin = Pt(72)
    sec.left_margin = Pt(72)
    sec.right_margin = Pt(72)

    add_paragraph(doc, 'UKAN 消融实验过程与结果整理', style='Title', align=WD_ALIGN_PARAGRAPH.CENTER)
    add_paragraph(doc, '（润色扩展版，含占位表与第三创新点筛选结论）', align=WD_ALIGN_PARAGRAPH.CENTER, color=(90, 90, 90))

    add_paragraph(doc, '1. 消融实验背景与目标', style='Heading 1')
    add_paragraph(doc, '当前 UKAN 研究路线中，前两个创新点已被确定为主模型必须保留的核心结构：改进1为双路编码器（原始卷积分支 + MaxViT 分支），改进2为 BRA / Tok-KAN bottleneck，用于增强底部全局语义建模能力。在此基础上，进一步设计第三创新点，希望在不破坏主模型主体有效性的前提下继续提升整体分割性能。')
    add_paragraph(doc, '从研究逻辑上看，前两个创新点分别作用于编码阶段与底部语义建模阶段，已经构成了较强的主模型骨架。因此第三创新点不再适合采用重写主干、替换主路径的方式，而更适合选择一种低耦合、可插拔、风险较低的补充增强模块。这样既能维持前两个创新点的有效性，又能通过解码末端精修的方式尝试进一步提升结果。')
    add_paragraph(doc, '因此，本轮消融实验的目标不仅是判断哪个结构最好，还包括回答三个更关键的问题：一是前两个主创新在统一官方 Vaihingen 协议下是否依然有效；二是第三创新点候选中真正能带来增益的是哪一种；三是最终主模型应如何组织，才能兼顾性能、稳定性和论文叙事逻辑。')

    add_paragraph(doc, '2. 数据协议重建过程', style='Heading 1')
    add_paragraph(doc, '实验前期使用的 `Potsdam_Vaihingen` 目录存在明显的数据协议混杂问题：其中同时包含 RGB 标签、P 模式标签、labels_crop、masks 等多种历史处理中间结果，且目录命名本身暗示了对 Potsdam 和 Vaihingen 的混合管理。这会导致旧实验虽然数值偏高，但难以确认其是否来自严格、可复现、可对比的 benchmark 协议。')
    add_paragraph(doc, '为了解决这个问题，后续统一切换到官方原始 Vaihingen 数据，并使用 MMSeg 官方脚本 `tools/convert_datasets/vaihingen.py` 重新构建标准数据集，生成 `data/vaihingen/img_dir/train`、`img_dir/val`、`ann_dir/train`、`ann_dir/val` 等标准目录。与此同时，为避免旧 `MyDatasetLand` 与官方标签编号顺序不一致，又新增了 `VaihingenOfficialDataset`，确保类别语义与官方转换后的 label id 完全对齐。')
    add_paragraph(doc, '这一过程直接解决了前期实验中 `low_vegetation=0`、某些类长期异常等现象，说明数据协议问题确实是影响结果可靠性的关键因素。因此，后续所有可信实验结果都应尽量建立在官方 `data/vaihingen` 基础上。')

    add_paragraph(doc, '3. 消融实验整体设计逻辑', style='Heading 1')
    add_paragraph(doc, '本轮消融实验分为两层：第一层是主模型主线消融，即对 baseline、仅改进1、仅改进2、改进1+改进2以及“改进1+改进2+第三创新点”进行对照；第二层是第三创新点内部消融，即在多个候选模块中筛选真正有效的方案。由于研究目标是保留前两个创新点作为核心主模型，因此第三创新点的设计原则被限定为：低耦合、轻量化、后插式，不重写主干主路径，尽量减少对已有强模型分布的破坏。')

    add_paragraph(doc, '4. 第三创新点候选方案设计', style='Heading 1')
    add_paragraph(doc, '4.1 方案1：BoundaryAux', style='Heading 2')
    add_paragraph(doc, '方案1的思路是从浅层特征中提取轻量边界响应，并将其上采样后用于调制最终 decoder 特征。其优点是边界解释性较强，适合遥感图像中的建筑轮廓、道路边缘和细粒度边界恢复任务，但实验结果表明其整体性能弱于方案2。')
    add_paragraph(doc, '4.2 方案2：LightRefine', style='Heading 2')
    add_paragraph(doc, '方案2最终被证明是当前最优第三创新点候选。它采用通道—空间联合重标定思路，对主模型输出的最终 decoder feature 做轻量校准：先通过全局池化和两层 1×1 卷积生成通道门控，再通过 avg/max pooling 与 7×7 spatial gate 生成空间权重，最终采用残差式形式输出。与方案1相比，它不显式改写边界逻辑，而是通过更稳定的后插式重标定来提升特征表达质量。')
    add_paragraph(doc, '4.3 方案3：MultiScaleFusion', style='Heading 2')
    add_paragraph(doc, '方案3希望通过多尺度特征回流进一步增强最终输出层，但工程上风险更高，显存占用更大，且在多次实验中表现出不稳定甚至非法访存等问题，因此最终未被保留为主候选。')

    add_paragraph(doc, '5. 第三创新点筛选过程与结论', style='Heading 1')
    add_paragraph(doc, '在第三创新点筛选中，实验遵循“先验证可跑，再看是否增益，再比较与主模型协同”的路径进行。结果显示，方案1虽然可以稳定训练，但整体表现不如方案2；方案3则在原始设计下未能提供足够稳定的工程表现；方案2（LightRefine）在多轮训练中始终保持更优且更稳的结果，并随着训练推进继续上升，因此当前已经可以明确将其作为第三创新点主体保留。')

    add_table(
        doc,
        '表1  主线消融实验汇总（官方 Vaihingen，待补全版）',
        ['实验项', 'mIoU', 'mDice', '备注'],
        [
            ['UKAN baseline', '[待补]', '[待补]', '官方 Vaihingen 基线'],
            ['UKAN + 改进1（双路编码器）', '[待补]', '[待补]', 'da=True'],
            ['UKAN + 改进2（BRA/Tok-KAN）', '[待补]', '[待补]', 'tr=True'],
            ['UKAN + 改进1 + 改进2', '[待补]', '[待补]', '主模型强基线'],
            ['UKAN + 改进1 + 改进2 + LightRefine', '55.67', '69.84', '当前第三创新点主候选'],
        ]
    )

    add_table(
        doc,
        '表2  改进创新3内部方案对比',
        ['方案', 'mIoU', 'mDice', '备注'],
        [
            ['方案1：BoundaryAux', '46.01', '60.99', '可跑通，但弱于方案2'],
            ['方案2：LightRefine（12000 iter）', '55.20', '69.51', '中期结果'],
            ['方案2：LightRefine（16000 iter）', '58.62', '72.25', '阶段峰值'],
            ['方案2：LightRefine（20000 iter）', '55.67', '69.84', '最终稳定结果'],
            ['方案2：Transfer版', '50.94', '65.59', '旧强协议迁移后回退'],
            ['方案3：MultiScaleFusion', '[未稳定]', '[未稳定]', '存在工程不稳定问题'],
        ]
    )

    add_table(
        doc,
        '表3  方案3（MultiScaleFusion）最终效果占位表',
        ['方案3设置', 'mIoU', 'mDice', '状态'],
        [
            ['方案3-Base（无 da / 无 tr）', '[待补]', '[待补]', '占位'],
            ['方案3-TR（仅 tr）', '[待补]', '[待补]', '占位'],
            ['方案3-DA（仅 da）', '[待补]', '[待补]', '占位'],
            ['方案3-ALL（da + tr）', '[待补]', '[待补]', '占位'],
        ]
    )

    add_paragraph(doc, '6. 方案2最终实验结果解读', style='Heading 1')
    add_paragraph(doc, '方案2（LightRefine）在 20000 iter 最终结果中达到 mIoU 55.67、mDice 69.84、aAcc 76.83，说明第三创新点已经不是“实验性尝试”，而是一个在官方 Vaihingen 协议下能够稳定工作并带来增益的有效模块。')
    add_paragraph(doc, '从 per-class 指标看，low_vegetation、building、car 等关键类别表现较强，impervious_surface、tree、clutter 也保持了可接受的稳定性。这说明 LightRefine 并非只对某单一类别起作用，而是在整体类别平衡上更具优势。')
    add_paragraph(doc, '需要注意的是，该结果尚未全面追平旧 `Potsdam_Vaihingen` 高结果，但旧结果本身并不建立在统一、标准、干净的官方协议上，因此不能简单将二者直接等同。更合理的结论是：在统一后的官方 Vaihingen 基准下，LightRefine 已经成为当前第三创新点中最值得保留的方案。')

    add_paragraph(doc, '7. 数据划分探索与后续路线', style='Heading 1')
    add_paragraph(doc, '为了进一步判断当前结果偏低是否受到官方 split 难度偏大的影响，项目中额外设计了两种数据重划分思路：一种是按 area 整块重划分；另一种是按同 area 分层切分，即 train 与 val 共享 area，但 patch 不重复。后者更适合作为工程验证集，用于观察模型结构改动是否稳定带来提升。')
    add_paragraph(doc, '在此基础上，还进一步构建了 stratified quick 与 stratified small 两套快速验证流程：前者适合先快速看趋势，后者适合在更小子集上跑一轮更完整的缩短版训练，以便更快获得相对稳定的结果。')

    add_paragraph(doc, '8. 当前代码与实验资产整理', style='Heading 1')
    add_paragraph(doc, '当前与改进创新3相关的核心代码资产包括：`variant_heads.py`（第三创新点候选模块实现）、`ukan_light_refine_da_tr_vaihingen.py`（方案2主实验配置）、`ukan_boundary_aux_da_tr_vaihingen.py`（方案1配置）、`ukan_multiscale_fusion_ablation_vaihingen.py`（方案3消融基准配置）、`ukan_light_refine_transfer_da_tr_vaihingen.py`（迁移版配置）、以及一系列用于重划分、快速验证、小数据子集实验的脚本与配置。')

    add_paragraph(doc, '9. 论文写作建议', style='Heading 1')
    add_paragraph(doc, '如果将当前工作写入论文，建议把第三创新点表述为：在双路编码器和 BRA/Tok-KAN bottleneck 的基础上，增加一个轻量级通道—空间联合重标定模块，对解码末端特征做进一步细化。这样可以形成一个逻辑清晰的三层创新链条：前端局部建模增强、中段全局语义增强、后端解码末端重标定增强。')
    add_paragraph(doc, '实验部分建议拆成两张主表：第一张表是主线消融（baseline、改进1、改进2、改进1+改进2、改进1+改进2+LightRefine）；第二张表是第三创新点内部对比（BoundaryAux、LightRefine、MultiScaleFusion、transfer 版等）。同时，可将方案3占位表保留为补充材料，待后续稳定结果补全。')

    add_paragraph(doc, '10. 总结', style='Heading 1')
    add_paragraph(doc, '综上，当前改进创新3已经从多个候选方向中收敛到 LightRefine 这一条主路线。它不是对前两个创新点的替代，而是在双路编码器与 BRA/Tok-KAN 主模型基础上的轻量补充增强。虽然在严格官方 Vaihingen 协议下，其数值还没有全面追平旧项目内部高结果，但从可复现性、稳定性和工程可控性角度看，LightRefine 已经是当前最有资格保留进最终模型的第三创新点。')

    doc.save(OUTPUT)
    print(OUTPUT)


if __name__ == '__main__':
    main()
