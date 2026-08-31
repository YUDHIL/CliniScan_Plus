# 🫁 CliniScan+ : AI-Assisted Chest X-ray Lung Abnormality Detection

> **CliniScan+** is a production-grade, AI-assisted chest X-ray abnormality detection and clinical decision support platform. Powered by **Ultralytics YOLO11** trained on the **VinBigData Chest X-ray Dataset**, CliniScan+ detects and localizes 10 targeted pulmonary and pleural pathologies with bounding-box precision, structured radiologist reports, and a multi-page interactive clinical dashboard.

---

## 🎯 1. Supported 10 Target Conditions

CliniScan+ focuses on 10 localized and diffuse lung parenchymal and pleural abnormalities:

| ID | Pathology Class | Clinical Description | Priority / Severity |
|:---:|:---|:---|:---:|
| **0** | **Atelectasis** | Partial or complete collapse of lung segments | Moderate |
| **1** | **ILD** | Interstitial Lung Disease; diffuse parenchymal scarring | Moderate |
| **2** | **Pulmonary fibrosis** | Chronic, irreversible lung tissue scarring | Moderate |
| **3** | **Pneumothorax** | Air leakage into pleural space causing lung collapse | **Critical (Emergency)** |
| **4** | **Pleural effusion** | Pathological fluid accumulation in pleural space | **High** |
| **5** | **Pleural thickening** | Fibrotic thickening of the pleural membrane | Low-Moderate |
| **6** | **Consolidation** | Alveolar filling with exudate/pus (infectious/pneumonic) | **High** |
| **7** | **Lung Opacity** | Non-specific parenchymal density increase | Moderate |
| **8** | **Nodule/Mass** | Focal pulmonary lesions (<3cm nodule, >3cm mass) | Moderate-High |
| **9** | **Infiltration** | Ill-defined parenchymal density infiltration | Moderate |

---

## 🏗️ 2. System Architecture

```text
                                  Chest X-ray (DICOM / JPEG / PNG)
                                                │
                                                ▼
                            +───────────────────────────────────────+
                            │   Image Preprocessing & Resizing      │
                            │   - Aspect ratio preservation (640px) │
                            │   - Contrast & grayscale stability    │
                            +───────────────────────────────────────+
                                                │
                                                ▼
                            +───────────────────────────────────────+
                            │       Ultralytics YOLO11 Engine       │
                            │   - Feature Pyramid & C3k2 Backbone   │
                            │   - Anchor-free Detection Head        │
                            +───────────────────────────────────────+
                                                │
                     ┌──────────────────────────┴──────────────────────────┐
                     ▼                                                     ▼
        Bounding Box Localizations                             Class Probability & Urgency
      (Normalized / Pixel Coordinates)                         (Confidence % & Severity)
                     │                                                     │
                     └──────────────────────────┬──────────────────────────┘
                                                │
                                                ▼
                            +───────────────────────────────────────+
                            │       Structured Clinical Findings    │
                            │   - Anatomical quadrant mapping       │
                            │   - Clinical recommendation notes     │
                            +───────────────────────────────────────+
                                                │
                     ┌──────────────────────────┼──────────────────────────┐
                     ▼                          ▼                          ▼
         Interactive Web UI            Doctor Review Queue        Audited Report Storage
        (Streamlit Dashboard)        (Attestation & Feedback)      (MongoDB / Local JSON)
```

---

## 📂 3. Project Structure

```text
d:\main pr\
├── data/
│   ├── processed/                        # YOLO-formatted dataset
│   │   ├── images/ (train, val, test)    # 70% / 15% / 15% split
│   │   └── labels/ (train, val, test)    # Normalized YOLO .txt annotations
│   └── cliniscan_db_backup.json          # Local persistence fallback
├── notebooks/
│   ├── 01_dataset_analysis.ipynb         # EDA, class balance, aspect ratios
│   ├── 02_annotation_validation.ipynb    # Visual bbox checks & overlay sanity
│   └── 03_model_evaluation.ipynb         # PR curves, confusion matrices, error analysis
├── src/
│   ├── __init__.py
│   ├── prepare_dataset.py                # Dataset filtering, conversion & split
│   ├── validate_dataset.py               # QA checks, box normalization verification
│   ├── train.py                          # YOLO11 training script with medical augmentations
│   ├── evaluate.py                       # Evaluation metrics & per-class reporting
│   ├── inference.py                      # Standalone InferenceEngine API
│   └── database.py                       # MongoDB client with mongomock fallback
├── models/                               # Saved model weights
├── results/
│   ├── validation_samples/               # Visual QA overlay images
│   ├── training/                         # Training curves and logs
│   ├── evaluation/                       # Confusion matrices & PR plots
│   └── predictions/                      # Inference sample predictions
├── app/
│   ├── __init__.py
│   ├── streamlit_app.py                  # Streamlit clinical dashboard
│   ├── components.py                     # UI cards, badges, printable HTML generator
│   └── styles.css                        # Modern medical styling
├── dataset.yaml                          # YOLO11 dataset configuration
├── requirements.txt                      # Project dependencies
└── README.md                             # Documentation & research guide
```

---

## 🚀 4. Getting Started

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Prepare & Validate Dataset
```bash
# 1. Filter 10 classes and generate YOLO splits (70/15/15)
python src/prepare_dataset.py

# 2. Run Quality Assurance checks & render 50 visual overlays
python src/validate_dataset.py --num_samples 50
```

### Step 3: Train YOLO11 Model
```bash
# Train YOLO11 baseline
python src/train.py --model yolo11n.pt --epochs 50 --batch 16 --imgsz 640
```

### Step 4: Evaluate Model Performance
```bash
# Run validation evaluation
python src/evaluate.py --model models/cliniscan_yolo11n_best.pt --split val
```

### Step 5: Test Standalone Inference
```bash
python src/inference.py --image "vinbigdata/train/0005e8e3701dfb1dd93d53e2ff537b6e.jpg" --conf 0.20
```

### Step 6: Launch the CliniScan+ Clinical Dashboard
```bash
streamlit run app/streamlit_app.py
```

---

## 🖥️ 5. Streamlit Application Modules

1. **🏠 Home & Overview**: System purpose, 10 supported pathologies, and clinical disclaimer.
2. **🔍 X-ray Analysis**: Interactive radiograph upload/sample selector, real-time confidence sliders, side-by-side radiograph comparisons, and localized finding cards.
3. **📄 Patient Clinical Report**: Comprehensive diagnostic report compilation, printable HTML generator, and PDF export.
4. **👨‍⚕️ Doctor Review Dashboard**: Triage queue, AI confirmation/rejection workflow, and physician recommendations.
5. **📊 Model & Research Insights**: Dataset distribution, per-class mAP tables, confusion matrices, and error analysis suitable for IEEE publication.

---

## ⚠️ 6. Medical Decision Support Disclaimer
CliniScan+ is designed strictly for investigational, educational, and clinical decision support purposes. It is not an autonomous diagnostic device. All AI-generated findings must be independently verified by a licensed radiologist or medical professional prior to clinical intervention.
