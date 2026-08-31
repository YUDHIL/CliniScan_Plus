"""
CliniScan+ Inference Service Engine
Provides high-performance, modular chest X-ray abnormality detection,
structured clinical findings generation, and bounding-box rendering.
"""

import os
import sys
import time
import json
import argparse
from typing import Union, List, Dict, Tuple, Optional
import numpy as np
import cv2
from PIL import Image

try:
    import torch
    import torchvision.extension
    import torchvision
except Exception:
    pass

from ultralytics import YOLO

# 10 Target Lung Classes
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

# Clinical severity classification & color palette
SEVERITY_MAPPING = {
    "Pneumothorax": {"severity": "Critical", "color": (220, 20, 60), "urgency": "Immediate radiologist evaluation required"},
    "Pleural effusion": {"severity": "High", "color": (148, 0, 211), "urgency": "Prompt clinical correlation recommended"},
    "Consolidation": {"severity": "High", "color": (0, 206, 209), "urgency": "Evaluate for infectious pneumonia / acute process"},
    "Nodule/Mass": {"severity": "Moderate-High", "color": (255, 69, 0), "urgency": "Follow-up CT or biopsy consideration"},
    "Atelectasis": {"severity": "Moderate", "color": (255, 140, 0), "urgency": "Assess airway clearance / postoperative status"},
    "ILD": {"severity": "Moderate", "color": (30, 144, 255), "urgency": "High-resolution CT (HRCT) consultation recommended"},
    "Pulmonary fibrosis": {"severity": "Moderate", "color": (50, 205, 50), "urgency": "Chronic interstitial evaluation"},
    "Lung Opacity": {"severity": "Moderate", "color": (255, 215, 0), "urgency": "Broad differential; clinical correlation needed"},
    "Infiltration": {"severity": "Moderate", "color": (0, 250, 154), "urgency": "Monitor for infectious / inflammatory progression"},
    "Pleural thickening": {"severity": "Low-Moderate", "color": (255, 105, 180), "urgency": "Chronic pleural assessment"}
}


class CliniScanDetector:
    """
    CliniScan+ AI Abnormality Detector powered by Ultralytics YOLO11.
    """
    def __init__(
        self,
        model_path: Optional[str] = None,
        fallback_model: str = "yolo11n.pt",
        device: str = "auto",
        model_version: str = "CliniScan-YOLO11-v1"
    ):
        self.model_version = model_version
        if model_path is None:
            self.model_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "models",
                "cliniscan_yolo11n_best.pt"
            )
        else:
            self.model_path = model_path
        
        # Select device
        if device == "auto":
            self.device = "0" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        # Load weights with fallback
        if os.path.exists(model_path):
            print(f"[CliniScanDetector] Loading trained weights from: {model_path}")
            self.model = YOLO(model_path)
        else:
            print(f"[CliniScanDetector] Trained model '{model_path}' not found. Initializing base: {fallback_model}")
            self.model = YOLO(fallback_model)

        # Warm up model to initialize CUDA & torchvision C-extensions in main thread
        try:
            dummy_img = np.zeros((640, 640, 3), dtype=np.uint8)
            self.model.predict(dummy_img, imgsz=640, device=self.device, verbose=False)
        except Exception as e:
            pass

    def predict(
        self,
        image_input: Union[str, np.ndarray, Image.Image],
        conf_threshold: float = 0.25,
        iou_threshold: float = 0.45,
        img_size: int = 640
    ) -> Dict:
        """
        Run inference on chest X-ray image and return structured clinical findings.
        """
        start_time = time.time()

        # Preprocess input image to standard numpy BGR format
        if isinstance(image_input, str):
            if not os.path.exists(image_input):
                raise FileNotFoundError(f"Image file not found: {image_input}")
            img_bgr = cv2.imread(image_input)
            source_name = os.path.basename(image_input)
        elif isinstance(image_input, Image.Image):
            img_rgb = np.array(image_input)
            img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
            source_name = "uploaded_image"
        elif isinstance(image_input, np.ndarray):
            if len(image_input.shape) == 2:  # Grayscale
                img_bgr = cv2.cvtColor(image_input, cv2.COLOR_GRAY2BGR)
            elif image_input.shape[2] == 4:  # RGBA
                img_bgr = cv2.cvtColor(image_input, cv2.COLOR_RGBA2BGR)
            else:
                img_bgr = image_input.copy()
            source_name = "array_input"
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

        orig_h, orig_w = img_bgr.shape[:2]

        # Execute YOLO prediction
        results = self.model.predict(
            source=img_bgr,
            conf=conf_threshold,
            iou=iou_threshold,
            imgsz=img_size,
            device=self.device,
            verbose=False
        )

        detections = []
        annotated_bgr = img_bgr.copy()

        if len(results) > 0 and results[0].boxes is not None:
            boxes = results[0].boxes
            for i in range(len(boxes)):
                box = boxes[i]
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                xyxy = box.xyxy[0].cpu().numpy()

                x1, y1, x2, y2 = int(xyxy[0]), int(xyxy[1]), int(xyxy[2]), int(xyxy[3])
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(orig_w - 1, x2), min(orig_h - 1, y2)

                # Normalized coordinates
                xc = ((x1 + x2) / 2.0) / orig_w
                yc = ((y1 + y2) / 2.0) / orig_h
                w = (x2 - x1) / orig_w
                h = (y2 - y1) / orig_h

                cls_name = TARGET_CLASSES[cls_id] if cls_id < len(TARGET_CLASSES) else f"Class_{cls_id}"
                meta = SEVERITY_MAPPING.get(cls_name, {"severity": "Moderate", "color": (0, 255, 0), "urgency": "Review needed"})

                # Determine anatomical quadrant / zone
                lat = "Right" if xc < 0.5 else "Left"
                zone = "Upper Zone" if yc < 0.33 else ("Mid Zone" if yc < 0.66 else "Lower Zone / Base")
                anatomical_location = f"{lat} Hemithorax ({zone})"

                detection_entry = {
                    "detection_id": i + 1,
                    "class_id": cls_id,
                    "class_name": cls_name,
                    "confidence": round(conf, 4),
                    "confidence_pct": f"{conf * 100:.1f}%",
                    "bbox_pixels": [x1, y1, x2, y2],
                    "bbox_normalized": [round(xc, 4), round(yc, 4), round(w, 4), round(h, 4)],
                    "location": anatomical_location,
                    "severity": meta["severity"],
                    "clinical_urgency": meta["urgency"]
                }
                detections.append(detection_entry)

                # Draw on annotated image
                box_color = meta["color"]
                cv2.rectangle(annotated_bgr, (x1, y1), (x2, y2), box_color, 3)

                label_text = f"{cls_name} {conf*100:.1f}%"
                font_scale = max(0.5, min(1.0, orig_w / 1400.0))
                thickness = max(1, int(orig_w / 1000.0))
                (text_w, text_h), _ = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness)
                tag_y = max(0, y1 - text_h - 10)
                cv2.rectangle(annotated_bgr, (x1, tag_y), (x1 + text_w + 8, y1), box_color, -1)
                cv2.putText(annotated_bgr, label_text, (x1 + 4, y1 - 4), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)

        inference_time_ms = round((time.time() - start_time) * 1000, 2)
        annotated_rgb = cv2.cvtColor(annotated_bgr, cv2.COLOR_BGR2RGB)

        output = {
            "model_version": self.model_version,
            "source_image": source_name,
            "image_dimensions": {"width": orig_w, "height": orig_h},
            "findings_count": len(detections),
            "detections": detections,
            "inference_time_ms": inference_time_ms,
            "conf_threshold_used": conf_threshold,
            "iou_threshold_used": iou_threshold,
            "device_used": self.device,
            "status": "Abnormalities Detected" if len(detections) > 0 else "No Target Findings Detected",
            "annotated_image_rgb": annotated_rgb
        }

        return output


if __name__ == "__main__":
    _proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parser = argparse.ArgumentParser(description="CliniScan+ X-ray Inference Engine")
    parser.add_argument("--image", type=str, required=True, help="Path to input chest X-ray image")
    parser.add_argument("--model", type=str, default=os.path.join(_proj_root, "models", "cliniscan_yolo11n_best.pt"), help="Path to YOLO11 model")
    parser.add_argument("--conf", type=float, default=0.25, help="Confidence threshold")
    parser.add_argument("--iou", type=float, default=0.45, help="IoU threshold")
    parser.add_argument("--output", type=str, default=os.path.join(_proj_root, "results", "predictions", "result.jpg"), help="Output annotated image path")
    args = parser.parse_args()

    detector = CliniScanDetector(model_path=args.model)
    res = detector.predict(args.image, conf_threshold=args.conf, iou_threshold=args.iou)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    out_bgr = cv2.cvtColor(res["annotated_image_rgb"], cv2.COLOR_RGB2BGR)
    cv2.imwrite(args.output, out_bgr)

    # Print summary
    print(json.dumps({k: v for k, v in res.items() if k != "annotated_image_rgb"}, indent=2))
    print(f"\nAnnotated visualization saved to: {args.output}")
