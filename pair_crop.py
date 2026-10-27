import os
import cv2
import numpy as np
import random
import multiprocessing as mp
from tqdm import tqdm

# 设置路径
image_folder = ".//Potsdam_Vaihingen/images"  # 原图文件夹
mask_folder = ".//Potsdam_Vaihingen/labels"  # mask文件夹
output_image_folder = ".//Potsdam_Vaihingen/train/images_crop"  # 裁剪后图像存放文件夹
output_mask_folder = ".//Potsdam_Vaihingen/train/labels_crop"  # 裁剪后mask存放文件夹

# 目标尺寸
crop_size = 512
num_crops = 10000  # 目标裁剪数量
num_workers = 16  # 进程数

# 创建输出文件夹
os.makedirs(output_image_folder, exist_ok=True)
os.makedirs(output_mask_folder, exist_ok=True)

# 获取所有图像文件
image_files = sorted([f for f in os.listdir(image_folder) if f.endswith(('.png', '.jpg', '.jpeg'))])
mask_files = sorted([f for f in os.listdir(mask_folder) if f.endswith(('.png', '.jpg', '.jpeg'))])

# 确保文件名匹配
assert len(image_files) == len(mask_files), "原图和mask数量不匹配"
assert all(img.split('.')[0] == msk.split('.')[0] for img, msk in zip(image_files, mask_files)), "文件名不匹配"


def crop_and_save(task):
    """裁剪并保存图像"""
    idx, count = task
    random.seed()  # 让不同进程的随机种子不同

    image_path = os.path.join(image_folder, image_files[idx])
    mask_path = os.path.join(mask_folder, mask_files[idx])

    # 读取图像
    image = cv2.imread(image_path)
    mask = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)  # mask一般是单通道
    # mask = cv2.imread(mask_path)  # mask一般是单通道

    image = cv2.resize(image, (6000, 6000))
    mask = cv2.resize(mask, (6000, 6000))

    if image is None or mask is None:
        return 0  # 失败的任务返回0

    h, w = image.shape[:2]

    if h < crop_size or w < crop_size:
        return 0  # 失败的任务返回0

    # 随机裁剪
    x = random.randint(0, w - crop_size)
    y = random.randint(0, h - crop_size)

    cropped_image = image[y:y + crop_size, x:x + crop_size]
    cropped_mask = mask[y:y + crop_size, x:x + crop_size]

    # 保存
    output_image_path = os.path.join(output_image_folder, f"crop_{count:05d}.png")
    output_mask_path = os.path.join(output_mask_folder, f"crop_{count:05d}.png")

    cv2.imwrite(output_image_path, cropped_image)
    cv2.imwrite(output_mask_path, cropped_mask)

    return 1  # 成功的任务返回1


def main():
    """主函数，使用多进程进行裁剪"""
    with mp.Manager() as manager:
        task_list = [(random.randint(0, len(image_files) - 1), i) for i in range(num_crops)]

        with mp.Pool(num_workers) as pool, tqdm(total=num_crops, desc="裁剪进度") as pbar:
            for result in pool.imap_unordered(crop_and_save, task_list):
                pbar.update(result)  # 更新进度条



if __name__ == "__main__":
    main()
