"""
CliniScan+ High-Performance FastAPI REST API Backend
Serves multi-role authentication, YOLO11 chest X-ray inference,
2,000-doctor directory search & recommendation, appointments, and report generation.
"""

import os
import sys
import io
import time
import base64
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# Pre-load torchvision extension to prevent circular import in Python 3.13
try:
    import torch
    import torchvision.extension
    import torchvision
except Exception:
    pass

from fastapi import FastAPI, UploadFile, File, Form, Query, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from pydantic import BaseModel, Field
from PIL import Image
import numpy as np

# Ensure project root is in python path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.inference import CliniScanDetector, TARGET_CLASSES, SEVERITY_MAPPING
from src.recommendation import doctor_engine
from src.database import db_instance
from src.gemini_chatbot import chatbot_engine
from app.components import generate_printable_referral_report_html, image_to_base64

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CliniScanAPI")

app = FastAPI(
    title="CliniScan+ Hospital API",
    description="REST API backend for AI-assisted Chest X-ray Triage & Specialist Referral Network",
    version="1.0.0"
)

# Enable CORS for Next.js (port 3000) and any local dev origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Initialize YOLO11 Detector
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "cliniscan_yolo11n_best.pt")
FALLBACK_MODEL = os.path.join(PROJECT_ROOT, "yolo11n.pt")
detector = CliniScanDetector(model_path=MODEL_PATH, fallback_model=FALLBACK_MODEL)


# ==============================================================================
# PYDANTIC SCHEMAS
# ==============================================================================
class LoginRequest(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: str
    role: Optional[str] = None


class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str
    full_name: str
    email: str
    phone: str
    city: str
    extra_data: Optional[Dict[str, Any]] = None


class ProfileUpdateRequest(BaseModel):
    username: str
    updates: Dict[str, Any]
    new_password: Optional[str] = None


class RecommendationRequest(BaseModel):
    detected_findings: List[Dict[str, Any]] = []
    city_filter: Optional[str] = None
    hospital_filter: Optional[str] = None
    availability_only: bool = True
    max_fee: Optional[int] = None
    top_k: int = 6
    use_gemini_live: Optional[bool] = True


class AppointmentCreateRequest(BaseModel):
    patient_username: str
    patient_name: str
    patient_phone: str
    doctor_name: str
    specialization: Optional[str] = "Specialist"
    hospital: Optional[str] = "Hospital"
    city: Optional[str] = "Bangalore"
    clinical_indication: Optional[str] = "Chest Radiograph Follow-up"
    appointment_slot: Optional[str] = "Tomorrow 10:00 AM"


class AppointmentConfirmRequest(BaseModel):
    doctor_name: str
    doctor_notes: Optional[str] = ""
    status: str = "Confirmed"


class ScanRecordCreateRequest(BaseModel):
    username: str
    user_role: str
    patient_name: str
    patient_id: str
    age: int
    gender: str
    city: str
    findings_count: int
    findings: List[Dict[str, Any]]
    image_b64: Optional[str] = None


class ReportGenerateRequest(BaseModel):
    report_id: str
    patient_info: Dict[str, Any]
    detection_results: Dict[str, Any]
    referred_doctor: Optional[Dict[str, Any]] = None
    annotated_img_b64: Optional[str] = None
    doctor_notes: Optional[str] = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[ChatMessage]] = []
    context: Optional[Dict[str, Any]] = None



# ==============================================================================
# 1. AUTHENTICATION & USER MANAGEMENT
# ==============================================================================
@app.post("/api/auth/login")
def login_user(req: LoginRequest):
    login_id = req.username or req.email
    if not login_id:
        raise HTTPException(status_code=400, detail="Username or email is required.")
    user = db_instance.authenticate_user(login_id, req.password, req.role)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username, password, or role.")
    return {"status": "success", "user": user}


@app.post("/api/auth/register")
def register_user(req: RegisterRequest):
    ok, msg = db_instance.register_user(
        username=req.username,
        password=req.password,
        role=req.role,
        full_name=req.full_name,
        email=req.email,
        phone=req.phone,
        city=req.city,
        extra_data=req.extra_data
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    
    if req.role == "Doctor":
        doctor_engine.reload()

    user = db_instance.get_user(req.username)
    return {"status": "success", "message": msg, "user": user}


@app.get("/api/auth/demo-users")
def get_demo_users():
    """Retrieve pre-seeded demo accounts and registered custom accounts."""
    all_users = []
    if db_instance.db is not None:
        all_users = list(db_instance.db.users.find({}, {"_id": 0, "password_hash": 0}))
    
    demo_accounts = [u for u in all_users if u.get("username", "").endswith("_demo")]
    custom_accounts = [u for u in all_users if not u.get("username", "").endswith("_demo")]

    return {
        "demo_accounts": demo_accounts,
        "custom_accounts": custom_accounts,
        "storage_mode": db_instance.storage_mode
    }


@app.get("/api/auth/me")
def get_user_profile(username: str = Query(...)):
    user = db_instance.get_user(username)
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"user": user}


@app.put("/api/auth/profile")
def update_profile(req: ProfileUpdateRequest):
    ok, msg, updated_u = db_instance.update_user_profile(
        username=req.username,
        updates=req.updates,
        new_password=req.new_password
    )
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    
    return {"status": "success", "message": msg, "user": updated_u}


# ==============================================================================
# 2. RADIOGRAPH SAMPLES & AI INFERENCE
# ==============================================================================
def get_samples_directories() -> List[str]:
    dirs = [
        os.path.join(PROJECT_ROOT, "sample_images"),
        os.path.join(PROJECT_ROOT, "data", "processed", "images", "test"),
        os.path.join(PROJECT_ROOT, "vinbigdata", "train"),
    ]
    return [d for d in dirs if os.path.exists(d)]


@app.get("/api/samples")
def list_sample_images():
    """List sample test radiographs available on the server."""
    samples = []
    for s_dir in get_samples_directories():
        files = [f for f in os.listdir(s_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        for f in files[:20]:
            if not any(s["filename"] == f for s in samples):
                samples.append({
                    "filename": f,
                    "directory": os.path.basename(s_dir),
                    "size_bytes": os.path.getsize(os.path.join(s_dir, f))
                })
        if len(samples) >= 30:
            break
    return {"samples": samples}


@app.get("/api/samples/{filename}")
def get_sample_image_file(filename: str):
    """Retrieve the sample image binary file."""
    for s_dir in get_samples_directories():
        fp = os.path.join(s_dir, filename)
        if os.path.exists(fp):
            return FileResponse(fp, media_type="image/jpeg")
    raise HTTPException(status_code=404, detail=f"Sample image '{filename}' not found.")


@app.post("/api/inference/detect")
async def run_detection(
    file: Optional[UploadFile] = File(None),
    sample_name: Optional[str] = Form(None),
    image_base64_input: Optional[str] = Form(None),
    conf_threshold: float = Form(0.15),
    iou_threshold: float = Form(0.45)
):
    """Run Ultralytics YOLO11 model detection on uploaded radiograph or sample."""
    pil_image = None
    source_name = "radiograph.jpg"

    if file is not None and file.filename:
        content = await file.read()
        pil_image = Image.open(io.BytesIO(content)).convert("RGB")
        source_name = file.filename
    elif sample_name:
        for s_dir in get_samples_directories():
            fp = os.path.join(s_dir, sample_name)
            if os.path.exists(fp):
                pil_image = Image.open(fp).convert("RGB")
                source_name = sample_name
                break
        if pil_image is None:
            raise HTTPException(status_code=404, detail=f"Sample image '{sample_name}' not found.")
    elif image_base64_input:
        try:
            raw_b64 = image_base64_input.split(",")[-1]
            img_data = base64.b64decode(raw_b64)
            pil_image = Image.open(io.BytesIO(img_data)).convert("RGB")
            source_name = "base64_upload.jpg"
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid base64 image data: {e}")
    else:
        raise HTTPException(status_code=400, detail="No image file, sample name, or base64 data provided.")

    # Original Image Base64
    orig_b64 = image_to_base64(pil_image)

    # Execute YOLO11 Inference
    try:
        results = detector.predict(
            image_input=pil_image,
            conf_threshold=conf_threshold,
            iou_threshold=iou_threshold
        )
    except Exception as e:
        logger.error(f"Inference error: {e}")
        raise HTTPException(status_code=500, detail=f"Inference failed: {str(e)}")

    # Convert annotated RGB image to base64
    annotated_pil = Image.fromarray(results["annotated_image_rgb"])
    annotated_b64 = image_to_base64(annotated_pil)

    # Get matched doctor recommendation summary automatically (robust fallback)
    try:
        recs = doctor_engine.recommend_doctors(
            detected_findings=results["detections"],
            city_filter=None,
            top_k=6,
            use_gemini_live=True
        )
    except Exception as e:
        logger.warning(f"Live recommendation failed, using local directory fallback: {e}")
        recs = doctor_engine.recommend_doctors(
            detected_findings=results["detections"],
            city_filter=None,
            top_k=6,
            use_gemini_live=False
        )

    return {
        "model_version": results["model_version"],
        "source_image": source_name,
        "image_dimensions": results["image_dimensions"],
        "findings_count": results["findings_count"],
        "detections": results["detections"],
        "inference_time_ms": results["inference_time_ms"],
        "conf_threshold_used": results["conf_threshold_used"],
        "iou_threshold_used": results["iou_threshold_used"],
        "status": results["status"],
        "original_image_b64": orig_b64,
        "annotated_image_b64": annotated_b64,
        "recommendations": recs
    }


# ==============================================================================
# 3. DOCTOR DIRECTORY & SPECIALIST RECOMMENDATIONS
# ==============================================================================
@app.get("/api/doctors")
def search_doctors(
    query: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    specialization: Optional[str] = Query(None),
    hospital: Optional[str] = Query(None),
    min_rating: float = Query(0.0),
    max_fee: Optional[int] = Query(None),
    availability: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(24, ge=1, le=100)
):
    """Search and filter the 2,000+ specialist directory with pagination."""
    avail_only = (availability.lower() == "available") if availability else False
    
    all_results = doctor_engine.search_all_doctors(
        query=query,
        specialty=specialization,
        city=city,
        hospital=hospital,
        min_rating=min_rating,
        max_fee=max_fee,
        available_only=avail_only
    )

    total_count = len(all_results)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    paginated_docs = all_results[start_idx:end_idx]

    return {
        "total_count": total_count,
        "page": page,
        "limit": limit,
        "total_pages": (total_count + limit - 1) // limit if total_count > 0 else 1,
        "doctors": paginated_docs
    }


@app.post("/api/doctors/register")
def register_specialist(payload: Dict[str, Any]):
    """Register a new doctor specialist into the 2,000-doctor directory."""
    ok, msg, new_doc = doctor_engine.register_doctor_into_system(payload)
    if not ok:
        raise HTTPException(status_code=400, detail=msg)
    return {"status": "success", "message": msg, "doctor": new_doc}


@app.post("/api/recommendations/match")
def get_recommendations(req: RecommendationRequest):
    """Match detected X-ray findings to top ranked clinical specialists."""
    recs = doctor_engine.recommend_doctors(
        detected_findings=req.detected_findings,
        city_filter=req.city_filter,
        hospital_filter=req.hospital_filter,
        availability_only=req.availability_only,
        max_fee=req.max_fee,
        top_k=req.top_k,
        use_gemini_live=req.use_gemini_live if req.use_gemini_live is not None else True
    )
    return recs


# ==============================================================================
# 4. APPOINTMENTS & DOCTOR TRIAGE WORKFLOW
# ==============================================================================
@app.post("/api/appointments")
def create_appointment(req: AppointmentCreateRequest):
    apt_id = db_instance.create_appointment(req.model_dump())
    if not apt_id:
        raise HTTPException(status_code=500, detail="Failed to create appointment.")
    return {"status": "success", "appointment_id": apt_id, "message": "Appointment booked successfully!"}


@app.get("/api/appointments")
def get_appointments(
    patient_username: Optional[str] = Query(None),
    doctor_name: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    limit: int = Query(100)
):
    if patient_username:
        apts = db_instance.get_patient_appointments(patient_username)
    elif doctor_name:
        apts = db_instance.get_doctor_appointments(doctor_name=doctor_name)
    else:
        apts = db_instance.get_all_appointments(limit=limit)

    if status_filter and status_filter != "All":
        apts = [a for a in apts if a.get("status") == status_filter]

    return {"appointments": apts, "count": len(apts)}


@app.put("/api/appointments/{appointment_id}/confirm")
def confirm_appointment_endpoint(appointment_id: str, req: AppointmentConfirmRequest):
    ok = db_instance.confirm_appointment(
        appointment_id=appointment_id,
        doctor_name=req.doctor_name,
        doctor_notes=req.doctor_notes or "",
        status=req.status
    )
    if not ok:
        raise HTTPException(status_code=400, detail="Failed to update appointment status.")
    return {"status": "success", "message": f"Appointment #{appointment_id} updated to {req.status}."}


# ==============================================================================
# 5. DIAGNOSTIC SCANS & LABORATORY REGISTRY
# ==============================================================================
@app.post("/api/scans")
def save_diagnostic_scan(req: ScanRecordCreateRequest):
    scan_id = db_instance.save_scan_record(req.model_dump())
    if not scan_id:
        raise HTTPException(status_code=500, detail="Failed to save diagnostic scan.")
    return {"status": "success", "scan_id": scan_id}


@app.get("/api/scans")
def get_user_scans_endpoint(username: Optional[str] = Query(None), limit: int = Query(50)):
    if username:
        scans = db_instance.get_user_scans(username, limit=limit)
    else:
        scans = db_instance.get_all_scans(limit=limit)
    return {"scans": scans, "count": len(scans)}


# ==============================================================================
# 6. PRINTABLE REPORTS & METADATA
# ==============================================================================
@app.post("/api/reports/generate", response_class=HTMLResponse)
def generate_report_html(req: ReportGenerateRequest):
    html_content = generate_printable_referral_report_html(
        report_id=req.report_id,
        patient_info=req.patient_info,
        detection_results=req.detection_results,
        referred_doctor=req.referred_doctor,
        annotated_img_b64=req.annotated_img_b64,
        doctor_notes=req.doctor_notes
    )
    return HTMLResponse(content=html_content)


@app.get("/api/meta/filters")
def get_metadata_filters():
    """Retrieve dropdown filter options and system configuration metadata."""
    return {
        "cities": ["All Cities"] + doctor_engine.get_cities(),
        "specializations": ["All Specializations"] + doctor_engine.get_specializations(),
        "hospitals": ["All Hospitals"] + doctor_engine.get_hospitals(),
        "target_classes": TARGET_CLASSES,
        "severity_mapping": SEVERITY_MAPPING,
        "storage_mode": db_instance.storage_mode,
        "total_doctors": len(doctor_engine.df)
    }


@app.post("/api/chat")
def chat_endpoint(req: ChatRequest):
    """Conversational Clinical AI Assistant powered by Google Gemini."""
    try:
        history_dicts = [{"role": h.role, "content": h.content} for h in (req.history or [])]
        reply = chatbot_engine.generate_response(
            message=req.message,
            history=history_dicts,
            context=req.context
        )
        return {
            "status": "success",
            "reply": reply,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Chat API exception: {e}")
        return {
            "status": "fallback",
            "reply": "I am here to assist with your chest X-ray findings and doctor referrals. How can I help you today?",
            "timestamp": datetime.now().isoformat()
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.api_server:app", host="127.0.0.1", port=8000, reload=True)
