import json
import os
import cv2
import numpy as np
from matplotlib import pyplot as plt
from pycocotools import mask as maskUtils
from tifffile import imread
from collections import defaultdict


def load_coco_annotations(annotation_path):
    with open(annotation_path, 'r') as f:
        coco_data = json.load(f)
    return coco_data


def prepare_dataset(annotation_path, image_dir, output_dir):
    # if you have no such folders
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'images'), exist_ok=True)
    os.makedirs(os.path.join(output_dir, 'masks'), exist_ok=True)

    coco_data = load_coco_annotations(annotation_path)

    images_info = {img['id']: img for img in coco_data['images']}
    annotations_info = defaultdict(list)

    for ann in coco_data['annotations']:
        annotations_info[ann['image_id']].append(ann)

    for image_id, anns in annotations_info.items():
        image_info = images_info[image_id]
        image_path = os.path.join(image_dir, image_info['file_name'])
        image = cv2.imread(image_path)

        mask = np.zeros([image.shape[0], image.shape[1]], dtype=np.uint8)

        for ann in anns:
            if type(ann['segmentation']) is list:
                segmentation = ann['segmentation'][0]
                points = np.array(segmentation).reshape(-1, 2).astype(int)
                cv2.fillPoly(mask, [points], color=255)
            elif type(ann['segmentation']) is dict:
                # Decode the RLE segmentation
                rle = ann['segmentation'].copy()
                rle_count_bytes = []
                rle_size_bytes = []
                for number in rle['counts']:
                    rle_count_bytes.append(number.to_bytes(8, 'big'))
                rle['counts'] = b''.join(rle_count_bytes)

                for number in rle['size']:
                    rle_size_bytes.append(number.to_bytes(8, 'big'))
                rle['size'] = b''.join(rle_size_bytes)

                binary_mask = maskUtils.decode(rle)
                contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for contour in contours:
                    cv2.fillPoly(mask, [contour], color=255)

        output_image_path = os.path.join(output_dir, 'images', image_info['file_name'])
        output_mask_path = os.path.join(output_dir, 'masks', image_info['file_name'])

        cv2.imwrite(output_image_path, image)
        cv2.imwrite(output_mask_path, mask)


def filter_mask(mask, threshold=0.55):
    mask_area = np.sum(mask > 0)

    total_area = mask.shape[0] * mask.shape[1]
    relative_area = mask_area / total_area

    if relative_area > threshold:
        return False
    else:
        return True


def get_dataset(image_dir, mask_dir, image_size, sample_count=None):
    images = []
    masks = []

    for image_name in os.listdir(image_dir):
        img = imread(os.path.join(image_dir, image_name))
        img = cv2.resize(img, image_size)

        for mask_name in os.listdir(mask_dir):
            if mask_name == image_name:
                mask = imread(os.path.join(mask_dir, mask_name))
                mask = cv2.resize(mask, image_size)

                if filter_mask(np.array(mask)):
                    masks.append(mask)
                    images.append(img)

        if sample_count and len(images) >= sample_count:
            break

    images = np.array(images) / 255.0
    masks = np.array(masks)

    masks[masks > 0] = 1
    masks = np.expand_dims(masks, axis=-1).astype(np.float32)

    return images, masks


annotation_path = "/data/code2025/Q2/2025-08-12-01/2_train5percent.json"
image_dir = "/data/code2025/Q2/2025-08-12-01/livecell_train_val_images"
output_dir = "/data/code2025/Q2/2025-08-12-01/dataset"
output_img_dir = os.path.join(output_dir, 'images')
output_masks_dir = os.path.join(output_dir, 'masks')
prepare_dataset(annotation_path, image_dir, output_dir)