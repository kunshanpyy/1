norm_cfg = dict(type='BN', requires_grad=True)
backbone_norm_cfg = dict(type='LN', requires_grad=True)

model = dict(
    type='EncoderDecoderFull',
    pretrained=None,
    decode_head=dict(
        type='UKAN',
        da=True,
        tr=False,
        channels=32,
        num_classes=6,
        loss_decode=[
            dict(type='CrossEntropyLoss', loss_name='loss_ce', use_sigmoid=False, loss_weight=1.0),
            dict(type='DiceLoss', loss_name='loss_dice', loss_weight=1.0),
        ],
    ),
    train_cfg=dict(),
    test_cfg=dict(mode='slide', crop_size=(512, 512), stride=(256, 256)),
)

dataset_type = 'VaihingenOfficialDataset'
img_size = (512, 512)
crop_size = (512, 512)

train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='LoadAnnotations'),
    dict(type='Resize', img_scale=crop_size, keep_ratio=False),
    dict(type='RandomFlip', flip_ratio=0.5),
    dict(type='PhotoMetricDistortion'),
    dict(type='Normalize', mean=[0, 0, 0], std=[1, 1, 1], to_rgb=True),
    dict(type='Pad', size=crop_size, pad_val=0, seg_pad_val=255),
    dict(type='DefaultFormatBundle'),
    dict(type='Collect', keys=['img', 'gt_semantic_seg']),
]

test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(
        type='MultiScaleFlipAug',
        img_scale=img_size,
        flip=False,
        transforms=[
            dict(type='Resize', keep_ratio=False),
            dict(type='Normalize', mean=[0, 0, 0], std=[1, 1, 1], to_rgb=True),
            dict(type='ImageToTensor', keys=['img']),
            dict(type='Collect', keys=['img']),
        ])
]

data_root = './data/vaihingen/'

data = dict(
    samples_per_gpu=1,
    workers_per_gpu=2,
    train=dict(type=dataset_type, data_root=data_root, img_dir='img_dir/train', ann_dir='ann_dir/train', pipeline=train_pipeline),
    val=dict(type=dataset_type, data_root=data_root, img_dir='img_dir/val', ann_dir='ann_dir/val', pipeline=test_pipeline),
    test=dict(type=dataset_type, data_root=data_root, img_dir='img_dir/val', ann_dir='ann_dir/val', pipeline=test_pipeline),
)

log_config = dict(interval=50, hooks=[dict(type='TextLoggerHook', by_epoch=False)])
dist_params = dict(backend='nccl')
log_level = 'INFO'
load_from = None
resume_from = None
workflow = [('train', 1)]
cudnn_benchmark = False
find_unused_parameters = True
auto_resume = False
device = 'cuda'
seed = 0
optimizer = dict(type='Adam', lr=5e-4, betas=(0.9, 0.999))
optimizer_config = dict()
lr_config = dict(policy='poly', power=0.9, min_lr=1e-5, by_epoch=False)
runner = dict(type='IterBasedRunner', max_iters=20000)
checkpoint_config = dict(by_epoch=False, save_optimizer=False, interval=20000)
evaluation = dict(interval=4000, metric=['mIoU', 'mFscore', 'mDice'])
work_dir = './work_dirs/ukan_da_vaihingen'
gpu_ids = range(0, 1)
