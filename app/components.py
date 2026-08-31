"""
CliniScan+ Hospital UI Components, Doctor Profile Cards,
Appointment Passes, and Official Diagnostic/Referral Report Generators
"""

import base64
import textwrap
from io import BytesIO
from typing import Dict, List, Optional
from PIL import Image


def image_to_base64(img: Image.Image) -> str:
    """Convert PIL image to base64 data URI."""
    buffered = BytesIO()
    img.save(buffered, format="JPEG", quality=90)
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{img_str}"


def render_finding_html(finding: Dict) -> str:
    """Render a clinical finding badge and localized site."""
    cls_name = finding.get("class_name", "Unknown")
    conf_pct = finding.get("confidence_pct", "0%")
    loc = finding.get("location", "Hemithorax")
    severity = finding.get("severity", "Moderate")
    urgency = finding.get("clinical_urgency", "Clinical correlation recommended")

    badge_class = "badge-moderate"
    if severity == "Critical":
        badge_class = "badge-critical"
    elif severity in ["High", "Moderate-High"]:
        badge_class = "badge-high"
    elif severity in ["Low-Moderate", "Low"]:
        badge_class = "badge-low"

    html = f"""<div class="finding-card">
<div class="finding-card-title">
<span><strong>{finding.get('detection_id', 1)}. {cls_name}</strong></span>
<span class="badge {badge_class}">{severity}</span>
</div>
<div style="font-size: 0.84rem; color: #475569; margin-top: 0.3rem;">
<strong>Confidence:</strong> {conf_pct} &nbsp;|&nbsp; <strong>Anatomical Site:</strong> {loc}
</div>
<div style="font-size: 0.8rem; color: #64748b; margin-top: 0.25rem; font-style: italic;">
Recommendation: {urgency}
</div>
</div>"""
    return html


def render_specialist_match_summary(rec_data: Dict) -> str:
    """Renders top summary recommendation banner based on detected pathology."""
    primary_spec = rec_data.get("primary_specialty", "Pulmonologist")
    urgency = rec_data.get("clinical_urgency", "Clinical correlation recommended")
    summary = rec_data.get("clinical_summary", "")

    html = f"""<div class="recs-header-banner">
<div>
<div class="recs-header-title">🩺 Recommended Primary Specialist: {primary_spec}</div>
<div class="recs-header-sub">{summary}</div>
</div>
<div style="text-align: right; background: rgba(255,255,255,0.18); padding: 6px 14px; border-radius: 8px;">
<div style="font-size: 0.72rem; text-transform: uppercase; font-weight: 700; color: #bae6fd;">Clinical Urgency</div>
<div style="font-size: 0.88rem; font-weight: 800; color: #ffffff;">{urgency}</div>
</div>
</div>"""
    return html


def render_doctor_card_html(doc: Dict) -> str:
    """Render a clean hospital specialist profile card."""
    doc_name = doc.get("doctor_name", "Doctor")
    specialty = doc.get("specialization", "Specialist")
    disease = doc.get("disease_expertise", "General")
    hospital = doc.get("hospital", "Hospital Network")
    city = doc.get("city", "City")
    rating = doc.get("rating", 4.5)
    exp = doc.get("experience_years", 10)
    fee = doc.get("fees_inr", 800)
    avail = doc.get("availability", "Available")
    is_exact = doc.get("is_exact_match", False)

    is_reg = doc.get("is_registered", False)

    reg_badge = (
        '<span style="background: #dcfce7; color: #15803d; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; border: 1px solid #86efac; margin-right: 4px;">🌟 Registered Specialist</span>'
        if is_reg
        else ''
    )

    avail_badge = (
        '<span class="avail-badge-available">● Available</span>'
        if avail.lower() == "available"
        else '<span class="avail-badge-busy">● Busy</span>'
    )

    match_badge = (
        '<span style="background: #e0f2fe; color: #0369a1; font-size: 0.72rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; border: 1px solid #bae6fd;">🎯 Pathology Match</span>'
        if is_exact
        else ''
    )

    clean_for_initials = doc_name.replace("Dr.", "").replace("Dr", "").strip()
    parts = clean_for_initials.split()
    initials = "".join([p[0].upper() for p in parts[:2]]) if parts else "DR"

    html = f"""<div class="doctor-card">
<div class="doctor-card-top">
<div class="doctor-avatar">{initials}</div>
<div class="doctor-info-col">
<div style="display: flex; justify-content: space-between; align-items: flex-start;">
<h3 class="doctor-name">{doc_name}</h3>
<div>{reg_badge}{avail_badge}</div>
</div>
<div class="doctor-specialty">{specialty} &nbsp;{match_badge}</div>
<div style="font-size: 0.78rem; color: #475569; margin-top: 0.25rem;">Expertise: <strong>{disease}</strong></div>
</div>
</div>
<div class="doctor-meta-grid">
<div>🏥 <strong>{hospital}</strong></div>
<div>📍 <strong>{city}</strong></div>
<div>⭐ <strong>{rating:.1f} / 5.0</strong> Rating</div>
<div>🩺 <strong>{exp} Years</strong> Experience</div>
</div>
<div class="doctor-card-footer">
<div>
<span style="font-size: 0.72rem; color: #64748b; font-weight: 600;">CONSULTATION FEE</span><br>
<span class="doctor-fee">₹{fee:,}</span>
</div>
<div style="font-size: 0.8rem; color: #0284c7; font-weight: 700;">
Verified Medical Specialist ✔️
</div>
</div>
</div>"""
    return html


def render_appointment_card_html(apt: Dict, user_role: str = "Patient") -> str:
    """Render an appointment status record card for patient or doctor."""
    apt_id = apt.get("appointment_id", "APT-000000")
    p_name = apt.get("patient_name", "Anonymous")
    p_phone = apt.get("patient_phone", "N/A")
    d_name = apt.get("doctor_name", "Doctor")
    hosp = apt.get("hospital", "Hospital")
    city = apt.get("city", "City")
    finding = apt.get("clinical_indication", "Routine Checkup")
    slot = apt.get("appointment_slot", "Slot N/A")
    status = apt.get("status", "Pending")
    notes = apt.get("doctor_notes", "")
    created_at = apt.get("created_at", "N/A")

    if status == "Confirmed":
        badge_html = '<span class="status-badge status-confirmed">🟢 Confirmed by Doctor</span>'
    elif status == "Declined":
        badge_html = '<span class="status-badge" style="background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5;">🔴 Declined</span>'
    else:
        badge_html = '<span class="status-badge status-pending">⏳ Pending Doctor Confirmation</span>'

    notes_html = ""
    if notes:
        notes_html = f"""<div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; padding: 8px 12px; margin-top: 10px; font-size: 0.84rem; color: #166534;"><strong>👨‍⚕️ Doctor's Prescription Notes:</strong> {notes}</div>"""

    html = f"""<div class="appointment-card">
<div class="appointment-header">
<div>
<strong style="color: #0f172a; font-size: 0.95rem;">Appointment #{apt_id}</strong>
<span style="font-size: 0.78rem; color: #64748b; margin-left: 8px;">Booked on {created_at[:10]}</span>
</div>
<div>{badge_html}</div>
</div>
<div class="appointment-grid">
<div>
<div style="font-size: 0.72rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Patient</div>
<div style="font-weight: 700; color: #0f172a;">{p_name}</div>
<div style="font-size: 0.8rem; color: #475569;">📞 {p_phone}</div>
</div>
<div>
<div style="font-size: 0.72rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Doctor & Hospital</div>
<div style="font-weight: 700; color: #0284c7;">{d_name}</div>
<div style="font-size: 0.8rem; color: #475569;">🏥 {hosp}, {city}</div>
</div>
<div>
<div style="font-size: 0.72rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Clinical Indication & Slot</div>
<div style="font-weight: 600; color: #b91c1c;">{finding}</div>
<div style="font-size: 0.8rem; color: #475569;">📅 {slot}</div>
</div>
</div>
{notes_html}
</div>"""
    return html


def generate_printable_referral_report_html(
    report_id: str,
    patient_info: Dict,
    detection_results: Dict,
    referred_doctor: Optional[Dict] = None,
    annotated_img_b64: Optional[str] = None,
    doctor_notes: Optional[str] = None
) -> str:
    """Generates official hospital referral certificate in standalone HTML/printable format."""
    findings = detection_results.get("detections", [])
    findings_rows = ""
    for f in findings:
        findings_rows += f"""<tr>
<td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-weight: 600;">{f.get('class_name')}</td>
<td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{f.get('location')}</td>
<td style="padding: 10px; border-bottom: 1px solid #e2e8f0;">{f.get('confidence_pct')}</td>
<td style="padding: 10px; border-bottom: 1px solid #e2e8f0; color: #b91c1c; font-weight: 600;">{f.get('severity')}</td>
<td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-size: 0.85em;">{f.get('clinical_urgency')}</td>
</tr>"""

    if not findings:
        findings_rows = """<tr>
<td colspan="5" style="padding: 15px; text-align: center; color: #059669; font-weight: 600;">
No focal pulmonary or pleural abnormalities detected.
</td>
</tr>"""

    doc_referral_html = ""
    if referred_doctor:
        doc_referral_html = f"""<div style="background: #f0f9ff; border: 1.5px solid #0284c7; border-radius: 8px; padding: 18px; margin: 20px 0;">
<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #bae6fd; padding-bottom: 8px; margin-bottom: 10px;">
<h3 style="margin: 0; color: #0369a1; font-size: 1.1em;">👨‍⚕️ Prescribed Clinical Specialist Referral</h3>
<span style="background: #0284c7; color: white; padding: 2px 8px; border-radius: 9999px; font-size: 0.72rem; font-weight: 700;">CONFIRMED REFERRAL</span>
</div>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.9em;">
<div><strong>Doctor Name:</strong> {referred_doctor.get('doctor_name')}</div>
<div><strong>Specialization:</strong> {referred_doctor.get('specialization')}</div>
<div><strong>Hospital Center:</strong> {referred_doctor.get('hospital')}, {referred_doctor.get('city')}</div>
<div><strong>Consultation Fee:</strong> ₹{referred_doctor.get('fees_inr', 0):,}</div>
<div><strong>Pathology Indication:</strong> {referred_doctor.get('disease_expertise')}</div>
</div>
</div>"""

    img_html = ""
    if annotated_img_b64:
        img_html = f"""<div style="text-align: center; margin: 20px 0;">
<h4 style="color: #0f172a; margin-bottom: 10px;">Annotated Radiograph</h4>
<img src="{annotated_img_b64}" style="max-width: 440px; width: 100%; border-radius: 8px; border: 1px solid #cbd5e1;" />
</div>"""

    doc_section = ""
    if doctor_notes:
        doc_section = f"""<div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 15px; margin-top: 15px;">
<h4 style="margin: 0 0 6px 0; color: #0f172a;">Attending Physician Review & Prescription</h4>
<p style="margin: 0; font-size: 0.92em; color: #334155; line-height: 1.5;">{doctor_notes}</p>
</div>"""

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>CliniScan+ Diagnostic Report - {report_id}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: #f1f5f9;
    color: #0f172a;
    padding: 20px;
    margin: 0;
}}
.no-print-bar {{
    max-width: 840px;
    margin: 0 auto 15px auto;
    display: flex;
    justify-content: flex-end;
    gap: 10px;
}}
.btn-print {{
    background: #0284c7;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 8px 18px;
    font-weight: 700;
    cursor: pointer;
    font-size: 0.9rem;
    box-shadow: 0 2px 4px rgba(2, 132, 199, 0.3);
}}
.btn-print:hover {{
    background: #0369a1;
}}
.report-card {{
    background: #ffffff;
    max-width: 840px;
    margin: 0 auto;
    padding: 35px 40px;
    border-radius: 12px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 10px 25px rgba(0,0,0,0.06);
}}
.table-findings {{
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    font-size: 0.88em;
}}
.table-findings th {{
    background-color: #0f172a;
    color: #ffffff;
    text-align: left;
    padding: 10px 12px;
    font-size: 0.8em;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
@media print {{
    body {{
        background: #ffffff;
        padding: 0;
    }}
    .no-print-bar {{
        display: none !important;
    }}
    .report-card {{
        border: none;
        box-shadow: none;
        padding: 0;
        max-width: 100%;
    }}
}}
</style>
</head>
<body>
<div class="no-print-bar">
    <button class="btn-print" onclick="window.print()">🖨️ Print / Save as PDF</button>
</div>
<div class="report-card">
<div style="border-bottom: 3px solid #0284c7; padding-bottom: 15px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: flex-end;">
<div>
<div style="display: flex; align-items: center; gap: 8px;">
<span style="font-size: 1.6rem;">🫁</span>
<h1 style="margin: 0; font-size: 1.5em; color: #0284c7; font-weight: 800;">CliniScan+ Hospital Diagnostic & Referral Report</h1>
</div>
<div style="font-size: 0.84em; color: #64748b; margin-top: 4px;">Automated YOLO11 Chest Radiograph AI Abnormality Triage</div>
</div>
<div style="text-align: right; font-size: 0.84em; color: #475569; line-height: 1.5;">
<div><strong>Report ID:</strong> <span style="font-family: monospace; font-weight: 700; color: #0f172a;">{report_id}</span></div>
<div><strong>Date:</strong> {patient_info.get('timestamp', 'N/A')}</div>
<div><span style="background: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 4px; font-weight: 700; font-size: 0.75rem;">Verified Certificate ✔️</span></div>
</div>
</div>

<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; background: #f8fafc; padding: 14px 16px; border-radius: 8px; border: 1px solid #e2e8f0; font-size: 0.88em; margin-bottom: 20px;">
<div><strong>Patient Full Name:</strong> {patient_info.get('full_name', 'Anonymous')}</div>
<div><strong>Patient ID / MRN:</strong> <code style="font-size: 0.95em;">{patient_info.get('patient_id', 'PAT-UNKNOWN')}</code></div>
<div><strong>Age / Gender:</strong> {patient_info.get('age', 'N/A')} Y / {patient_info.get('gender', 'N/A')}</div>
<div><strong>Location Coordinates:</strong> {patient_info.get('city', 'Bangalore')}</div>
<div><strong>Contact Phone:</strong> {patient_info.get('phone', 'N/A')}</div>
<div><strong>Blood Group:</strong> {patient_info.get('blood_group', 'Not Specified')}</div>
</div>

<h3 style="color: #0f172a; margin: 18px 0 8px 0; font-size: 1.1em;">AI Radiographic Detections ({len(findings)})</h3>
<table class="table-findings">
<thead>
<tr>
<th>Pathology Indication</th>
<th>Anatomical Site</th>
<th>Confidence</th>
<th>Severity</th>
<th>Clinical Triage Urgency</th>
</tr>
</thead>
<tbody>
{findings_rows}
</tbody>
</table>

{img_html}

{doc_referral_html}

{doc_section}

<div style="display: flex; justify-content: space-between; align-items: flex-end; margin-top: 30px; padding-top: 15px; border-top: 1px dashed #cbd5e1; font-size: 0.82em; color: #64748b;">
<div>
<strong>CliniScan+ Health Security Network</strong><br>
Diagnostic Radiograph Verification Gateway
</div>
<div style="text-align: right;">
<div style="border-bottom: 1px solid #94a3b8; width: 160px; margin-bottom: 4px;"></div>
Attending Specialist Signature
</div>
</div>

<div style="background: #fef2f2; border-left: 4px solid #ef4444; padding: 10px 14px; border-radius: 0 6px 6px 0; font-size: 0.78em; color: #991b1b; margin-top: 20px; line-height: 1.4;">
<strong>CLINICAL DISCLAIMER:</strong> This automated radiograph analysis is generated by CliniScan+ YOLO11 for assistive diagnostic screening and triage. Definitive patient diagnosis and therapeutic management must be validated by a licensed physician.
</div>
</div>
</body>
</html>"""


def render_patient_id_card_html(user: Dict) -> str:
    """Render a digital patient health ID card."""
    user_id = user.get("user_id", f"PAT-{user.get('username', '').upper()}")
    full_name = user.get("full_name", "Patient")
    username = user.get("username", "patient")
    city = user.get("city", "Bangalore")
    age = user.get("age", "N/A")
    gender = user.get("gender", "N/A")
    blood = user.get("blood_group", "Not Specified")
    phone = user.get("phone", "N/A")
    email = user.get("email", "N/A")

    return f"""<div style="background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color: #ffffff; border-radius: 14px; padding: 1.5rem; box-shadow: 0 10px 25px rgba(2, 132, 199, 0.25);">
<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem;">
<div>
<div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; opacity: 0.85;">Hospital Patient ID</div>
<div style="font-size: 1.15rem; font-weight: 800; font-family: monospace;">{user_id}</div>
</div>
<span style="background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 700;">
Active Patient ✔️
</span>
</div>
<div style="font-size: 1.35rem; font-weight: 800; margin-bottom: 0.35rem;">
{full_name}
</div>
<div style="font-size: 0.85rem; opacity: 0.9; margin-bottom: 1.25rem;">
@{username} &nbsp;|&nbsp; 📍 {city}
</div>
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; background: rgba(0,0,0,0.15); padding: 0.85rem; border-radius: 8px; font-size: 0.84rem;">
<div><strong>Age / Gender:</strong> {age} Y / {gender}</div>
<div><strong>Blood Group:</strong> {blood}</div>
<div><strong>Contact:</strong> {phone}</div>
<div><strong>Email:</strong> {email}</div>
</div>
<div style="margin-top: 1rem; font-size: 0.72rem; opacity: 0.75; text-align: right;">
CliniScan+ Health Security Network
</div>
</div>"""


def render_lab_id_card_html(user: Dict) -> str:
    """Render diagnostic laboratory accreditation pass."""
    user_id = user.get("user_id", f"LAB-{user.get('username', '').upper()}")
    full_name = user.get("full_name", "Diagnostic Center")
    username = user.get("username", "lab")
    city = user.get("city", "Bangalore")
    license_no = user.get("license_no", f"LAB-{city[:3].upper()}-2026")
    lead_radiologist = user.get("lead_radiologist", "Chief Radiologist")
    phone = user.get("phone", "N/A")
    email = user.get("email", "N/A")

    return f"""<div style="background: linear-gradient(135deg, #7c3aed 0%, #4c1d95 100%); color: #ffffff; border-radius: 14px; padding: 1.5rem; box-shadow: 0 10px 25px rgba(124, 58, 237, 0.25);">
<div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.25rem;">
<div>
<div style="font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.08em; opacity: 0.85;">Facility ID</div>
<div style="font-size: 1.15rem; font-weight: 800; font-family: monospace;">{user_id}</div>
</div>
<span style="background: rgba(255,255,255,0.2); padding: 4px 10px; border-radius: 20px; font-size: 0.78rem; font-weight: 700;">
Certified Laboratory ✔️
</span>
</div>
<div style="font-size: 1.3rem; font-weight: 800; margin-bottom: 0.35rem;">
{full_name}
</div>
<div style="font-size: 0.85rem; opacity: 0.9; margin-bottom: 1.25rem;">
@{username} &nbsp;|&nbsp; 📍 {city}
</div>
<div style="background: rgba(0,0,0,0.2); padding: 0.85rem; border-radius: 8px; font-size: 0.84rem; line-height: 1.6;">
<div><strong>License No:</strong> <code>{license_no}</code></div>
<div><strong>Lead Consultant:</strong> {lead_radiologist}</div>
<div><strong>Official Email:</strong> {email}</div>
<div><strong>Direct Line:</strong> {phone}</div>
</div>
<div style="margin-top: 1rem; font-size: 0.72rem; opacity: 0.75; text-align: right;">
CliniScan+ Laboratory Triage Gateway
</div>
</div>"""
