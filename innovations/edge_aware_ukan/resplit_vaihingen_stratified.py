import argparse
import os
import os.path as osp
import random
import re
import shutil
from collections import defaultdict


AREA_PATTERN = re.compile(r'^(area\d+)_')


def collect_files(dir_path):
    if not osp.exists(dir_path):
        return []
    exts = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp'}
    return sorted(
        osp.join(dir_path, f)
        for f in os.listdir(dir_path)
        if osp.splitext(f)[1].lower() in exts
    )


def extract_area(filename):
    m = AREA_PATTERN.match(filename)
    return m.group(1) if m else None


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def copy_pairs(file_names, src_img_map, src_ann_map, dst_img_dir, dst_ann_dir):
    ensure_dir(dst_img_dir)
    ensure_dir(dst_ann_dir)
    copied = 0
    missing = []
    for name in file_names:
        src_img = src_img_map.get(name)
        src_ann = src_ann_map.get(name)
        if src_img is None or src_ann is None:
            missing.append(name)
            continue
        shutil.copy2(src_img, osp.join(dst_img_dir, name))
        shutil.copy2(src_ann, osp.join(dst_ann_dir, name))
        copied += 1
    return copied, missing


def main():
    parser = argparse.ArgumentParser(description='Stratified resplit of converted Vaihingen patches by area.')
    parser.add_argument('--src-root', default='./data/vaihingen', help='Source converted Vaihingen root')
    parser.add_argument('--dst-root', default='./data/vaihingen_stratified', help='Destination root for stratified split')
    parser.add_argument('--val-ratio', type=float, default=0.2, help='Validation ratio within each area')
    parser.add_argument('--seed', type=int, default=42, help='Random seed')
    parser.add_argument('--min-val-per-area', type=int, default=1, help='Minimum validation patches per area')
    parser.add_argument('--copy-test-from-val', action='store_true', help='If set, create test split by copying val split')
    args = parser.parse_args()

    if not (0.0 < args.val_ratio < 1.0):
        raise ValueError('val-ratio must be in (0, 1).')

    src_img_train = osp.join(args.src_root, 'img_dir', 'train')
    src_img_val = osp.join(args.src_root, 'img_dir', 'val')
    src_ann_train = osp.join(args.src_root, 'ann_dir', 'train')
    src_ann_val = osp.join(args.src_root, 'ann_dir', 'val')

    img_files = collect_files(src_img_train) + collect_files(src_img_val)
    ann_files = collect_files(src_ann_train) + collect_files(src_ann_val)

    img_map = {osp.basename(x): x for x in img_files}
    ann_map = {osp.basename(x): x for x in ann_files}
    common_names = sorted(set(img_map.keys()) & set(ann_map.keys()))

    area_to_files = defaultdict(list)
    unknown = []
    for name in common_names:
        area = extract_area(name)
        if area is None:
            unknown.append(name)
            continue
        area_to_files[area].append(name)

    rng = random.Random(args.seed)
    train_files, val_files = [], []
    area_stats = {}
    for area in sorted(area_to_files.keys(), key=lambda x: int(x.replace('area', ''))):
        names = sorted(area_to_files[area])
        rng.shuffle(names)
        n_total = len(names)
        n_val = max(args.min_val_per_area, int(round(n_total * args.val_ratio)))
        n_val = min(n_val, max(1, n_total - 1)) if n_total > 1 else 0
        area_val = names[:n_val]
        area_train = names[n_val:]
        train_files.extend(area_train)
        val_files.extend(area_val)
        area_stats[area] = dict(total=n_total, train=len(area_train), val=len(area_val))

    dst_img_train = osp.join(args.dst_root, 'img_dir', 'train')
    dst_img_val = osp.join(args.dst_root, 'img_dir', 'val')
    dst_ann_train = osp.join(args.dst_root, 'ann_dir', 'train')
    dst_ann_val = osp.join(args.dst_root, 'ann_dir', 'val')

    copied_train, missing_train = copy_pairs(train_files, img_map, ann_map, dst_img_train, dst_ann_train)
    copied_val, missing_val = copy_pairs(val_files, img_map, ann_map, dst_img_val, dst_ann_val)

    if args.copy_test_from_val:
        dst_img_test = osp.join(args.dst_root, 'img_dir', 'test')
        dst_ann_test = osp.join(args.dst_root, 'ann_dir', 'test')
        ensure_dir(dst_img_test)
        ensure_dir(dst_ann_test)
        for name in val_files:
            shutil.copy2(osp.join(dst_img_val, name), osp.join(dst_img_test, name))
            shutil.copy2(osp.join(dst_ann_val, name), osp.join(dst_ann_test, name))

    print('=== Vaihingen Stratified Resplit Summary ===')
    print('Source root:', args.src_root)
    print('Target root:', args.dst_root)
    print('Seed:', args.seed)
    print('Val ratio:', args.val_ratio)
    print('Areas:', sorted(area_stats.keys(), key=lambda x: int(x.replace('area', ''))))
    print('Train patch count:', len(train_files), 'copied:', copied_train)
    print('Val patch count:', len(val_files), 'copied:', copied_val)
    print('Missing train pairs:', len(missing_train))
    print('Missing val pairs:', len(missing_val))
    if unknown:
        print('Unknown filename pattern:', unknown[:20])
    print('Per-area stats:')
    for area in sorted(area_stats.keys(), key=lambda x: int(x.replace('area', ''))):
        s = area_stats[area]
        print(f'  {area}: total={s["total"]}, train={s["train"]}, val={s["val"]}')
    print('Done.')
    print('You can point data_root to:', args.dst_root)


if __name__ == '__main__':
    main()
