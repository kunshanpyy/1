import argparse
import os
import os.path as osp
import re
import shutil
from collections import Counter, defaultdict


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


def copy_pairs(file_list, src_img_dir, src_ann_dir, dst_img_dir, dst_ann_dir):
    ensure_dir(dst_img_dir)
    ensure_dir(dst_ann_dir)
    copied = 0
    missing = []
    for img_name in file_list:
        src_img = osp.join(src_img_dir, img_name)
        src_ann = osp.join(src_ann_dir, img_name)
        if not osp.exists(src_img) or not osp.exists(src_ann):
            missing.append(img_name)
            continue
        shutil.copy2(src_img, osp.join(dst_img_dir, img_name))
        shutil.copy2(src_ann, osp.join(dst_ann_dir, img_name))
        copied += 1
    return copied, missing


def main():
    parser = argparse.ArgumentParser(description='Resplit converted Vaihingen patches by area names.')
    parser.add_argument('--src-root', default='./data/vaihingen', help='Source converted Vaihingen root')
    parser.add_argument('--dst-root', default='./data/vaihingen_resplit', help='Destination resplit root')
    parser.add_argument('--train-areas', nargs='+', required=True,
                        help='Area ids for train split, e.g. area1 area3 area5')
    parser.add_argument('--val-areas', nargs='+', required=True,
                        help='Area ids for val split, e.g. area2 area4 area6')
    parser.add_argument('--copy-test-from-val', action='store_true',
                        help='If set, test split will mirror val split')
    args = parser.parse_args()

    src_img_train = osp.join(args.src_root, 'img_dir', 'train')
    src_img_val = osp.join(args.src_root, 'img_dir', 'val')
    src_ann_train = osp.join(args.src_root, 'ann_dir', 'train')
    src_ann_val = osp.join(args.src_root, 'ann_dir', 'val')

    src_img_files = collect_files(src_img_train) + collect_files(src_img_val)
    src_ann_files = collect_files(src_ann_train) + collect_files(src_ann_val)

    img_names = [osp.basename(x) for x in src_img_files]
    ann_names = {osp.basename(x) for x in src_ann_files}
    img_names = [x for x in img_names if x in ann_names]

    area_to_files = defaultdict(list)
    unknown = []
    for name in sorted(set(img_names)):
        area = extract_area(name)
        if area is None:
            unknown.append(name)
            continue
        area_to_files[area].append(name)

    train_areas = set(args.train_areas)
    val_areas = set(args.val_areas)
    overlap = train_areas & val_areas
    if overlap:
        raise ValueError(f'Overlapping areas in train/val: {sorted(overlap)}')

    all_areas = sorted(area_to_files.keys(), key=lambda x: int(x.replace('area', '')))
    train_files, val_files = [], []
    unassigned_areas = []
    for area in all_areas:
        if area in train_areas:
            train_files.extend(area_to_files[area])
        elif area in val_areas:
            val_files.extend(area_to_files[area])
        else:
            unassigned_areas.append(area)

    dst_img_train = osp.join(args.dst_root, 'img_dir', 'train')
    dst_img_val = osp.join(args.dst_root, 'img_dir', 'val')
    dst_ann_train = osp.join(args.dst_root, 'ann_dir', 'train')
    dst_ann_val = osp.join(args.dst_root, 'ann_dir', 'val')

    copied_train, missing_train = copy_pairs(
        train_files,
        src_img_train if osp.exists(src_img_train) else src_img_val,
        src_ann_train if osp.exists(src_ann_train) else src_ann_val,
        dst_img_train,
        dst_ann_train,
    )

    if missing_train:
        copied_train, missing_train = copy_pairs(
            train_files,
            osp.join(args.src_root, 'img_dir', 'val'),
            osp.join(args.src_root, 'ann_dir', 'val'),
            dst_img_train,
            dst_ann_train,
        )

    copied_val, missing_val = copy_pairs(
        val_files,
        src_img_train if osp.exists(src_img_train) else src_img_val,
        src_ann_train if osp.exists(src_ann_train) else src_ann_val,
        dst_img_val,
        dst_ann_val,
    )

    if missing_val:
        copied_val, missing_val = copy_pairs(
            val_files,
            osp.join(args.src_root, 'img_dir', 'val'),
            osp.join(args.src_root, 'ann_dir', 'val'),
            dst_img_val,
            dst_ann_val,
        )

    if args.copy_test_from_val:
        dst_img_test = osp.join(args.dst_root, 'img_dir', 'test')
        dst_ann_test = osp.join(args.dst_root, 'ann_dir', 'test')
        ensure_dir(dst_img_test)
        ensure_dir(dst_ann_test)
        for f in val_files:
            src_img = osp.join(dst_img_val, f)
            src_ann = osp.join(dst_ann_val, f)
            if osp.exists(src_img):
                shutil.copy2(src_img, osp.join(dst_img_test, f))
            if osp.exists(src_ann):
                shutil.copy2(src_ann, osp.join(dst_ann_test, f))

    print('=== Vaihingen Resplit Summary ===')
    print('Source root:', args.src_root)
    print('Target root:', args.dst_root)
    print('All detected areas:', all_areas)
    print('Train areas:', sorted(train_areas, key=lambda x: int(x.replace('area', ''))))
    print('Val areas:', sorted(val_areas, key=lambda x: int(x.replace('area', ''))))
    print('Train patch count:', len(train_files))
    print('Val patch count:', len(val_files))
    print('Unassigned areas:', unassigned_areas)
    if unknown:
        print('Files with unknown area pattern:', unknown[:20])
    print('Train distribution:', dict(sorted((k, len(v)) for k, v in area_to_files.items() if k in train_areas)))
    print('Val distribution:', dict(sorted((k, len(v)) for k, v in area_to_files.items() if k in val_areas)))
    print('Done.')
    print('You can point data_root to:', args.dst_root)


if __name__ == '__main__':
    main()
