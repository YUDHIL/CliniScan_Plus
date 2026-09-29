"""
CliniScan+ YOLO11 Training Pipeline
Trains Ultralytics YOLO11 model on VinBigData chest X-rays
with medical-safe augmentations and automatic model checkpointing.
"""

import os
import shutil
import json
import argparse
import logging
import torch
from typing import Optional
from ultralytics import YOLO

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def train_cliniscan_yolo11(
    data_yaml: Optional[str] = None,
    model_variant: str = "yolo11n.pt",
    epochs: int = 50,
    batch_size: int = 16,
    img_size: int = 640,
    device: str = "auto",
    project_dir: Optional[str] = None,
    experiment_name: str = "cliniscan_yolo11n",
    models_dir: Optional[str] = None,
    lr0: float = 0.01,
    patience: int = 15,
    workers: int = 4
):
    """
    Train YOLO11 model with medical X-ray optimized parameters.
    """
    _proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if data_yaml is None:
        data_yaml = os.path.join(_proj_root, "dataset.yaml")
    if project_dir is None:
        project_dir = os.path.join(_proj_root, "results", "training")
    if models_dir is None:
        models_dir = os.path.join(_proj_root, "models")
    """
    Train YOLO11 model with medical X-ray optimized parameters.
    """
    logger.info("Initializing CliniScan+ YOLO11 Training Pipeline...")
    os.makedirs(project_dir, exist_ok=True)
    os.makedirs(models_dir, exist_ok=True)

    # Device selection
    if device == "auto":
        device = "0" if torch.cuda.is_available() else "cpu"
    logger.info(f"Target Device: {device} (CUDA available: {torch.cuda.is_available()})")

    # Load base model
    logger.info(f"Loading base architecture: {model_variant}")
    model = YOLO(model_variant)

    # Medical-safe augmentation hyper-parameters
    # Avoid aggressive warping/mixup that would distort lung anatomy
    train_args = dict(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=img_size,
        device=device,
        project=project_dir,
        name=experiment_name,
        exist_ok=True,
        patience=patience,
        save=True,
        save_period=5,
        workers=workers,
        lr0=lr0,
        lrf=0.01,
        warmup_epochs=3.0,
        # Medical augmentations
        degrees=5.0,        # subtle rotation (+/- 5 deg)
        translate=0.05,     # subtle translation (+/- 5%)
        scale=0.1,          # subtle zoom (+/- 10%)
        fliplr=0.5,         # horizontal flip
        flipud=0.0,         # no vertical flip for chest X-ray
        mosaic=0.0,         # disable mosaic for clean anatomical structure
        mixup=0.0,          # disable mixup
        hsv_h=0.0,          # grayscale stability
        hsv_s=0.0,
        hsv_v=0.15,         # mild contrast/brightness variation
        val=True,
        plots=True,
        verbose=True
    )

    logger.info(f"Starting training for {epochs} epochs on {data_yaml}...")
    results = model.train(**train_args)

    # Export best model
    exp_dir = os.path.join(project_dir, experiment_name)
    best_weights = os.path.join(exp_dir, "weights", "best.pt")
    last_weights = os.path.join(exp_dir, "weights", "last.pt")

    target_best_weights = os.path.join(models_dir, f"{experiment_name}_best.pt")
    target_last_weights = os.path.join(models_dir, f"{experiment_name}_last.pt")

    if os.path.exists(best_weights):
        shutil.copy2(best_weights, target_best_weights)
        logger.info(f"Successfully copied best weights to: {target_best_weights}")
    elif os.path.exists(last_weights):
        shutil.copy2(last_weights, target_best_weights)
        logger.info(f"Copied last weights to: {target_best_weights}")

    # Summary record
    summary_path = os.path.join(exp_dir, "training_summary.json")
    summary_data = {
        "model_variant": model_variant,
        "epochs": epochs,
        "batch_size": batch_size,
        "img_size": img_size,
        "device": str(device),
        "best_weights_path": target_best_weights,
        "experiment_dir": exp_dir
    }
    with open(summary_path, "w") as sf:
        json.dump(summary_data, sf, indent=2)

    logger.info("Training pipeline finished successfully.")
    return results, target_best_weights


if __name__ == "__main__":
    _root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(description="CliniScan+ YOLO11 Training")
    parser.add_argument("--data", type=str, default=os.path.join(_root, "dataset.yaml"), help="Path to dataset.yaml")
    parser.add_argument("--model", type=str, default="yolo11n.pt", help="YOLO11 model variant (yolo11n.pt, yolo11s.pt, yolo11m.pt)")
    parser.add_argument("--epochs", type=int, default=50, help="Number of training epochs")
    parser.add_argument("--batch", type=int, default=16, help="Batch size")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size")
    parser.add_argument("--device", type=str, default="auto", help="Device (cpu, 0, auto)")
    parser.add_argument("--project", type=str, default=os.path.join(_root, "results", "training"), help="Training logs project directory")
    parser.add_argument("--name", type=str, default="cliniscan_yolo11n", help="Experiment name")
    parser.add_argument("--models_dir", type=str, default=os.path.join(_root, "models"), help="Destination directory for model weights")
    parser.add_argument("--lr", type=float, default=0.01, help="Initial learning rate")
    parser.add_argument("--patience", type=int, default=15, help="Early stopping patience")
    parser.add_argument("--workers", type=int, default=4, help="Data loader workers")

    args = parser.parse_args()
    train_cliniscan_yolo11(
        data_yaml=args.data,
        model_variant=args.model,
        epochs=args.epochs,
        batch_size=args.batch,
        img_size=args.imgsz,
        device=args.device,
        project_dir=args.project,
        experiment_name=args.name,
        models_dir=args.models_dir,
        lr0=args.lr,
        patience=args.patience,
        workers=args.workers
    )
