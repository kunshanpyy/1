import torch
import torch.nn as nn
import torch.nn.functional as F

from mmseg.models.builder import HEADS
from mmseg.models.decode_heads.ukan import UKAN


class _UKANVariantBase(UKAN):
    """Base class for low-coupling innovation variants built on top of the
    strong UKAN main model (dual encoder + BRA bottleneck).
    """

    def _forward_backbone(self, x):
        B = x.shape[0]

        out = F.relu(F.max_pool2d(self.encoder1(x), 2, 2))
        t1 = out

        out = F.relu(F.max_pool2d(self.encoder2(out), 2, 2))
        t2 = out

        out = F.relu(F.max_pool2d(self.encoder3(out), 2, 2))
        t3 = out

        if self.da:
            features = self.maxvit(x)
            t1 = self.merge1(torch.concat([t1, features[0]], dim=1))
            t2 = self.merge2(torch.concat([t2, features[1]], dim=1))
            t3 = self.merge3(torch.concat([t3, features[2]], dim=1))

        out, H, W = self.patch_embed3(out)
        for blk in self.block1:
            out = blk(out, H, W)
        out = self.norm3(out)
        out = out.reshape(B, H, W, -1).permute(0, 3, 1, 2).contiguous()
        t4 = out

        out, H, W = self.patch_embed4(out)
        for blk in self.block2:
            out = blk(out, H, W)
        out = self.norm4(out)
        out = out.reshape(B, H, W, -1).permute(0, 3, 1, 2).contiguous()

        if self.tr:
            t4 = self.tr_model1(t4) + t4
            out = self.tr_model2(out) + out

        out = F.relu(F.interpolate(self.decoder1(out), scale_factor=(2, 2), mode='bilinear', align_corners=False))
        out = torch.add(out, t4)

        _, _, H, W = out.shape
        out = out.flatten(2).transpose(1, 2)
        for blk in self.dblock1:
            out = blk(out, H, W)
        out = self.dnorm3(out)
        out = out.reshape(B, H, W, -1).permute(0, 3, 1, 2).contiguous()

        out = F.relu(F.interpolate(self.decoder2(out), scale_factor=(2, 2), mode='bilinear', align_corners=False))
        out = torch.add(out, t3)

        _, _, H, W = out.shape
        out = out.flatten(2).transpose(1, 2)
        for blk in self.dblock2:
            out = blk(out, H, W)
        out = self.dnorm4(out)
        out = out.reshape(B, H, W, -1).permute(0, 3, 1, 2).contiguous()

        out = F.relu(F.interpolate(self.decoder3(out), scale_factor=(2, 2), mode='bilinear', align_corners=False))
        out = torch.add(out, t2)

        out = F.relu(F.interpolate(self.decoder4(out), scale_factor=(2, 2), mode='bilinear', align_corners=False))
        out = torch.add(out, t1)

        out = F.relu(F.interpolate(self.decoder5(out), scale_factor=(2, 2), mode='bilinear', align_corners=False))
        return out, {'t1': t1, 't2': t2, 't3': t3, 't4': t4}


@HEADS.register_module()
class UKAN_BoundaryAux(_UKANVariantBase):
    """方案1: Boundary-aware auxiliary refinement.

    Lightweight edge prior is extracted from shallow t1 feature and used to
    refine the final decoder feature without rewriting the main fusion path.
    """

    def __init__(self, refine_reduction=4, **kwargs):
        super().__init__(**kwargs)
        embed_dims = kwargs.get('embed_dims', [256, 320, 512])
        final_ch = embed_dims[0] // 8
        shallow_ch = embed_dims[0] // 8
        hidden = max(final_ch // refine_reduction, 8)

        self.edge_refine = nn.Sequential(
            nn.Conv2d(shallow_ch, shallow_ch, kernel_size=3, padding=1, groups=shallow_ch, bias=False),
            nn.BatchNorm2d(shallow_ch),
            nn.Conv2d(shallow_ch, hidden, kernel_size=1, bias=False),
            nn.BatchNorm2d(hidden),
            nn.ReLU(inplace=True),
            nn.Conv2d(hidden, final_ch, kernel_size=1, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x):
        out, feats = self._forward_backbone(x)
        t1 = feats['t1']
        edge_seed = torch.abs(t1 - F.avg_pool2d(t1, kernel_size=3, stride=1, padding=1))
        edge_map = self.edge_refine(edge_seed)
        edge_map = F.interpolate(edge_map, size=out.shape[2:], mode='bilinear', align_corners=False)
        out = out + out * edge_map
        return self.cls_seg(out)


class _ChannelSpatialRefine(nn.Module):
    def __init__(self, channels, reduction=4):
        super().__init__()
        hidden = max(channels // reduction, 8)
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.channel_gate = nn.Sequential(
            nn.Conv2d(channels, hidden, kernel_size=1, bias=False),
            nn.ReLU(inplace=True),
            nn.Conv2d(hidden, channels, kernel_size=1, bias=False),
            nn.Sigmoid(),
        )
        self.spatial_gate = nn.Sequential(
            nn.Conv2d(2, 1, kernel_size=7, padding=3, bias=False),
            nn.Sigmoid(),
        )

    def forward(self, x):
        ch = self.channel_gate(self.avg_pool(x))
        x_ch = x * ch
        avg_map = torch.mean(x_ch, dim=1, keepdim=True)
        max_map, _ = torch.max(x_ch, dim=1, keepdim=True)
        sp = self.spatial_gate(torch.cat([avg_map, max_map], dim=1))
        return x_ch * sp + x


@HEADS.register_module()
class UKAN_LightRefine(_UKANVariantBase):
    """方案2: Lightweight channel-spatial refinement head.

    Keeps the strong da+tr main path unchanged and only performs a lightweight
    residual reweighting before final segmentation.
    """

    def __init__(self, refine_reduction=4, **kwargs):
        super().__init__(**kwargs)
        embed_dims = kwargs.get('embed_dims', [256, 320, 512])
        final_ch = embed_dims[0] // 8
        self.refine = _ChannelSpatialRefine(final_ch, reduction=refine_reduction)

    def forward(self, x):
        out, _ = self._forward_backbone(x)
        out = self.refine(out)
        return self.cls_seg(out)


@HEADS.register_module()
class UKAN_MultiScaleFusion(_UKANVariantBase):
    """方案3: Deep-supervision-inspired multi-scale fusion.

    Uses intermediate decoder/encoder features as auxiliary multi-scale context
    and fuses them back into the final decoder feature with a lightweight head.
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        embed_dims = kwargs.get('embed_dims', [256, 320, 512])
        final_ch = embed_dims[0] // 8
        self.proj_t1 = nn.Conv2d(embed_dims[0] // 8, final_ch, kernel_size=1, bias=False)
        self.proj_t2 = nn.Conv2d(embed_dims[0] // 4, final_ch, kernel_size=1, bias=False)
        self.proj_t3 = nn.Conv2d(embed_dims[0], final_ch, kernel_size=1, bias=False)
        self.proj_t4 = nn.Conv2d(embed_dims[1], final_ch, kernel_size=1, bias=False)
        self.fuse = nn.Sequential(
            nn.Conv2d(final_ch * 5, final_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(final_ch),
            nn.ReLU(inplace=True),
            nn.Conv2d(final_ch, final_ch, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(final_ch),
            nn.ReLU(inplace=True),
        )

    def forward(self, x):
        out, feats = self._forward_backbone(x)
        size = out.shape[2:]
        f1 = self.proj_t1(F.interpolate(feats['t1'], size=size, mode='bilinear', align_corners=False))
        f2 = self.proj_t2(F.interpolate(feats['t2'], size=size, mode='bilinear', align_corners=False))
        f3 = self.proj_t3(F.interpolate(feats['t3'], size=size, mode='bilinear', align_corners=False))
        f4 = self.proj_t4(F.interpolate(feats['t4'], size=size, mode='bilinear', align_corners=False))
        out = out + self.fuse(torch.cat([out, f1, f2, f3, f4], dim=1))
        return self.cls_seg(out)
