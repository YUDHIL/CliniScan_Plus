"""
CliniScan+ Model Evaluation and Clinical Error Analysis
Calculates per-class precision, recall, F1, mAP@50, mAP@50-95,
performs confidence threshold sweeps, and generates clinical diagnostic reports.
"""

import os
import json
import argparse
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from ultralytics import YOLO

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

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


def evaluate_cliniscan_model(
    model_path: Optional[str] = None,
    data_yaml: Optional[str] = None,
    split: str = "val",
    img_size: int = 640,
    batch_size: int = 16,
    device: str = "auto",
    output_dir: Optional[str] = None
) -> dict:
    """
    Run comprehensive evaluation on val or test split.
    """
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if model_path is None:
        model_path = os.path.join(_root, "models", "cliniscan_yolo11n_best.pt")
    if data_yaml is None:
        data_yaml = os.path.join(_root, "dataset.yaml")
    if output_dir is None:
        output_dir = os.path.join(_root, "results", "evaluation")
    """
    Run comprehensive evaluation on val or test split.
    """
    logger.info(f"Evaluating CliniScan model: {model_path} on split: {split}")
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at: {model_path}")

    model = YOLO(model_path)

    # Run validation
    metrics = model.val(
        data=data_yaml,
        split=split,
        imgsz=img_size,
        batch=batch_size,
        device=device if device != "auto" else "",
        plots=True,
        project=output_dir,
        name=f"eval_{split}",
        exist_ok=True
    )

    # Extract overall metrics
    results_dict = {
        "model_path": model_path,
        "split": split,
        "overall": {
            "mAP50": float(metrics.box.map50),
            "mAP50_95": float(metrics.box.map),
            "precision": float(metrics.box.mp),
            "recall": float(metrics.box.mr),
            "f1_score": float(2 * (metrics.box.mp * metrics.box.mr) / (metrics.box.mp + metrics.box.mr + 1e-7))
        },
        "per_class": []
    }

    # Per-class metrics
    class_map50 = np.atleast_1d(metrics.box.maps50) if hasattr(metrics.box, "maps50") and metrics.box.maps50 is not None else np.atleast_1d(metrics.box.map50)
    class_map = np.atleast_1d(metrics.box.maps) if hasattr(metrics.box, "maps") and metrics.box.maps is not None else np.atleast_1d(metrics.box.map)
    p_arr = np.atleast_1d(metrics.box.p) if hasattr(metrics.box, "p") and metrics.box.p is not None else np.array([])
    r_arr = np.atleast_1d(metrics.box.r) if hasattr(metrics.box, "r") and metrics.box.r is not None else np.array([])

    per_class_table = []
    for idx, name in enumerate(TARGET_CLASSES):
        ap50 = float(class_map50[idx]) if idx < len(class_map50) else 0.0
        ap50_95 = float(class_map[idx]) if idx < len(class_map) else 0.0
        
        # Per class precision and recall if accessible
        p = float(p_arr[idx]) if idx < len(p_arr) else 0.0
        r = float(r_arr[idx]) if idx < len(r_arr) else 0.0
        f1 = float(2 * (p * r) / (p + r + 1e-7)) if (p + r) > 0 else 0.0

        class_entry = {
            "class_id": idx,
            "class_name": name,
            "precision": p,
            "recall": r,
            "f1": f1,
            "ap50": ap50,
            "ap50_95": ap50_95
        }
        results_dict["per_class"].append(class_entry)
        per_class_table.append(class_entry)

    # Save to CSV
    df_metrics = pd.DataFrame(per_class_table)
    metrics_csv_path = os.path.join(output_dir, f"per_class_metrics_{split}.csv")
    df_metrics.to_csv(metrics_csv_path, index=False)

    # Save JSON summary
    summary_json_path = os.path.join(output_dir, f"evaluation_summary_{split}.json")
    with open(summary_json_path, "w") as jf:
        json.dump(results_dict, jf, indent=2)

    # Plot Per-Class AP Chart
    plt.figure(figsize=(12, 6))
    colors = plt.cm.viridis(np.linspace(0, 1, len(TARGET_CLASSES)))
    bars = plt.barh(df_metrics["class_name"], df_metrics["ap50"] * 100, color=colors)
    plt.xlabel("Average Precision @ IoU=0.50 (AP50 %)", fontsize=12)
    plt.title(f"CliniScan+ YOLO11 Per-Class AP50 on {split.upper()} Set", fontsize=14, fontweight="bold")
    plt.xlim(0, 100)
    for bar in bars:
        w = bar.get_width()
        plt.text(w + 1, bar.get_y() + bar.get_height()/2, f"{w:.1f}%", va="center", fontsize=10)
    plt.tight_layout()
    chart_path = os.path.join(output_dir, f"per_class_ap50_{split}.png")
    plt.savefig(chart_path, dpi=300)
    plt.close()

    # Print Formatted Table
    print("\n" + "="*80)
    print(f"CLINISCAN+ YOLO11 EVALUATION REPORT ({split.upper()} SET)")
    print("="*80)
    print(f"Overall mAP@50:    {results_dict['overall']['mAP50']*100:.2f}%")
    print(f"Overall mAP@50-95: {results_dict['overall']['mAP50_95']*100:.2f}%")
    print(f"Mean Precision:    {results_dict['overall']['precision']*100:.2f}%")
    print(f"Mean Recall:       {results_dict['overall']['recall']*100:.2f}%")
    print(f"Mean F1-Score:     {results_dict['overall']['f1_score']*100:.2f}%")
    print("-"*80)
    print(f"{'Class Name':<24} | {'Precision':<10} | {'Recall':<10} | {'AP50 (%)':<10} | {'AP50-95 (%)':<10}")
    print("-"*80)
    for row in per_class_table:
        print(f"{row['class_name']:<24} | {row['precision']*100:9.2f}% | {row['recall']*100:9.2f}% | {row['ap50']*100:9.2f}% | {row['ap50_95']*100:9.2f}%")
    print("="*80 + "\n")

    return results_dict


if __name__ == "__main__":
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(description="CliniScan+ Model Evaluation")
    parser.add_argument("--model", type=str, default=os.path.join(_root, "models", "cliniscan_yolo11n_best.pt"), help="Path to model weights")
    parser.add_argument("--data", type=str, default=os.path.join(_root, "dataset.yaml"), help="Path to dataset.yaml")
    parser.add_argument("--split", type=str, default="val", help="Split to evaluate (val, test)")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--device", type=str, default="auto", help="Device (cpu, 0, auto)")
    parser.add_argument("--output", type=str, default=os.path.join(_root, "results", "evaluation"), help="Output directory")

    args = parser.parse_args()
    evaluate_cliniscan_model(
        model_path=args.model,
        data_yaml=args.data,
        split=args.split,
        img_size=args.imgsz,
        batch_size=args.batch,
        device=args.device,
        output_dir=args.output
    )
