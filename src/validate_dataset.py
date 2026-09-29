"""
CliniScan+ Dataset Validation and Quality Assurance Pipeline
Validates YOLO annotations, detects bounding-box anomalies,
and renders visual quality-control overlays on X-ray images.
"""

import os
import glob
import json
import argparse
import random
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
from tqdm import tqdm

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

# Distinct color palette for 10 classes (BGR format for OpenCV)
CLASS_COLORS = [
    (255, 99, 71),    # Tomato / Red-Orange - Atelectasis
    (30, 144, 255),   # Dodger Blue - ILD
    (50, 205, 50),    # Lime Green - Pulmonary fibrosis
    (255, 215, 0),    # Gold - Pneumothorax
    (148, 0, 211),    # Dark Violet - Pleural effusion
    (255, 105, 180),  # Hot Pink - Pleural thickening
    (0, 206, 209),    # Dark Turquoise - Consolidation
    (255, 140, 0),    # Dark Orange - Lung Opacity
    (220, 20, 60),    # Crimson - Nodule/Mass
    (0, 250, 154),    # Medium Spring Green - Infiltration
]


def draw_yolo_boxes_on_image(image_path: str, label_path: str, output_path: str):
    """
    Renders bounding boxes and labeled tags on the X-ray image.
    """
    img = cv2.imread(image_path)
    if img is None:
        return False

    h, w = img.shape[:2]
    if not os.path.exists(label_path):
        cv2.imwrite(output_path, img)
        return True

    with open(label_path, "r") as lf:
        lines = [line.strip() for line in lf.readlines() if line.strip()]

    for line in lines:
        parts = line.split()
        if len(parts) != 5:
            continue
        cls_id, xc, yc, bw, bh = int(parts[0]), float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
        if cls_id < 0 or cls_id >= len(TARGET_CLASSES):
            continue

        # Convert normalized to pixel coords
        xmin = int((xc - bw / 2.0) * w)
        ymin = int((yc - bh / 2.0) * h)
        xmax = int((xc + bw / 2.0) * w)
        ymax = int((yc + bh / 2.0) * h)

        xmin, ymin = max(0, xmin), max(0, ymin)
        xmax, ymax = min(w - 1, xmax), min(h - 1, ymax)

        color = CLASS_COLORS[cls_id % len(CLASS_COLORS)]
        class_name = TARGET_CLASSES[cls_id]

        # Draw bounding box
        cv2.rectangle(img, (xmin, ymin), (xmax, ymax), color, 3)

        # Label background banner
        label_text = f"{class_name}"
        font_scale = max(0.5, min(1.0, w / 1500.0))
        thickness = max(1, int(w / 1000.0))
        (text_w, text_h), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
        
        tag_ymin = max(0, ymin - text_h - 10)
        cv2.rectangle(img, (xmin, tag_ymin), (xmin + text_w + 10, ymin), color, -1)
        cv2.putText(img, label_text, (xmin + 5, ymin - 5), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cv2.imwrite(output_path, img)
    return True


def validate_yolo_dataset(
    processed_dir: Optional[str] = None,
    output_samples_dir: Optional[str] = None,
    num_samples_to_render: int = 100,
    random_seed: int = 42
) -> Dict:
    """
    Validates dataset integrity across train/val/test splits.
    """
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if processed_dir is None:
        processed_dir = os.path.join(_root, "data", "processed")
    if output_samples_dir is None:
        output_samples_dir = os.path.join(_root, "results", "validation_samples")
    print(f"Validating processed YOLO dataset at: {processed_dir}")
    os.makedirs(output_samples_dir, exist_ok=True)

    report = {
        "splits": {},
        "overall": {
            "total_images": 0,
            "total_annotations": 0,
            "negative_images": 0,
            "corrupted_images": 0,
            "invalid_boxes": 0,
            "out_of_bounds_boxes": 0,
            "class_counts": {cls: 0 for cls in TARGET_CLASSES}
        }
    }

    all_annotated_samples = []

    for split in ["train", "val", "test"]:
        img_dir = os.path.join(processed_dir, "images", split)
        lbl_dir = os.path.join(processed_dir, "labels", split)

        if not os.path.exists(img_dir) or not os.path.exists(lbl_dir):
            print(f"Warning: Split {split} directory does not exist.")
            continue

        images = glob.glob(os.path.join(img_dir, "*.jpg"))
        labels = glob.glob(os.path.join(lbl_dir, "*.txt"))

        split_stats = {
            "images": len(images),
            "labels": len(labels),
            "annotations": 0,
            "negatives": 0,
            "class_counts": {cls: 0 for cls in TARGET_CLASSES}
        }

        for img_path in tqdm(images, desc=f"Validating {split}"):
            img_name = os.path.basename(img_path)
            base_id = os.path.splitext(img_name)[0]
            lbl_path = os.path.join(lbl_dir, f"{base_id}.txt")

            # Check if image can be opened
            if not os.path.exists(lbl_path):
                report["overall"]["negative_images"] += 1
                split_stats["negatives"] += 1
                continue

            with open(lbl_path, "r") as lf:
                lines = [l.strip() for l in lf.readlines() if l.strip()]

            if not lines:
                report["overall"]["negative_images"] += 1
                split_stats["negatives"] += 1
            else:
                all_annotated_samples.append((img_path, lbl_path, split))

            for line in lines:
                parts = line.split()
                if len(parts) != 5:
                    report["overall"]["invalid_boxes"] += 1
                    continue

                try:
                    cls_id = int(parts[0])
                    xc, yc, bw, bh = float(parts[1]), float(parts[2]), float(parts[3]), float(parts[4])
                except ValueError:
                    report["overall"]["invalid_boxes"] += 1
                    continue

                if cls_id < 0 or cls_id >= len(TARGET_CLASSES):
                    report["overall"]["invalid_boxes"] += 1
                    continue

                if xc < 0.0 or xc > 1.0 or yc < 0.0 or yc > 1.0 or bw <= 0.0 or bw > 1.0 or bh <= 0.0 or bh > 1.0:
                    report["overall"]["out_of_bounds_boxes"] += 1

                cls_name = TARGET_CLASSES[cls_id]
                split_stats["class_counts"][cls_name] += 1
                report["overall"]["class_counts"][cls_name] += 1
                split_stats["annotations"] += 1
                report["overall"]["total_annotations"] += 1

        report["overall"]["total_images"] += len(images)
        report["splits"][split] = split_stats

    # Render Sample Overlays for Visual QA
    random.seed(random_seed)
    selected_for_vis = random.sample(all_annotated_samples, min(num_samples_to_render, len(all_annotated_samples)))
    print(f"Generating {len(selected_for_vis)} QA visual overlays in {output_samples_dir}...")

    for img_path, lbl_path, split in tqdm(selected_for_vis, desc="Rendering QA overlays"):
        base_name = os.path.basename(img_path)
        out_path = os.path.join(output_samples_dir, f"{split}_{base_name}")
        draw_yolo_boxes_on_image(img_path, lbl_path, out_path)

    # Save JSON report
    report_json_path = os.path.join(os.path.dirname(output_samples_dir), "dataset_validation_report.json")
    with open(report_json_path, "w") as jf:
        json.dump(report, jf, indent=2)

    print(f"\n================ DATASET VALIDATION REPORT ================")
    print(f"Total Processed Images: {report['overall']['total_images']}")
    print(f"Total Target Annotations: {report['overall']['total_annotations']}")
    print(f"Negative / Background Images: {report['overall']['negative_images']}")
    print(f"Invalid / Malformed Boxes: {report['overall']['invalid_boxes']}")
    print(f"Out of Bounds Boxes: {report['overall']['out_of_bounds_boxes']}")
    print("Class Distribution:")
    for cls_name, count in report['overall']['class_counts'].items():
        print(f"  - {cls_name:22s}: {count:5d} annotations")
    print(f"===========================================================\n")
    print(f"Report saved to: {report_json_path}")
    print(f"Visual overlays saved to: {output_samples_dir}")

    return report


if __name__ == "__main__":
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(description="CliniScan+ Dataset Validation and Visual QA")
    parser.add_argument("--processed_dir", type=str, default=os.path.join(_root, "data", "processed"), help="Processed dataset directory")
    parser.add_argument("--samples_dir", type=str, default=os.path.join(_root, "results", "validation_samples"), help="Output directory for visual QA samples")
    parser.add_argument("--num_samples", type=int, default=100, help="Number of visual QA overlays to generate")
    args = parser.parse_args()

    validate_yolo_dataset(
        processed_dir=args.processed_dir,
        output_samples_dir=args.samples_dir,
        num_samples_to_render=args.num_samples
    )
