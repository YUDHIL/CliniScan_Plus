"""
Comprehensive Test Suite for CliniScan+ FastAPI REST API Endpoints
"""

import os
import sys
from fastapi.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.api_server import app

client = TestClient(app)

def run_tests():
    print("--- 1. Testing Metadata Filters ---")
    res = client.get("/api/meta/filters")
    assert res.status_code == 200, f"Failed meta: {res.text}"
    meta = res.json()
    print(f"✅ Loaded {len(meta['cities'])} cities, {len(meta['specializations'])} specialties, {meta['total_doctors']} doctors.")

    print("\n--- 2. Testing Demo Accounts ---")
    res = client.get("/api/auth/demo-users")
    assert res.status_code == 200
    data = res.json()
    print(f"✅ Found {len(data['demo_accounts'])} demo accounts and {len(data['custom_accounts'])} custom accounts.")

    print("\n--- 3. Testing Authentication (patient_demo, doctor_demo, lab_demo) ---")
    for role, user_id, pwd in [
        ("Patient", "patient_demo", "patient123"),
        ("Doctor", "doctor_demo", "doctor123"),
        ("Laboratory", "lab_demo", "lab123")
    ]:
        res = client.post("/api/auth/login", json={"username": user_id, "password": pwd, "role": role})
        assert res.status_code == 200, f"Login failed for {user_id}: {res.text}"
        u = res.json()["user"]
        print(f"✅ Authenticated: {u['full_name']} ({u['role']})")

    print("\n--- 4. Testing Samples Listing & Binary Retrieval ---")
    res = client.get("/api/samples")
    assert res.status_code == 200
    samples = res.json()["samples"]
    print(f"✅ Found {len(samples)} test samples: {[s['filename'] for s in samples[:3]]}")
    
    if samples:
        sample_name = samples[0]["filename"]
        img_res = client.get(f"/api/samples/{sample_name}")
        assert img_res.status_code == 200, f"Failed to fetch sample image binary: {img_res.status_code}"
        assert len(img_res.content) > 1000
        print(f"✅ Sample Image Streamed: {sample_name} ({len(img_res.content)} bytes)")

        print("\n--- 5. Testing YOLO11 Inference on Sample ---")
        res = client.post("/api/inference/detect", data={"sample_name": sample_name, "conf_threshold": 0.15})
        assert res.status_code == 200, f"Inference failed: {res.text}"
        inf = res.json()
        print(f"✅ Inference Success! Findings: {inf['findings_count']} | Status: {inf['status']} | Time: {inf['inference_time_ms']}ms")

    print("\n--- 6. Testing 2,000-Doctor Directory Search & Filters ---")
    res = client.get("/api/doctors?city=Bangalore&limit=5")
    assert res.status_code == 200
    docs = res.json()
    print(f"✅ Doctor Search: Total {docs['total_count']} doctors matching Bangalore. Page returned {len(docs['doctors'])}.")

    print("\n--- 7. Testing Recommendation Matching Engine ---")
    sample_findings = [{"class_name": "Pleural effusion", "confidence_pct": "84%", "location": "Right Lower Zone", "severity": "High"}]
    res = client.post("/api/recommendations/match", json={"detected_findings": sample_findings, "top_k": 3})
    assert res.status_code == 200
    rec_data = res.json()
    print(f"✅ Recommendation Engine: Primary Specialty '{rec_data['primary_specialty']}' with {len(rec_data['recommended_doctors'])} matched doctors.")


    print("\n--- 8. Testing Diagnostic Scan Saving & History ---")
    res = client.post("/api/scans", json={
        "username": "patient_demo",
        "user_role": "Patient",
        "patient_name": "Eleanor Vance",
        "patient_id": "PAT-TEST-001",
        "age": 58,
        "gender": "Female",
        "city": "Bangalore",
        "findings_count": 1,
        "findings": sample_findings
    })
    assert res.status_code == 200
    scan_id = res.json()["scan_id"]
    print(f"✅ Diagnostic Scan Saved with ID: {scan_id}")

    res = client.get("/api/scans?username=patient_demo")
    assert res.status_code == 200
    print(f"✅ Patient Scan History retrieved {res.json()['count']} records.")

    print("\n--- 9. Testing Appointments Workflow (Create & Confirm) ---")
    res = client.post("/api/appointments", json={
        "patient_username": "patient_demo",
        "patient_name": "Eleanor Vance",
        "patient_phone": "+91 98765 43210",
        "doctor_name": "Dr. Yukti Chauhan",
        "specialization": "Pulmonologist",
        "hospital": "AIIMS Hospital",
        "city": "Bangalore",
        "clinical_indication": "Pleural Effusion Follow-up",
        "appointment_slot": "Tomorrow 10:00 AM"
    })
    assert res.status_code == 200
    apt_id = res.json()["appointment_id"]
    print(f"✅ Appointment Booked with ID: {apt_id}")

    res = client.put(f"/api/appointments/{apt_id}/confirm", json={
        "doctor_name": "Dr. Yukti Chauhan",
        "doctor_notes": "Confirmed. Please report to the pulmonary unit.",
        "status": "Confirmed"
    })
    assert res.status_code == 200
    print(f"✅ Appointment #{apt_id} Confirmed by Doctor.")

    print("\n--- 10. Testing Standalone HTML Report Generation ---")
    res = client.post("/api/reports/generate", json={
        "report_id": f"RAD-TEST-{apt_id}",
        "patient_info": {"full_name": "Eleanor Vance", "patient_id": "PAT-TEST-001", "age": 58, "gender": "Female", "city": "Bangalore"},
        "detection_results": {"findings_count": 1, "detections": sample_findings, "inference_time_ms": 145.2},
        "referred_doctor": {"doctor_name": "Dr. Yukti Chauhan", "specialization": "Pulmonologist", "hospital": "AIIMS Hospital", "city": "Bangalore", "fees_inr": 800},
        "doctor_notes": "Clinical confirmation verified."
    })
    assert res.status_code == 200
    assert "CliniScan+" in res.text
    print(f"✅ Standalone HTML Diagnostic Report generated successfully ({len(res.text)} characters).")

    print("\n🎉 ALL 10 CRITICAL BACKEND API SUITES PASSED FLAWLESSLY!")

if __name__ == "__main__":
    run_tests()

