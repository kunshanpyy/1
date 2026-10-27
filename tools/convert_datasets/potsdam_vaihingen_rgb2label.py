# Copyright (c) OpenMMLab. All rights reserved.
import argparse
import os
import os.path as osp

import mmcv
import numpy as np
from PIL import Image

potsdam_vaihingen_palette = {
    0: (255, 255, 255),  # impervious_surface / background-like white region in current labels
    1: (0, 0, 255),      # building
    2: (0, 255, 255),    # low_vegetation
    3: (0, 255, 0),      # tree
    4: (255, 255, 0),    # car
    5: (255, 0, 0),      # clutter / background depending on your taxonomy
}

potsdam_vaihingen_invert_palette = {
    v: k for k, v in potsdam_vaihingen_palette.items()
}


def convert_from_color(arr_3d, palette=potsdam_vaihingen_invert_palette, ignore_index=255):
    """RGB-color encoding to grayscale label ids.

    Args:
        arr_3d (np.ndarray): RGB mask with shape (H, W, 3).
        palette (dict): Mapping from RGB tuple to class index.
        ignore_index (int): Value used for unknown colors.

    Returns:
        np.ndarray: Single-channel label map with shape (H, W).
    """
    arr_2d = np.full((arr_3d.shape[0], arr_3d.shape[1]), ignore_index, dtype=np.uint8)

    for color, idx in palette.items():
        match = np.all(arr_3d == np.array(color).reshape(1, 1, 3), axis=2)
        arr_2d[match] = idx

    return arr_2d


def convert_file(src_path, dst_path, palette, ignore_index=255):
    mask = mmcv.imread(src_path, channel_order='rgb')
    label = convert_from_color(mask, palette=palette, ignore_index=ignore_index)
    Image.fromarray(label.astype(np.uint8), mode='L').save(dst_path)



def convert_dir(src_dir, dst_dir, palette, ignore_index=255):
    mmcv.mkdir_or_exist(dst_dir)
    files = sorted([f for f in os.listdir(src_dir) if f.lower().endswith('.png')])
    prog_bar = mmcv.ProgressBar(len(files))
    for filename in files:
        convert_file(
            osp.join(src_dir, filename),
            osp.join(dst_dir, filename),
            palette=palette,
            ignore_index=ignore_index)
        prog_bar.update()



def parse_args():
    parser = argparse.ArgumentParser(
        description='Convert Potsdam/Vaihingen RGB masks to single-channel label ids')
    parser.add_argument('dataset_path', help='Dataset root, e.g. ./Potsdam_Vaihingen')
    parser.add_argument(
        '--src_subdirs',
        nargs='+',
        default=['train/labels', 'test/labels'],
        help='Relative label directories to convert')
    parser.add_argument(
        '--dst_suffix',
        default='_labelid',
        help='Suffix appended to each converted directory name')
    parser.add_argument(
        '--ignore_index',
        default=255,
        type=int,
        help='Ignore value for unknown colors')
    return parser.parse_args()



def main():
    args = parse_args()

    print('Using palette mapping:')
    for idx, color in potsdam_vaihingen_palette.items():
        print(f'  class {idx}: {color}')

    for rel_dir in args.src_subdirs:
        src_dir = osp.join(args.dataset_path, rel_dir)
        dst_dir = src_dir + args.dst_suffix
        assert osp.exists(src_dir), f'Not found: {src_dir}'
        print(f'Converting {src_dir} -> {dst_dir}')
        convert_dir(
            src_dir,
            dst_dir,
            palette=potsdam_vaihingen_invert_palette,
            ignore_index=args.ignore_index)

    print('\nDone.')
    print('You can then point mmseg ann_dir to the converted folders, e.g.:')
    print('  train/labels_labelid')
    print('  test/labels_labelid')


if __name__ == '__main__':
    main()
