"""
CliniScan+ Dataset Preparation Pipeline
Transforms VinBigData Chest X-ray dataset into Ultralytics YOLO11 format
with 10 selected lung abnormality classes.
"""

import os
import shutil
import argparse
import logging
from typing import Dict, List, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from tqdm import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 10 Target Lung Abnormality Classes
TARGET_CLASSES = [
    "Atelectasis",
    "ILD",
    "Pulmonary fibrosis",
    "Pneumothorax",
    "Pleural effusion",
    "Pleural thickening",
    "Consolidation",
    "Lung Opacity",
    "Nodule/Mass",
    "Infiltration"
]

CLASS_TO_ID = {name: idx for idx, name in enumerate(TARGET_CLASSES)}
ID_TO_CLASS = {idx: name for idx, name in enumerate(TARGET_CLASSES)}


def calculate_iou(box1: List[float], box2: List[float]) -> float:
    """
    Calculate Intersection over Union (IoU) between two bounding boxes
    Box format: [x_min, y_min, x_max, y_max]
    """
    x1 = max(box1[0], box2[0])
    y1 = max(box1[1], box2[1])
    x2 = min(box1[2], box2[2])
    y2 = min(box1[3], box2[3])

    intersection = max(0.0, x2 - x1) * max(0.0, y2 - y1)
    if intersection == 0.0:
        return 0.0

    area1 = (box1[2] - box1[0]) * (box1[3] - box1[1])
    area2 = (box2[2] - box2[0]) * (box2[3] - box2[1])
    union = area1 + area2 - intersection
    return intersection / union if union > 0 else 0.0


def consolidate_boxes(boxes_for_image: List[Dict], iou_threshold: float = 0.5) -> List[Dict]:
    """
    Consolidate overlapping annotations of the same class from multiple radiologists.
    Averages coordinates for bounding boxes exceeding the IoU threshold.
    """
    if not boxes_for_image:
        return []

    # Group by class
    by_class: Dict[int, List[Dict]] = {}
    for b in boxes_for_image:
        by_class.setdefault(b["class_id"], []).append(b)

    consolidated = []
    for cls_id, b_list in by_class.items():
        used = [False] * len(b_list)
        for i in range(len(b_list)):
            if used[i]:
                continue
            matched_group = [b_list[i]]
            used[i] = True
            for j in range(i + 1, len(b_list)):
                if not used[j]:
                    box_a = [b_list[i]["x_min"], b_list[i]["y_min"], b_list[i]["x_max"], b_list[i]["y_max"]]
                    box_b = [b_list[j]["x_min"], b_list[j]["y_min"], b_list[j]["x_max"], b_list[j]["y_max"]]
                    if calculate_iou(box_a, box_b) >= iou_threshold:
                        matched_group.append(b_list[j])
                        used[j] = True

            # Average coordinates across consensus group
            avg_xmin = sum(b["x_min"] for b in matched_group) / len(matched_group)
            avg_ymin = sum(b["y_min"] for b in matched_group) / len(matched_group)
            avg_xmax = sum(b["x_max"] for b in matched_group) / len(matched_group)
            avg_ymax = sum(b["y_max"] for b in matched_group) / len(matched_group)
            img_w = matched_group[0]["width"]
            img_h = matched_group[0]["height"]

            consolidated.append({
                "class_id": cls_id,
                "class_name": matched_group[0]["class_name"],
                "x_min": avg_xmin,
                "y_min": avg_ymin,
                "x_max": avg_xmax,
                "y_max": avg_ymax,
                "width": img_w,
                "height": img_h
            })

    return consolidated


def convert_to_yolo_bbox(x_min: float, y_min: float, x_max: float, y_max: float, width: float, height: float) -> Tuple[float, float, float, float]:
    """
    Convert absolute [x_min, y_min, x_max, y_max] to normalized [x_center, y_center, w, h].
    """
    x_min = max(0.0, min(float(x_min), float(width)))
    x_max = max(0.0, min(float(x_max), float(width)))
    y_min = max(0.0, min(float(y_min), float(height)))
    y_max = max(0.0, min(float(y_max), float(height)))

    x_center = ((x_min + x_max) / 2.0) / width
    y_center = ((y_min + y_max) / 2.0) / height
    box_w = (x_max - x_min) / width
    box_h = (y_max - y_min) / height

    # Clamp to [0, 1]
    x_center = max(0.0, min(1.0, x_center))
    y_center = max(0.0, min(1.0, y_center))
    box_w = max(0.0, min(1.0, box_w))
    box_h = max(0.0, min(1.0, box_h))

    return x_center, y_center, box_w, box_h


def copy_or_link_file(src_path: str, dst_path: str, use_symlink: bool = False):
    """
    Link or copy image file to destination path.
    Prioritizes instantaneous hardlinks (0 bytes extra disk),
    then symlinks, then standard copy.
    """
    if os.path.exists(dst_path):
        return
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    try:
        os.link(src_path, dst_path)
        return
    except Exception:
        pass

    if use_symlink:
        try:
            os.symlink(src_path, dst_path)
            return
        except Exception:
            pass

    shutil.copy2(src_path, dst_path)


def prepare_yolo_dataset(
    data_dir: Optional[str] = None,
    output_dir: Optional[str] = None,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    include_negatives: bool = True,
    negative_ratio: float = 0.30,
    iou_merge_threshold: float = 0.5,
    use_symlink: bool = False,
    sample_limit: Optional[int] = None,
    random_seed: int = 42
) -> Dict:
    """
    Filter, merge, and split VinBigData Chest X-ray dataset into YOLO format.
    Main function to process VinBigData CSV and images into standard YOLO structure.
    """
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if data_dir is None:
        data_dir = os.path.join(_root, "vinbigdata")
    if output_dir is None:
        output_dir = os.path.join(_root, "data", "processed")
    logger.info("Starting CliniScan+ YOLO11 dataset preparation...")
    logger.info(f"Source Directory: {data_dir}")
    logger.info(f"Target Directory: {output_dir}")

    train_csv_path = os.path.join(data_dir, "train.csv")
    train_img_dir = os.path.join(data_dir, "train")

    if not os.path.exists(train_csv_path):
        raise FileNotFoundError(f"Missing train.csv at: {train_csv_path}")
    if not os.path.exists(train_img_dir):
        raise FileNotFoundError(f"Missing train images directory at: {train_img_dir}")

    # 1. Load CSV
    df = pd.read_csv(train_csv_path)
    logger.info(f"Loaded {len(df)} total annotation rows for {df['image_id'].nunique()} unique images.")

    # 2. Filter target classes
    target_mask = df["class_name"].isin(TARGET_CLASSES)
    target_df = df[target_mask].copy()
    target_df["target_class_id"] = target_df["class_name"].map(CLASS_TO_ID)

    logger.info(f"Filtered {len(target_df)} annotations across 10 target classes.")
    logger.info(f"Target class distribution:\n{target_df['class_name'].value_counts()}")

    # Positive unique images (having at least 1 target finding)
    positive_images = target_df["image_id"].unique().tolist()
    logger.info(f"Total positive images with target abnormalities: {len(positive_images)}")

    # Negative images (images with 'No finding' only or no target classes)
    all_images = df["image_id"].unique().tolist()
    negative_images = list(set(all_images) - set(positive_images))
    logger.info(f"Total potential background/negative images: {len(negative_images)}")

    # Subsample negatives if requested
    if include_negatives and negative_ratio > 0:
        np.random.seed(random_seed)
        num_negatives = int(len(positive_images) * negative_ratio)
        num_negatives = min(num_negatives, len(negative_images))
        selected_negatives = list(np.random.choice(negative_images, size=num_negatives, replace=False))
        logger.info(f"Selected {len(selected_negatives)} negative/normal images ({negative_ratio*100:.1f}% ratio) to prevent false positives.")
    else:
        selected_negatives = []

    # Selected image pool
    selected_image_ids = positive_images + selected_negatives
    if sample_limit is not None and sample_limit < len(selected_image_ids):
        np.random.seed(random_seed)
        selected_image_ids = list(np.random.choice(selected_image_ids, size=sample_limit, replace=False))
        logger.info(f"Sample limit applied: using {len(selected_image_ids)} images.")

    # 3. Create Train / Val / Test Split by unique Image ID
    np.random.seed(random_seed)
    train_ids, test_val_ids = train_test_split(
        selected_image_ids,
        test_size=(val_ratio + test_ratio),
        random_state=random_seed,
        shuffle=True
    )
    val_prop = val_ratio / (val_ratio + test_ratio)
    val_ids, test_ids = train_test_split(
        test_val_ids,
        test_size=(1.0 - val_prop),
        random_state=random_seed,
        shuffle=True
    )

    split_map = {}
    for img_id in train_ids:
        split_map[img_id] = "train"
    for img_id in val_ids:
        split_map[img_id] = "val"
    for img_id in test_ids:
        split_map[img_id] = "test"

    logger.info(f"Split breakdown: Train: {len(train_ids)} ({len(train_ids)/len(selected_image_ids)*100:.1f}%), "
                f"Val: {len(val_ids)} ({len(val_ids)/len(selected_image_ids)*100:.1f}%), "
                f"Test: {len(test_ids)} ({len(test_ids)/len(selected_image_ids)*100:.1f}%)")

    # 4. Create directories
    for split in ["train", "val", "test"]:
        os.makedirs(os.path.join(output_dir, "images", split), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "labels", split), exist_ok=True)

    # 5. Build annotation index by image_id
    image_annotations: Dict[str, List[Dict]] = {}
    for _, row in target_df.iterrows():
        img_id = row["image_id"]
        if img_id not in split_map:
            continue
        # Check box coordinates
        if pd.isna(row["x_min"]) or pd.isna(row["y_min"]) or pd.isna(row["x_max"]) or pd.isna(row["y_max"]):
            continue
        if row["x_max"] <= row["x_min"] or row["y_max"] <= row["y_min"]:
            continue

        image_annotations.setdefault(img_id, []).append({
            "class_id": int(row["target_class_id"]),
            "class_name": row["class_name"],
            "x_min": float(row["x_min"]),
            "y_min": float(row["y_min"]),
            "x_max": float(row["x_max"]),
            "y_max": float(row["y_max"]),
            "width": float(row["width"]),
            "height": float(row["height"])
        })

    # 6. Process and write images and YOLO label txt files
    stats = {"train_boxes": 0, "val_boxes": 0, "test_boxes": 0, "errors": 0}
    per_class_counts = {split: {name: 0 for name in TARGET_CLASSES} for split in ["train", "val", "test"]}

    logger.info("Writing images and YOLO label files...")
    for img_id in tqdm(selected_image_ids, desc="Processing dataset"):
        split = split_map[img_id]
        src_img_file = os.path.join(train_img_dir, f"{img_id}.jpg")
        if not os.path.exists(src_img_file):
            stats["errors"] += 1
            continue

        dst_img_file = os.path.join(output_dir, "images", split, f"{img_id}.jpg")
        dst_lbl_file = os.path.join(output_dir, "labels", split, f"{img_id}.txt")

        # Copy/link image
        copy_or_link_file(src_img_file, dst_img_file, use_symlink=use_symlink)

        # Process annotations for this image
        raw_boxes = image_annotations.get(img_id, [])
        consolidated = consolidate_boxes(raw_boxes, iou_threshold=iou_merge_threshold)

        label_lines = []
        for box in consolidated:
            xc, yc, w, h = convert_to_yolo_bbox(
                box["x_min"], box["y_min"], box["x_max"], box["y_max"],
                box["width"], box["height"]
            )
            if w > 0.001 and h > 0.001:
                cls_id = box["class_id"]
                label_lines.append(f"{cls_id} {xc:.6f} {yc:.6f} {w:.6f} {h:.6f}\n")
                per_class_counts[split][ID_TO_CLASS[cls_id]] += 1
                stats[f"{split}_boxes"] += 1

        # Write label file (empty file for negatives is standard in YOLO)
        with open(dst_lbl_file, "w") as lf:
            lf.writelines(label_lines)

    # 7. Generate dataset.yaml
    dataset_yaml_path = os.path.join(os.path.dirname(output_dir), "dataset.yaml")
    # Also write inside output_dir for portability
    inner_yaml_path = os.path.join(output_dir, "dataset.yaml")

    yaml_content = f"""# CliniScan+ YOLO11 Dataset Configuration
path: {os.path.abspath(output_dir).replace('\\', '/')}
train: images/train
val: images/val
test: images/test

names:
"""
    for idx, name in enumerate(TARGET_CLASSES):
        yaml_content += f"  {idx}: {name}\n"

    for yp in [dataset_yaml_path, inner_yaml_path]:
        try:
            with open(yp, "w") as yf:
                yf.write(yaml_content)
        except Exception as e:
            logger.warning(f"Could not write yaml to {yp}: {e}")

    logger.info("Dataset preparation complete!")
    logger.info(f"Summary Statistics: {stats}")
    logger.info(f"Dataset YAML generated at: {inner_yaml_path}")

    return {
        "stats": stats,
        "per_class_counts": per_class_counts,
        "splits": {
            "train": len(train_ids),
            "val": len(val_ids),
            "test": len(test_ids)
        },
        "yaml_path": inner_yaml_path
    }


if __name__ == "__main__":
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(description="CliniScan+ VinBigData Dataset Preparation")
    parser.add_argument("--data_dir", type=str, default=os.path.join(_root, "vinbigdata"), help="Path to raw vinbigdata directory")
    parser.add_argument("--output_dir", type=str, default=os.path.join(_root, "data", "processed"), help="Path to output processed dataset")
    parser.add_argument("--train_ratio", type=float, default=0.70, help="Train split ratio")
    parser.add_argument("--val_ratio", type=float, default=0.15, help="Val split ratio")
    parser.add_argument("--test_ratio", type=float, default=0.15, help="Test split ratio")
    parser.add_argument("--no_negatives", action="store_true", help="Exclude background/negative images")
    parser.add_argument("--negative_ratio", type=float, default=0.20, help="Ratio of negative images to include")
    parser.add_argument("--iou_merge", type=float, default=0.5, help="IoU threshold for consensus merging")
    parser.add_argument("--sample_limit", type=int, default=None, help="Optional sample limit for quick debugging")
    parser.add_argument("--symlink", action="store_true", help="Use symlinks instead of copying images")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()
    prepare_yolo_dataset(
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        include_negatives=not args.no_negatives,
        negative_ratio=args.negative_ratio,
        iou_merge_threshold=args.iou_merge,
        use_symlink=args.symlink,
        sample_limit=args.sample_limit,
        random_seed=args.seed
    )
