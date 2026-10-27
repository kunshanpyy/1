import argparse
import os
import os.path as osp
import random
import shutil
from collections import defaultdict


VALID_EXTS = {'.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp'}


def ensure_dir(path):
    os.makedirs(path, exist_ok=True)


def list_files(path):
    if not osp.exists(path):
        return []
    return sorted(
        f for f in os.listdir(path)
        if osp.splitext(f)[1].lower() in VALID_EXTS
    )


def extract_area(name):
    return name.split('_')[0] if '_' in name else 'unknown'


def build_subset(src_root, dst_root, max_per_area_train=60, max_per_area_val=20, copy_test=True, seed=42):
    rng = random.Random(seed)
    for split, max_per_area in [('train', max_per_area_train), ('val', max_per_area_val)]:
        src_img = osp.join(src_root, 'img_dir', split)
        src_ann = osp.join(src_root, 'ann_dir', split)
        dst_img = osp.join(dst_root, 'img_dir', split)
        dst_ann = osp.join(dst_root, 'ann_dir', split)
        ensure_dir(dst_img)
        ensure_dir(dst_ann)

        files = list_files(src_img)
        files = [f for f in files if osp.exists(osp.join(src_ann, f))]
        by_area = defaultdict(list)
        for f in files:
            by_area[extract_area(f)].append(f)

        total = 0
        for area, area_files in sorted(by_area.items()):
            area_files = sorted(area_files)
            rng.shuffle(area_files)
            chosen = area_files[:min(len(area_files), max_per_area)]
            for f in chosen:
                shutil.copy2(osp.join(src_img, f), osp.join(dst_img, f))
                shutil.copy2(osp.join(src_ann, f), osp.join(dst_ann, f))
            print(f'[INFO] {split} {area}: {len(chosen)}/{len(area_files)} copied')
            total += len(chosen)
        print(f'[INFO] {split} total copied: {total}')

    if copy_test:
        src_img = osp.join(src_root, 'img_dir', 'val')
        src_ann = osp.join(src_root, 'ann_dir', 'val')
        dst_img = osp.join(dst_root, 'img_dir', 'test')
        dst_ann = osp.join(dst_root, 'ann_dir', 'test')
        ensure_dir(dst_img)
        ensure_dir(dst_ann)
        for f in list_files(osp.join(dst_root, 'img_dir', 'val')):
            shutil.copy2(osp.join(src_img, f), osp.join(dst_img, f))
            shutil.copy2(osp.join(src_ann, f), osp.join(dst_ann, f))
        print('[INFO] test split copied from subset val split')


def main():
    parser = argparse.ArgumentParser(description='Build a smaller Vaihingen subset for quick full-pipeline experiments.')
    parser.add_argument('--src-root', default='./data/vaihingen_stratified', help='Source dataset root')
    parser.add_argument('--dst-root', default='./data/vaihingen_stratified_small', help='Target small dataset root')
    parser.add_argument('--train-per-area', type=int, default=60, help='Max train patches per area')
    parser.add_argument('--val-per-area', type=int, default=20, help='Max val patches per area')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    build_subset(
        src_root=args.src_root,
        dst_root=args.dst_root,
        max_per_area_train=args.train_per_area,
        max_per_area_val=args.val_per_area,
        copy_test=True,
        seed=args.seed,
    )
    print('[DONE] Small subset prepared at:', args.dst_root)


if __name__ == '__main__':
    main()
