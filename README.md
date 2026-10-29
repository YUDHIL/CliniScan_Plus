# 🫁 CliniScan+ : AI-Assisted Chest X-ray Lung Abnormality Detection

> **CliniScan+** is a production-grade, AI-assisted chest X-ray abnormality detection and clinical decision support platform. Powered by **Ultralytics YOLO11** trained on the **VinBigData Chest X-ray Dataset**, CliniScan+ detects and localizes 10 targeted pulmonary and pleural pathologies with bounding-box precision, structured radiologist reports, and a multi-page interactive clinical dashboard.

---

## 📋 Academic Project Deliverables (Phase - II)

**Institution**: Rajiv Gandhi Institute of Technology | **Department**: Computer Science & Engineering  
**Project Group**: Group 3 (BCS786) | **Project Guide**: Dr. Latha P H  
**Team Members**: Rishika (1RG23CS053), Vedashree (1RG23CS079), Yudhil Krishna (1RG22CS092), Shiva Kumar (1RG23CS064)

Quick access to project documents in the [`docs/`](docs/) repository:

| Document | File Link & Path | Description |
| :--- | :--- | :--- |
| 📄 **Project Report** | [docs/project_report.pdf](docs/project_report.pdf) | Final Phase-II Comprehensive Project Report |
| 📄 **Published Paper** | [docs/published_paper.pdf](docs/published_paper.pdf) | Published Research Paper |
| 📄 **Project Synopsis** | [docs/synopsis.pdf](docs/synopsis.pdf) | Approved Phase-II Project Synopsis |
| 📜 **Certificates** | • [IRE Certificate](docs/Certificates/IRE_Certificate.pdf)<br>• [Acceptance Letter](docs/Certificates/Acceptance_letter.pdf) | Paper Presentation & Acceptance Credentials |
| 📚 **Base Papers** | • [AI Interpretability & Grad-CAM](docs/base_papers/Enhancing_Pneumonia_Diagnosis_Through_AI_Interpretability_Comparative_Analysis_of_Pixel-Level_Interpretability_and_Grad-CAM_on_X-ray_Imaging_With_VGG19.pdf)<br>• [AI-Driven Deep Learning Framework](docs/base_papers/Revolutionizing_Pneumonia_Diagnosis_AI-Driven_Deep_Learning_Framework_for_Automated_Detection_From_Chest_X-Rays.pdf) | Reference Literature & Foundational Benchmarks |

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
                           Interactive Web UI            Doctor Review Queue        Audited Report Storage
        (Next.js 14 Frontend)        (Attestation & Feedback)      (MongoDB / Local JSON)
```

---

## 📂 3. Project Structure

```text
d:\CliniScan+\
├── docs/                                 # Academic deliverables (Report, Synopsis, Papers, Certificates)
├── frontend/                             # Next.js 14 React + Tailwind web app
│   ├── src/
│   │   ├── app/                          # App router layouts & pages
│   │   ├── components/                   # Modular clinical UI components
│   │   ├── lib/api.ts                    # Backend REST API client
│   │   └── types/                        # TypeScript interfaces
│   └── package.json                      # Frontend dependencies
├── src/
│   ├── __init__.py
│   ├── api_server.py                     # FastAPI REST API backend
│   ├── gemini_recommender.py             # Live Gemini doctor recommendation engine
│   ├── recommendation.py                 # Hybrid doctor recommendation & ranking
│   ├── inference.py                      # Standalone YOLO11 Inference Engine
│   └── database.py                       # MongoDB & local JSON persistence
├── models/                               # Saved model weights
├── data/                                 # Doctor directory dataset & scan records
├── app/
│   └── components.py                     # Clinical HTML badges & printable report generator
├── run_backend.py                        # FastAPI server launcher (port 8000)
├── requirements.txt                      # Python backend dependencies
└── README.md                             # Documentation & project guide
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

### Step 6: Launch CliniScan+ (FastAPI Backend + Next.js Frontend)

#### Terminal 1: Start FastAPI REST API Backend
```bash
python run_backend.py
# Backend API available at: http://localhost:8000
# Interactive API Docs: http://localhost:8000/docs
```

#### Terminal 2: Start Next.js React Web Application
```bash
cd frontend
npm install
npm run dev
# Open Web Application in Browser: http://localhost:3000
```

---

## 🖥️ 5. Next.js Clinical Web Application Modules

1. **🧑‍🦱 Patient Portal**:
   - **Interactive X-ray Scanner**: Drag-and-drop file upload & VinBigData sample selector with real-time confidence sliders.
   - **YOLO11 Localization**: Sub-second bounding boxes, class probability %, anatomical quadrant localization, and clinical severity indicators.
   - **Specialist Matching**: Automatic matching of detected findings to recommended medical specialists.
   - **My Appointments**: Live tracking of doctor confirmations and downloadable referral passes.
   - **Scan History**: Full diagnostic report vault with standalone printable HTML/PDF export.

2. **👨‍⚕️ Doctor Review Dashboard**:
   - **Triage Queue**: Triage incoming patient requests across the hospital network.
   - **1-Click Confirmation**: Direct confirmation and custom clinical prescription advice.
   - **Diagnostic Studio Lab**: High-resolution radiograph triage with doctor-signed certificate generation.
   - **Practice Profile**: Real-time management of doctor specialization, hospital network, fees, and availability.

3. **🔬 Laboratory Diagnostic Portal**:
   - **Patient Intake**: MRN registration, age, gender, and clinical history intake.
   - **Automated Triage**: Instant YOLO11 detection execution and official lab certificate generation.
   - **Specialist Routing**: Direct routing of laboratory findings to verified hospital specialists.
   - **Registry & Accreditation**: Processed tests registry and facility credentials.

4. **🔍 2,000-Doctor Directory**:
   - Multi-filter explorer across 26 cities and 10 hospital networks with live search and appointment scheduling.

5. **📊 Model & Research Insights**:
   - Supported 10 target pathologies, severity mapping, YOLO11 architecture specs, and dataset split details.

---

## ⚠️ 6. Medical Decision Support Disclaimer
CliniScan+ is designed strictly for investigational, educational, and clinical decision support purposes. It is not an autonomous diagnostic device. All AI-generated findings must be independently verified by a licensed radiologist or medical professional prior to clinical intervention.
