import torch
import torch.nn as nn
import torch.nn.functional as F

from mmseg.models.builder import HEADS
from mmseg.models.decode_heads.ukan import UKAN


class EdgeAwareGate(nn.Module):
    """Edge-aware adaptive fusion for decoder-skip aggregation.

    Motivation:
    UKAN currently uses direct addition for skip fusion. This module first extracts
    a lightweight edge response from skip features, enhances shallow structure, and
    then predicts a spatial gate to adaptively mix decoder semantics with skip detail.
    """

    def __init__(self, channels, reduction=4):
        super().__init__()
        hidden = max(channels // reduction, 8)

        self.edge_conv = nn.Sequential(
            nn.Conv2d(channels, channels, kernel_size=3, padding=1, groups=channels, bias=False),
            nn.BatchNorm2d(channels),
            nn.Conv2d(channels, channels, kernel_size=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.Sigmoid(),
        )

        self.gate = nn.Sequential(
            nn.Conv2d(channels * 3, hidden, kernel_size=1, bias=False),
            nn.BatchNorm2d(hidden),
            nn.ReLU(inplace=True),
            nn.Conv2d(hidden, channels, kernel_size=3, padding=1, bias=False),
            nn.BatchNorm2d(channels),
            nn.Sigmoid(),
        )

    def forward(self, dec_feat, skip_feat):
        # lightweight edge prior from high-frequency skip residual
        pooled = F.avg_pool2d(skip_feat, kernel_size=3, stride=1, padding=1)
        edge_seed = torch.abs(skip_feat - pooled)
        edge_map = self.edge_conv(edge_seed)

        # enhance shallow structure before fusion
        skip_enhanced = skip_feat + skip_feat * edge_map

        # adaptive gate conditioned on decoder / skip / discrepancy
        fusion_context = torch.cat([
            dec_feat,
            skip_enhanced,
            torch.abs(dec_feat - skip_enhanced)
        ], dim=1)
        gate = self.gate(fusion_context)

        out = dec_feat * (1.0 - gate) + skip_enhanced * gate
        return out


@HEADS.register_module()
class UKAN_EAG(UKAN):
    """UKAN with Edge-Aware Adaptive Skip Fusion (EASF).

    Innovation point:
    Replace plain additive skip fusion with edge-guided gated fusion, targeting
    boundary sharpening and small-structure preservation in remote sensing.
    """

    def __init__(self, edge_reduction=4, **kwargs):
        super().__init__(**kwargs)
        embed_dims = kwargs.get('embed_dims', [256, 320, 512])

        self.skip_fuse4 = EdgeAwareGate(embed_dims[1], reduction=edge_reduction)      # 320
        self.skip_fuse3 = EdgeAwareGate(embed_dims[0], reduction=edge_reduction)      # 256
        self.skip_fuse2 = EdgeAwareGate(embed_dims[0] // 4, reduction=edge_reduction) # 64
        self.skip_fuse1 = EdgeAwareGate(embed_dims[0] // 8, reduction=edge_reduction) # 32

    def forward(self, x):
        B = x.shape[0]

        # ===== Encoder =====
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

        # ===== Tokenized KAN encoder =====
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

        # ===== Decoder with edge-aware gated skip fusion =====
        out = F.relu(F.interpolate(self.decoder1(out), scale_factor=(2, 2), mode='bilinear', align_corners=False))
        out = self.skip_fuse4(out, t4)

        _, _, H, W = out.shape
        out = out.flatten(2).transpose(1, 2)
        for blk in self.dblock1:
            out = blk(out, H, W)

        out = self.dnorm3(out)
        out = out.reshape(B, H, W, -1).permute(0, 3, 1, 2).contiguous()
        out = F.relu(F.interpolate(self.decoder2(out), scale_factor=(2, 2), mode='bilinear', align_corners=False))
        out = self.skip_fuse3(out, t3)

        _, _, H, W = out.shape
        out = out.flatten(2).transpose(1, 2)
        for blk in self.dblock2:
            out = blk(out, H, W)

        out = self.dnorm4(out)
        out = out.reshape(B, H, W, -1).permute(0, 3, 1, 2).contiguous()

        out = F.relu(F.interpolate(self.decoder3(out), scale_factor=(2, 2), mode='bilinear', align_corners=False))
        out = self.skip_fuse2(out, t2)

        out = F.relu(F.interpolate(self.decoder4(out), scale_factor=(2, 2), mode='bilinear', align_corners=False))
        out = self.skip_fuse1(out, t1)

        out = F.relu(F.interpolate(self.decoder5(out), scale_factor=(2, 2), mode='bilinear', align_corners=False))
        out = self.cls_seg(out)
        return out
