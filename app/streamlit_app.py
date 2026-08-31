"""
CliniScan+ Hospital-Grade AI Chest X-ray Triage & Specialist Referral Platform
Features Multi-Role Authentication (Patient, Doctor, Laboratory), YOLO11 Detection,
2,000-Doctor Directory, and MongoDB-Backed Doctor Confirmation Workflows.
"""

import os
import sys
import time
from datetime import datetime
from io import BytesIO
from PIL import Image
import numpy as np
import pandas as pd

# Pre-load torchvision extension to prevent circular import in Python 3.13
try:
    import torch
    import torchvision.extension
    import torchvision
except Exception:
    pass

import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.inference import CliniScanDetector, TARGET_CLASSES, SEVERITY_MAPPING
from src.recommendation import doctor_engine
from src.database import db_instance
from app.components import (
    image_to_base64,
    render_finding_html,
    render_doctor_card_html,
    render_specialist_match_summary,
    render_appointment_card_html,
    generate_printable_referral_report_html,
    render_patient_id_card_html,
    render_lab_id_card_html
)

# Streamlit Page Config - Clean Hospital Theme
st.set_page_config(
    page_title="CliniScan+ Hospital Portal | YOLO11 AI & Specialist Network",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load Hospital Light CSS
css_path = os.path.join(os.path.dirname(__file__), "styles.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


@st.cache_resource
def get_detector():
    """Cache the YOLO11 model detector."""
    model_best = os.path.join(PROJECT_ROOT, "models", "cliniscan_yolo11n_best.pt")
    return CliniScanDetector(model_path=model_best, fallback_model="yolo11n.pt")


# ==============================================================================
# AUTHENTICATION & SESSION STATE MANAGEMENT
# ==============================================================================
if "user_session" not in st.session_state:
    st.session_state["user_session"] = None

user = st.session_state["user_session"]

# Sidebar - Brand & User Info
st.sidebar.markdown(
    """
    <div style="padding: 10px 0 15px 0;">
        <h2 style="margin: 0; color: #0284c7; font-weight: 800; font-size: 1.6rem; letter-spacing: -0.02em;">🏥 CliniScan+</h2>
        <div style="font-size: 0.8rem; color: #64748b; font-weight: 600;">Hospital AI & Specialist Triage System</div>
    </div>
    """,
    unsafe_allow_html=True
)

if user:
    role_class = f"role-{user['role'].lower()}"
    st.sidebar.markdown(
        f"""
        <div class="user-session-bar" style="margin-bottom: 1rem; padding: 10px 12px;">
            <div>
                <div style="font-size: 0.72rem; color: #64748b; font-weight: 700; text-transform: uppercase;">Signed In As</div>
                <div style="font-weight: 800; color: #0f172a; font-size: 0.95rem;">{user['full_name']}</div>
                <div style="margin-top: 4px;"><span class="role-badge {role_class}">{user['role']}</span></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.sidebar.button("🚪 Sign Out", use_container_width=True):
        st.session_state["user_session"] = None
        st.session_state.clear()
        st.rerun()

    # Doctor Identity Selector
    if user["role"] == "Doctor":
        st.sidebar.markdown("---")
        st.sidebar.markdown("##### 🩺 Doctor Practice Persona")
        
        my_doc_name = user["full_name"].strip()
        if not my_doc_name.startswith("Dr. "):
            my_doc_name = f"Dr. {my_doc_name}"
        
        doctor_options = [f"{my_doc_name} (Signed In Account)"]
        
        # Add all registered doctor accounts from database
        if db_instance.db is not None:
            all_db_doctors = list(db_instance.db.users.find({"role": "Doctor"}, {"_id": 0}))
            for ob in all_db_doctors:
                ob_name = ob.get("full_name", "").strip()
                if not ob_name.startswith("Dr. "):
                    ob_name = f"Dr. {ob_name}"
                opt = f"{ob_name} ({ob.get('hospital', 'Hospital')} - {ob.get('specialization', 'Specialist')})"
                if ob_name != my_doc_name and not any(ob_name in x for x in doctor_options):
                    doctor_options.append(opt)

        selected_doc_option = st.sidebar.selectbox("Active Doctor Identity:", doctor_options, index=0)
        active_doctor_name = selected_doc_option.split(" (")[0]
    else:
        active_doctor_name = user["full_name"]

st.sidebar.markdown("---")
st.sidebar.markdown(
    f"""
    <div style="font-size: 0.75rem; color: #64748b; line-height: 1.5;">
        <strong>Database:</strong> {db_instance.storage_mode}<br>
        <strong>AI Model:</strong> YOLO11 Nano (VinBigData)<br>
        <strong>Doctor Directory:</strong> 2,000 Specialists
    </div>
    """,
    unsafe_allow_html=True
)


# ==============================================================================
# AUTHENTICATION GATEWAY (IF NOT LOGGED IN)
# ==============================================================================
if not user:
    st.markdown(
        """
        <div class="hospital-header">
            <h1 class="hospital-title">Hospital Diagnostic & Specialist Referral Portal</h1>
            <div class="hospital-subtitle">
                Secure clinical access for <strong>Patients</strong>, <strong>Attending Doctors</strong>, and <strong>Diagnostic Laboratories</strong>.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    auth_col1, auth_col2 = st.columns([1.3, 1])

    with auth_col1:
        auth_tab1, auth_tab2 = st.tabs(["🔐 Sign In to Account", "📝 Create New Account"])

        # TAB 1: SIGN IN
        with auth_tab1:
            st.markdown("#### Access Your Portal")
            with st.form("signin_form"):
                role_select = st.selectbox("Select Your Role *", ["Patient", "Doctor", "Laboratory"])
                username_input = st.text_input("Username *", placeholder="e.g. patient_demo or your username")
                password_input = st.text_input("Password *", type="password", placeholder="Enter password")
                signin_submit = st.form_submit_button("Sign In ➔", type="primary", use_container_width=True)

                if signin_submit:
                    if username_input and password_input:
                        auth_user = db_instance.authenticate_user(username_input, password_input, role_select)
                        if auth_user:
                            st.session_state["user_session"] = auth_user
                            st.success(f"Welcome back, {auth_user['full_name']}!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Invalid username, password, or role. Please try again.")
                    else:
                        st.warning("Please fill in all required fields.")

        # TAB 2: SIGN UP
        with auth_tab2:
            st.markdown("#### Register New Account")
            if "reg_reset_count" not in st.session_state:
                st.session_state["reg_reset_count"] = 0
            if "last_reg_msg" in st.session_state and st.session_state["last_reg_msg"]:
                st.success(st.session_state["last_reg_msg"])
                st.session_state["last_reg_msg"] = None

            # Reactive Role Selector (outside form so UI updates instantly per role)
            new_role = st.selectbox(
                "I am registering as *",
                ["Patient", "Doctor", "Laboratory"],
                key=f"role_sel_{st.session_state['reg_reset_count']}"
            )

            r_key = st.session_state["reg_reset_count"]
            with st.form(f"signup_form_{new_role}_{r_key}"):
                c_a, c_b = st.columns(2)
                with c_a:
                    new_username = st.text_input("Username *", key=f"u_{r_key}", placeholder="e.g. john_doe")
                    new_fullname = st.text_input(
                        "Doctor Full Name (e.g. Dr. Name) *" if new_role == "Doctor" else ("Laboratory Name *" if new_role == "Laboratory" else "Patient Full Name *"),
                        key=f"fn_{r_key}"
                    )
                    new_email = st.text_input("Email Address *", key=f"em_{r_key}", placeholder="name@domain.com")
                with c_b:
                    new_password = st.text_input("Password *", type="password", key=f"pw_{r_key}", placeholder="Create password")
                    new_phone = st.text_input("Contact Phone Number *", key=f"ph_{r_key}", placeholder="+91 98765 43210")
                    new_city = st.selectbox("City *", doctor_engine.get_cities(), key=f"ct_{r_key}")

                # Dynamic Role-Specific Extra Fields
                extra_data = {}
                if new_role == "Doctor":
                    c_doc1, c_doc2 = st.columns(2)
                    with c_doc1:
                        doc_spec = st.selectbox("Specialization *", doctor_engine.get_specializations(), key=f"ds_{r_key}")
                        extra_data["specialization"] = doc_spec
                        doc_exp = st.number_input("Years of Clinical Experience", 1, 50, 15, key=f"exp_{r_key}")
                        extra_data["experience_years"] = doc_exp
                    with c_doc2:
                        doc_hosp = st.selectbox("Hospital Network *", doctor_engine.get_hospitals(), key=f"dh_{r_key}")
                        extra_data["hospital"] = doc_hosp
                        doc_fee = st.number_input("Consultation Fee (₹)", 100, 5000, 800, step=50, key=f"fee_{r_key}")
                        extra_data["fees_inr"] = doc_fee
                        extra_data["rating"] = 5.0
                        extra_data["availability"] = "Available"
                elif new_role == "Patient":
                    c_pat1, c_pat2 = st.columns(2)
                    with c_pat1:
                        p_age = st.number_input("Patient Age", 1, 120, 35, key=f"age_{r_key}")
                        extra_data["age"] = p_age
                    with c_pat2:
                        p_gen = st.selectbox("Gender", ["Male", "Female", "Other"], key=f"gen_{r_key}")
                        extra_data["gender"] = p_gen
                elif new_role == "Laboratory":
                    lab_lic = st.text_input("Diagnostic Lab License Number *", value=f"LAB-{new_city[:3].upper()}-2026", key=f"lic_{r_key}")
                    extra_data["license_no"] = lab_lic

                signup_submit = st.form_submit_button(f"Create {new_role} Account ➔", type="primary", use_container_width=True)

                if signup_submit:
                    if new_username and new_password and new_fullname and new_email and new_phone:
                        ok, msg = db_instance.register_user(
                            username=new_username,
                            password=new_password,
                            role=new_role,
                            full_name=new_fullname,
                            email=new_email,
                            phone=new_phone,
                            city=new_city,
                            extra_data=extra_data
                        )
                        if ok:
                            if new_role == "Doctor":
                                doctor_engine.reload()
                            st.session_state["last_reg_msg"] = f"🎉 {new_role} Account '{new_username}' created successfully! Doctor is now live in the recommendation database."
                            st.session_state["reg_reset_count"] += 1
                            st.rerun()
                        else:
                            st.error(msg)
                    else:
                        st.warning("Please complete all required fields (*).")

    with auth_col2:
        st.markdown(
            """
            <div class="hospital-card" style="border-top: 4px solid #0284c7;">
                <h3 style="margin-top: 0; color: #0284c7;">🚀 Quick Demo Logins</h3>
                <div style="font-size: 0.85rem; color: #475569; margin-bottom: 1rem;">
                    Click any pre-seeded role to test the full clinical workflow immediately:
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("🧑‍🦱 Quick Sign In: Patient (Eleanor Vance)", use_container_width=True):
            st.session_state["user_session"] = db_instance.authenticate_user("patient_demo", "patient123")
            st.rerun()

        if st.button("👨‍⚕️ Quick Sign In: Doctor (Dr. Yukti Chauhan)", use_container_width=True):
            st.session_state["user_session"] = db_instance.authenticate_user("doctor_demo", "doctor123")
            st.rerun()

        if st.button("🔬 Quick Sign In: Laboratory (Apex Diagnostic Lab)", use_container_width=True):
            st.session_state["user_session"] = db_instance.authenticate_user("lab_demo", "lab123")
            st.rerun()

        # Display All Newly Registered User Accounts
        all_users = []
        if db_instance.db is not None:
            all_users = list(db_instance.db.users.find({}, {"_id": 0, "password_hash": 0}))

        custom_users = [u for u in all_users if not u.get("username", "").endswith("_demo")]
        if custom_users:
            st.markdown(
                f"""
                <div class="hospital-card" style="margin-top: 15px; border-top: 4px solid #16a34a;">
                    <h4 style="margin-top: 0; color: #15803d;">📋 Your Registered Accounts ({len(custom_users)})</h4>
                    <div style="font-size: 0.82rem; color: #475569; margin-bottom: 0.75rem;">
                        Recently created accounts available in MongoDB:
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            for idx, cu in enumerate(custom_users):
                role_tag = f"<span class='role-badge role-{cu['role'].lower()}'>{cu['role']}</span>"
                st.markdown(
                    f"""
                    <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px 12px; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong style="color: #0f172a;">{cu.get('full_name')}</strong> 
                                <span style="font-size: 0.8rem; color: #64748b;">(@{cu.get('username')})</span>
                            </div>
                            <div>{role_tag}</div>
                        </div>
                        <div style="font-size: 0.78rem; color: #475569; margin-top: 4px;">
                            📍 {cu.get('city', 'N/A')} &nbsp;|&nbsp; 📞 {cu.get('phone', 'N/A')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if st.button(f"⚡ Sign In as @{cu.get('username')}", key=f"quick_u_{idx}", use_container_width=True):
                    st.session_state["user_session"] = cu
                    st.rerun()


# ==============================================================================
# ROLE 1: 🧑‍🦱 PATIENT PORTAL
# ==============================================================================
elif user["role"] == "Patient":
    patient_menu = st.sidebar.radio(
        "Patient Services",
        [
            "🫁 Scan X-ray & Match Specialist",
            "🔍 Search 2,000 Doctors Directory",
            "📅 My Appointments & Confirmations",
            "📁 My Diagnostic Scan Records",
            "👤 My Profile & Personal Info"
        ]
    )

    # --------------------------------------------------------------------------
    # PATIENT TAB 1: SCAN X-RAY & MATCH DOCTOR
    # --------------------------------------------------------------------------
    if patient_menu == "🫁 Scan X-ray & Match Specialist":
        st.markdown(
            """
            <div class="hospital-header">
                <h1 class="hospital-title">Patient Chest Radiograph Screening & Specialist Matching</h1>
                <div class="hospital-subtitle">
                    Upload your chest X-ray for instant YOLO11 AI abnormality detection and verified specialist recommendations.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        detector = get_detector()

        col_input, col_params = st.columns([2.2, 1])
        with col_input:
            st.markdown("#### 1. Upload Chest X-ray")
            in_mode = st.radio("Input Option:", ["📂 Upload Image File", "🔬 Choose Sample Chest Radiograph"], horizontal=True)
            input_image = None
            image_name = "patient_xray.jpg"

            if in_mode == "📂 Upload Image File":
                up_file = st.file_uploader("Upload DICOM/JPEG/PNG Chest X-ray", type=["jpg", "jpeg", "png"])
                if up_file is not None:
                    input_image = Image.open(up_file).convert("RGB")
                    image_name = up_file.name
            else:
                sample_dir = os.path.join(PROJECT_ROOT, "data", "processed", "images", "test")
                if not os.path.exists(sample_dir) or not os.listdir(sample_dir):
                    sample_dir = os.path.join(PROJECT_ROOT, "sample_images")
                if os.path.exists(sample_dir):
                    sample_files = [f for f in os.listdir(sample_dir) if f.endswith((".jpg", ".png", ".jpeg"))][:30]
                    if sample_files:
                        chosen_sample = st.selectbox("Select Test Radiograph:", sample_files)
                        if chosen_sample:
                            input_image = Image.open(os.path.join(sample_dir, chosen_sample)).convert("RGB")
                            image_name = chosen_sample

        with col_params:
            st.markdown("#### 2. Patient Preferences")
            p_city = st.selectbox("Your Location (City):", ["All Cities"] + doctor_engine.get_cities(),
                                  index=doctor_engine.get_cities().index(user.get("city", "Bangalore")) + 1 if user.get("city") in doctor_engine.get_cities() else 0)
            conf_val = st.slider("AI Sensitivity Threshold", 0.05, 0.60, 0.15, 0.05)

        if input_image is not None:
            st.markdown("---")
            if st.button("🚀 Analyze X-ray & Find Specialists", type="primary", use_container_width=True):
                with st.spinner("AI analyzing chest radiograph and matching specialists..."):
                    results = detector.predict(input_image, conf_threshold=conf_val)
                    # Persist scan to MongoDB
                    img_b64 = image_to_base64(Image.fromarray(results["annotated_image_rgb"]))
                    scan_id = db_instance.save_scan_record({
                        "username": user["username"],
                        "user_role": "Patient",
                        "patient_name": user["full_name"],
                        "patient_phone": user.get("phone", ""),
                        "city": p_city,
                        "findings_count": results["findings_count"],
                        "findings": results["detections"],
                        "image_b64": img_b64,
                        "image_name": image_name
                    })
                    st.session_state["patient_current_scan"] = results
                    st.session_state["patient_scan_id"] = scan_id
                    st.session_state["patient_image"] = input_image

            if "patient_current_scan" in st.session_state:
                res = st.session_state["patient_current_scan"]
                ann_img = Image.fromarray(res["annotated_image_rgb"])
                img_b64 = image_to_base64(ann_img)

                st.markdown("### 3. AI Diagnostic Analysis")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("##### 📷 Input Radiograph")
                    st.image(st.session_state["patient_image"], use_container_width=True)
                with c2:
                    st.markdown(f"##### 🎯 AI Localized Detections ({res['findings_count']} Findings)")
                    st.image(ann_img, use_container_width=True)

                if res["detections"]:
                    for f in res["detections"]:
                        st.markdown(render_finding_html(f), unsafe_allow_html=True)
                else:
                    st.success("✅ Normal Radiograph: No focal abnormalities detected.")

                # Doctor recommendations
                st.markdown("---")
                st.markdown("### 4. 🩺 Recommended Medical Specialists")
                rec_res = doctor_engine.recommend_doctors(
                    detected_findings=res.get("detections", []),
                    city_filter=p_city,
                    top_k=6
                )
                st.markdown(render_specialist_match_summary(rec_res), unsafe_allow_html=True)

                docs = rec_res.get("doctors") or rec_res.get("recommended_doctors", [])
                for i in range(0, len(docs), 2):
                    dc1, dc2 = st.columns(2)
                    with dc1:
                        d = docs[i]
                        st.markdown(render_doctor_card_html(d), unsafe_allow_html=True)
                        if st.button(f"📅 Book Consultation with {d['doctor_name']}", key=f"p_book_{i}"):
                            st.session_state["p_selected_doc"] = d
                    if i + 1 < len(docs):
                        with dc2:
                            d2 = docs[i+1]
                            st.markdown(render_doctor_card_html(d2), unsafe_allow_html=True)
                            if st.button(f"📅 Book Consultation with {d2['doctor_name']}", key=f"p_book_{i+1}"):
                                st.session_state["p_selected_doc"] = d2

                # Booking Form Modal
                if "p_selected_doc" in st.session_state:
                    s_doc = st.session_state["p_selected_doc"]
                    st.markdown("---")
                    st.markdown(
                        f"""
                        <div style="background: #f0fdf4; border: 1.5px solid #22c55e; border-radius: 10px; padding: 1.25rem;">
                            <h3 style="margin: 0 0 0.4rem 0; color: #15803d;">📅 Confirm Appointment Request</h3>
                            <div style="font-size: 0.9rem; color: #166534;">
                                Requesting consultation with <strong>{s_doc['doctor_name']}</strong> ({s_doc['specialization']}) at <strong>{s_doc['hospital']}, {s_doc['city']}</strong>.
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    with st.form("p_booking_form"):
                        bk1, bk2 = st.columns(2)
                        with bk1:
                            b_name = st.text_input("Patient Full Name *", value=user["full_name"])
                            b_phone = st.text_input("Contact Phone Number *", value=user.get("phone", ""))
                        with bk2:
                            b_slot = st.selectbox(
                                "Preferred Consultation Slot:",
                                [
                                    "Tomorrow (09:30 AM - 10:30 AM)",
                                    "Tomorrow (02:30 PM - 03:30 PM)",
                                    "Day After Tomorrow (11:00 AM - 12:00 PM)",
                                    "This Saturday (10:00 AM - 11:30 AM)"
                                ]
                            )
                            b_reason = st.text_input("Reason / Indication", value=f"AI Detected: {', '.join(rec_res['target_findings'])}")

                        if st.form_submit_button("Send Appointment Request to Doctor ➔", type="primary", use_container_width=True):
                            apt_record = doctor_engine.book_appointment(
                                patient_name=b_name,
                                patient_phone=b_phone,
                                doctor_name=s_doc["doctor_name"],
                                hospital=s_doc["hospital"],
                                city=s_doc["city"],
                                finding=b_reason,
                                preferred_slot=b_slot,
                                patient_username=user["username"],
                                specialization=s_doc["specialization"],
                                scan_id=st.session_state.get("patient_scan_id")
                            )
                            st.success(f"🎉 Appointment Request Sent! Appointment #{apt_record['appointment_id']} is now pending confirmation from {s_doc['doctor_name']}.")

                # --------------------------------------------------------------
                # SECTION 5: OFFICIAL DIAGNOSTIC CERTIFICATE & CLINICAL REPORT
                # --------------------------------------------------------------
                st.markdown("---")
                st.markdown("### 5. 📄 Official Diagnostic Certificate & Clinical Report")
                
                rep_id = st.session_state.get("patient_scan_id", f"SCN-{int(time.time()*1000)%1000000:06d}")
                pat_info = {
                    "full_name": user.get("full_name", "Anonymous"),
                    "patient_id": user.get("user_id", f"PAT-{user['username'].upper()}"),
                    "age": user.get("age", 45),
                    "gender": user.get("gender", "Male"),
                    "blood_group": user.get("blood_group", "Not Specified"),
                    "phone": user.get("phone", "N/A"),
                    "city": p_city,
                    "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
                }
                
                ref_doc = st.session_state.get("p_selected_doc")
                if not ref_doc and docs:
                    ref_doc = docs[0]  # default to primary recommended specialist

                full_report_html = generate_printable_referral_report_html(
                    report_id=rep_id,
                    patient_info=pat_info,
                    detection_results=res,
                    referred_doctor=ref_doc,
                    annotated_img_b64=img_b64
                )

                rc1, rc2 = st.columns([1.3, 1])
                with rc1:
                    st.download_button(
                        label="📥 Download Official Diagnostic Report (Print / PDF)",
                        data=full_report_html,
                        file_name=f"CliniScan_Report_{rep_id}.html",
                        mime="text/html",
                        type="primary",
                        use_container_width=True,
                        key="dl_main_detection_report"
                    )
                with rc2:
                    st.caption("🖨️ Open the downloaded HTML file in your browser to print or save directly as PDF (**Ctrl + P**).")

                with st.expander("👁️ View Full Diagnostic Report & Official Clinical Certificate", expanded=True):
                    st.components.v1.html(full_report_html, height=760, scrolling=True)

    # --------------------------------------------------------------------------
    # PATIENT TAB 2: SEARCH 2,000 DOCTORS
    # --------------------------------------------------------------------------
    elif patient_menu == "🔍 Search 2,000 Doctors Directory":
        st.markdown(
            """
            <div class="hospital-header">
                <h1 class="hospital-title">Medical Specialist Directory & Hospital Network</h1>
                <div class="hospital-subtitle">
                    Search and book appointments with 2,000+ verified Pulmonologists, Cardiologists, Oncologists, and Physicians across 26 cities.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        dir_tab1, dir_tab2, dir_tab3 = st.tabs([
            "🔍 Search & Book Specialist",
            "📊 Network & Specialty Analytics",
            "➕ Register New Specialist"
        ])

        with dir_tab1:
            sq1, sq2, sq3 = st.columns([2, 1, 1])
            with sq1:
                q_text = st.text_input("🔍 Search by Name, Pathology, Hospital, or City:", placeholder="e.g. Pulmonologist, AIIMS, Effusion, Bangalore...")
            with sq2:
                q_spec = st.selectbox("Specialty:", ["All Specialties"] + doctor_engine.get_specializations())
            with sq3:
                q_city = st.selectbox("City:", ["All Cities"] + doctor_engine.get_cities())

            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                q_hosp = st.selectbox("Hospital Network:", ["All Hospitals"] + doctor_engine.get_hospitals())
            with col_f2:
                q_avail = st.checkbox("Available Specialists Only", value=False)
            with col_f3:
                q_max_fee = st.slider("Max Consultation Fee (₹)", 100, 2000, 2000, 50)

            results = doctor_engine.search_all_doctors(
                query=q_text,
                specialty=q_spec,
                city=q_city,
                hospital=q_hosp,
                available_only=q_avail,
                max_fee=q_max_fee if q_max_fee < 2000 else None
            )
            st.markdown(f"**Found {len(results):,} Doctors Matching Filters:**")

            for i in range(0, min(10, len(results)), 2):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(render_doctor_card_html(results[i]), unsafe_allow_html=True)
                    with st.expander(f"📅 Book Appointment with {results[i]['doctor_name']}"):
                        with st.form(f"book_dir_form_{i}"):
                            b_slot = st.selectbox(
                                "Preferred Slot:",
                                [
                                    "Tomorrow (09:30 AM - 10:30 AM)",
                                    "Tomorrow (02:30 PM - 03:30 PM)",
                                    "Day After Tomorrow (11:00 AM - 12:00 PM)"
                                ],
                                key=f"slot_dir_{i}"
                            )
                            b_reason = st.text_input("Consultation Reason", value="General Clinical Consultation", key=f"reason_dir_{i}")
                            if st.form_submit_button(f"Confirm Appointment with {results[i]['doctor_name']} ➔", type="primary", use_container_width=True):
                                apt_record = doctor_engine.book_appointment(
                                    patient_name=user["full_name"],
                                    patient_phone=user.get("phone", "+91 98765 43210"),
                                    doctor_name=results[i]["doctor_name"],
                                    hospital=results[i]["hospital"],
                                    city=results[i]["city"],
                                    finding=b_reason,
                                    preferred_slot=b_slot,
                                    patient_username=user["username"],
                                    specialization=results[i]["specialization"]
                                )
                                st.success(f"🎉 Appointment #{apt_record['appointment_id']} booked with {results[i]['doctor_name']}! Go to 'My Appointments & Confirmations' tab to track.")
                if i + 1 < len(results):
                    with c2:
                        st.markdown(render_doctor_card_html(results[i+1]), unsafe_allow_html=True)
                        with st.expander(f"📅 Book Appointment with {results[i+1]['doctor_name']}"):
                            with st.form(f"book_dir_form_{i+1}"):
                                b_slot2 = st.selectbox(
                                    "Preferred Slot:",
                                    [
                                        "Tomorrow (09:30 AM - 10:30 AM)",
                                        "Tomorrow (02:30 PM - 03:30 PM)",
                                        "Day After Tomorrow (11:00 AM - 12:00 PM)"
                                    ],
                                    key=f"slot_dir_{i+1}"
                                )
                                b_reason2 = st.text_input("Consultation Reason", value="General Clinical Consultation", key=f"reason_dir_{i+1}")
                                if st.form_submit_button(f"Confirm Appointment with {results[i+1]['doctor_name']} ➔", type="primary", use_container_width=True):
                                    apt_record2 = doctor_engine.book_appointment(
                                        patient_name=user["full_name"],
                                        patient_phone=user.get("phone", "+91 98765 43210"),
                                        doctor_name=results[i+1]["doctor_name"],
                                        hospital=results[i+1]["hospital"],
                                        city=results[i+1]["city"],
                                        finding=b_reason2,
                                        preferred_slot=b_slot2,
                                        patient_username=user["username"],
                                        specialization=results[i+1]["specialization"]
                                    )
                                    st.success(f"🎉 Appointment #{apt_record2['appointment_id']} booked with {results[i+1]['doctor_name']}! Go to 'My Appointments & Confirmations' tab to track.")

        with dir_tab2:
            st.markdown("#### 📊 Clinical Directory & Network Analytics")
            stats = doctor_engine.get_analytics_summary()

            m1, m2, m3, m4 = st.columns(4)
            with m1:
                st.metric("Total Medical Specialists", f"{stats['total_doctors']:,}")
            with m2:
                st.metric("Registered Platform Doctors", f"{stats['registered_doctors']}")
            with m3:
                st.metric("Avg Consultation Fee", f"₹{stats['avg_fees']:,}")
            with m4:
                st.metric("Avg Clinical Experience", f"{stats['avg_experience']} Years")

            st.markdown("---")
            a_col1, a_col2 = st.columns(2)
            with a_col1:
                st.markdown("##### 🩺 Specialists by Department")
                spec_df = pd.DataFrame(list(stats["specialization_counts"].items()), columns=["Specialty", "Count"]).sort_values(by="Count", ascending=False)
                st.bar_chart(spec_df.set_index("Specialty"))

            with a_col2:
                st.markdown("##### 📍 Top Practice Cities")
                top_cities = pd.DataFrame(list(stats["city_counts"].items()), columns=["City", "Doctors"]).sort_values(by="Doctors", ascending=False).head(10)
                st.bar_chart(top_cities.set_index("City"))

        with dir_tab3:
            st.markdown("#### ➕ Register New Specialist Into Healthcare Directory")
            st.caption("Add a new doctor with automatic credential generation and instant synchronization across all recommendation datasets.")

            with st.form("dir_reg_doc_form"):
                rc1, rc2 = st.columns(2)
                with rc1:
                    nd_name = st.text_input("Doctor Full Name *", placeholder="Dr. Rajeshwari Sharma")
                    nd_spec = st.selectbox("Medical Specialization *", doctor_engine.get_specializations())
                    nd_exp = st.number_input("Clinical Experience (Years) *", 1, 50, 15)
                    nd_fee = st.number_input("Consultation Fee (₹) *", 100, 5000, 800, step=50)
                with rc2:
                    nd_hosp = st.selectbox("Hospital Network *", doctor_engine.get_hospitals())
                    nd_city = st.selectbox("City Location *", doctor_engine.get_cities())
                    nd_disease = st.text_input("Disease / Pathology Expertise", placeholder="e.g. Pleural effusion, Pulmonary fibrosis")
                    nd_avail = st.selectbox("Availability *", ["Available", "Busy"])

                with st.expander("🔐 Custom Credentials (Optional)"):
                    nd_uname = st.text_input("Custom Username", placeholder="Leave blank to auto-generate")
                    nd_email = st.text_input("Custom Email", placeholder="Leave blank to auto-generate")
                    nd_pass = st.text_input("Temporary Password", value="Doctor123!", type="password")

                reg_btn = st.form_submit_button("➕ Register Specialist & Sync Network ➔", type="primary", use_container_width=True)

            if reg_btn:
                if not nd_name.strip():
                    st.error("Please enter the Doctor's Full Name.")
                else:
                    ok, msg, new_doc_info = doctor_engine.register_doctor_into_system({
                        "Doctor_Name": nd_name.strip(),
                        "Specialization": nd_spec,
                        "Experience": int(nd_exp),
                        "Fees": int(nd_fee),
                        "Hospital": nd_hosp,
                        "City": nd_city,
                        "Disease": nd_disease.strip() if nd_disease.strip() else nd_spec,
                        "Availability": nd_avail,
                        "username": nd_uname.strip() if nd_uname.strip() else None,
                        "email": nd_email.strip() if nd_email.strip() else None,
                        "password": nd_pass.strip() if nd_pass.strip() else "Doctor123!"
                    })
                    if ok:
                        st.success(f"🎉 Specialist Registered Successfully! ID: `{new_doc_info.get('user_id')}` | Username: `@{new_doc_info.get('username')}`")
                        st.info(f"🔑 **Doctor Login Credentials:** Username: `@{new_doc_info.get('username')}` | Password: `{new_doc_info.get('password')}` | Email: `{new_doc_info.get('email')}`")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"Error registering doctor: {msg}")

    # --------------------------------------------------------------------------
    # PATIENT TAB 3: MY APPOINTMENTS & CONFIRMATIONS
    # --------------------------------------------------------------------------
    elif patient_menu == "📅 My Appointments & Confirmations":
        st.markdown(
            """
            <div class="hospital-header">
                <h1 class="hospital-title">My Appointments & Referrals</h1>
                <div class="hospital-subtitle">
                    Track live confirmation status from your attending specialist and download official referral certificates.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        apts = db_instance.get_patient_appointments(user["username"])
        if apts:
            st.markdown(f"**You have {len(apts)} appointment records:**")
            for idx, a in enumerate(apts):
                st.markdown(render_appointment_card_html(a, user_role="Patient"), unsafe_allow_html=True)
                if a.get("status") == "Confirmed":
                    ref_html = generate_printable_referral_report_html(
                        report_id=a.get("appointment_id", "APT-001"),
                        patient_info={
                            "full_name": a.get("patient_name", user["full_name"]),
                            "patient_id": f"PAT-{user['username'].upper()}",
                            "age": user.get("age", 45),
                            "gender": user.get("gender", "N/A"),
                            "city": a.get("city", "Bangalore"),
                            "timestamp": a.get("doctor_confirmed_at", a.get("created_at", "N/A"))
                        },
                        detection_results={"detections": [], "model_version": "CliniScan-YOLO11-v1"},
                        referred_doctor={
                            "doctor_name": a.get("doctor_name"),
                            "specialization": a.get("specialization", "Specialist"),
                            "hospital": a.get("hospital", "AIIMS"),
                            "city": a.get("city", "Bangalore"),
                            "fees_inr": 800,
                            "disease_expertise": a.get("clinical_indication", "Respiratory Consult")
                        },
                        doctor_notes=a.get("doctor_notes", "Confirmed consultation.")
                    )
                    st.download_button(
                        label=f"📥 Download Confirmed Referral Pass ({a.get('doctor_name')})",
                        data=ref_html,
                        file_name=f"Referral_{a.get('appointment_id')}.html",
                        mime="text/html",
                        key=f"dl_ref_{idx}"
                    )
        else:
            st.info("You haven't booked any appointments yet. Scan an X-ray or search doctors to book a consultation.")

    # --------------------------------------------------------------------------
    # PATIENT TAB 4: SCAN RECORDS & HISTORICAL REPORTS
    # --------------------------------------------------------------------------
    elif patient_menu == "📁 My Diagnostic Scan Records":
        st.markdown(
            """
            <div class="hospital-header">
                <h1 class="hospital-title">My Diagnostic X-ray Scan History & Reports</h1>
                <div class="hospital-subtitle">
                    Archived chest radiograph scans, localized AI findings, and official clinical certificates.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        scans = db_instance.get_user_scans(user["username"])
        if scans:
            st.markdown(f"**Total Scans on File:** {len(scans)}")
            for idx, s in enumerate(scans):
                s_id = s.get("scan_id", f"SCN-{idx:04d}")
                s_time = s.get("timestamp", "N/A")
                f_count = s.get("findings_count", 0)
                findings = s.get("findings", [])
                img_b64 = s.get("image_b64")

                # Format finding tags
                finding_tags = ""
                if findings:
                    for f in findings:
                        f_name = f.get("class_name", "Finding")
                        f_conf = f.get("confidence_pct", "")
                        f_sev = f.get("severity", "Moderate")
                        badge_color = "#ef4444" if f_sev in ["Critical", "High"] else "#f59e0b"
                        finding_tags += f'<span style="background: #fee2e2; color: {badge_color}; padding: 3px 8px; border-radius: 4px; font-size: 0.78rem; font-weight: 700; margin-right: 6px; border: 1px solid #fca5a5;">{f_name} ({f_conf})</span>'
                else:
                    finding_tags = '<span style="background: #dcfce7; color: #15803d; padding: 3px 8px; border-radius: 4px; font-size: 0.78rem; font-weight: 700; border: 1px solid #86efac;">Normal Radiograph (No findings)</span>'

                st.markdown(
                    f"""
                    <div class="hospital-card" style="margin-bottom: 0.75rem;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h4 style="margin: 0; color: #0284c7;">Radiograph Scan #{s_id}</h4>
                            <span style="font-size: 0.8rem; color: #64748b;">📅 {s_time}</span>
                        </div>
                        <div style="margin-top: 8px; font-size: 0.88rem;">
                            <strong>AI Detections ({f_count}):</strong> {finding_tags}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # Generate full printable report for this past scan
                pat_info = {
                    "full_name": s.get("patient_name") or user.get("full_name", "Anonymous"),
                    "patient_id": s.get("user_id") or user.get("user_id", f"PAT-{user['username'].upper()}"),
                    "age": s.get("age") or user.get("age", 45),
                    "gender": s.get("gender") or user.get("gender", "Male"),
                    "blood_group": user.get("blood_group", "Not Specified"),
                    "phone": s.get("patient_phone") or user.get("phone", "N/A"),
                    "city": s.get("city") or user.get("city", "Bangalore"),
                    "timestamp": s_time
                }
                scan_rep_html = generate_printable_referral_report_html(
                    report_id=s_id,
                    patient_info=pat_info,
                    detection_results={"detections": findings},
                    annotated_img_b64=img_b64
                )

                b_col1, b_col2 = st.columns([1.2, 1.8])
                with b_col1:
                    st.download_button(
                        label=f"📥 Download Report #{s_id}",
                        data=scan_rep_html,
                        file_name=f"Diagnostic_Report_{s_id}.html",
                        mime="text/html",
                        key=f"dl_scan_rep_{idx}_{s_id}",
                        type="secondary",
                        use_container_width=True
                    )
                with b_col2:
                    with st.expander(f"👁️ View Scan #{s_id} Full Diagnostic Report & Certificate"):
                        st.components.v1.html(scan_rep_html, height=650, scrolling=True)
                st.markdown("<div style='margin-bottom: 1.25rem;'></div>", unsafe_allow_html=True)
        else:
            st.info("No scan history recorded for this account. Upload and scan a chest X-ray to generate your first diagnostic report.")

    # --------------------------------------------------------------------------
    # PATIENT TAB 5: MY PROFILE & PERSONAL INFO
    # --------------------------------------------------------------------------
    elif patient_menu == "👤 My Profile & Personal Info":
        st.markdown(
            """
            <div class="hospital-header">
                <h1 class="hospital-title">My Personal Profile & Health Account Settings</h1>
                <div class="hospital-subtitle">
                    Update your personal coordinates, emergency contact details, health metrics, and account security.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        all_cities = doctor_engine.get_cities()
        user_city = user.get("city", "Bangalore")
        city_idx = all_cities.index(user_city) if user_city in all_cities else 0

        col_form, col_card = st.columns([1.35, 1])

        with col_form:
            st.markdown("#### ✏️ Edit Personal Information")
            with st.form("patient_edit_profile_form"):
                c1, c2 = st.columns(2)
                with c1:
                    p_name = st.text_input("Full Name *", value=user.get("full_name", ""))
                    p_email = st.text_input("Email Address *", value=user.get("email", ""))
                    p_age = st.number_input("Age (Years) *", min_value=1, max_value=120, value=int(user.get("age", 35)))
                    p_blood = st.selectbox(
                        "Blood Group",
                        ["Not Specified", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"],
                        index=["Not Specified", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].index(user.get("blood_group", "Not Specified")) if user.get("blood_group") in ["Not Specified", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"] else 0
                    )
                with c2:
                    p_phone = st.text_input("Contact Phone Number *", value=user.get("phone", ""))
                    p_city = st.selectbox("City Location *", all_cities, index=city_idx)
                    p_gen = st.selectbox(
                        "Gender *",
                        ["Male", "Female", "Other"],
                        index=["Male", "Female", "Other"].index(user.get("gender", "Male")) if user.get("gender") in ["Male", "Female", "Other"] else 0
                    )
                    p_emer = st.text_input("Emergency Contact Phone", value=user.get("emergency_contact", ""), placeholder="+91 99887 76655")

                with st.expander("🔐 Security & Password Update (Optional)"):
                    st.caption("Leave blank to keep your current password.")
                    new_pw = st.text_input("New Password", type="password", placeholder="Enter new password")
                    confirm_pw = st.text_input("Confirm New Password", type="password", placeholder="Confirm new password")

                save_submit = st.form_submit_button("💾 Save Profile Changes ➔", type="primary", use_container_width=True)

            if save_submit:
                if not p_name.strip() or not p_email.strip() or not p_phone.strip():
                    st.error("Please fill in all mandatory fields (Name, Email, Phone).")
                elif new_pw and new_pw != confirm_pw:
                    st.error("❌ New password and confirmation do not match.")
                else:
                    updates = {
                        "full_name": p_name.strip(),
                        "email": p_email.strip(),
                        "phone": p_phone.strip(),
                        "city": p_city,
                        "age": int(p_age),
                        "gender": p_gen,
                        "blood_group": p_blood,
                        "emergency_contact": p_emer.strip()
                    }
                    ok, msg, updated_u = db_instance.update_user_profile(
                        username=user["username"],
                        updates=updates,
                        new_password=new_pw.strip() if new_pw else None
                    )
                    if ok:
                        st.session_state["user_session"] = updated_u
                        st.success("🎉 Your personal profile has been updated successfully!")
                        time.sleep(0.4)
                        st.rerun()
                    else:
                        st.error(f"Error updating profile: {msg}")

        with col_card:
            st.markdown("#### 🪪 Digital Patient Health ID")
            st.markdown(render_patient_id_card_html(user), unsafe_allow_html=True)


# ==============================================================================
# ROLE 2: 👨‍⚕️ DOCTOR PORTAL
# ==============================================================================
elif user["role"] == "Doctor":
    doc_menu = st.sidebar.radio(
        "Doctor Portal Navigation",
        [
            "📥 Patient Appointment Requests & Confirmation Queue",
            "🫁 Clinical Radiograph Diagnostic Studio",
            "👥 Confirmed Patient Roster",
            "👤 Doctor Profile & Practice Settings"
        ]
    )

    # --------------------------------------------------------------------------
    # DOCTOR TAB 1: APPOINTMENT REQUESTS & CONFIRMATION
    # --------------------------------------------------------------------------
    if doc_menu == "📥 Patient Appointment Requests & Confirmation Queue":
        st.markdown(
            """
            <div class="hospital-header">
                <h1 class="hospital-title">Doctor Appointment Review & Confirmation Queue</h1>
                <div class="hospital-subtitle">
                    Review incoming patient consultation requests, inspect radiographic findings, and confirm appointments with clinical notes.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Demo Mode Queue Selector
        q_filter = st.radio(
            "Appointment Queue Mode:",
            [
                "🌐 All Hospital Patient Bookings (Demo Mode - Shows all appointments)",
                f"🩺 Assigned to {active_doctor_name} Only"
            ],
            horizontal=True
        )

        if "All Hospital" in q_filter:
            doctor_apts = db_instance.get_all_appointments() if hasattr(db_instance, "get_all_appointments") else db_instance.get_doctor_appointments()
        else:
            doctor_apts = db_instance.get_doctor_appointments(doctor_name=active_doctor_name)

        pending_apts = [a for a in doctor_apts if a.get("status") == "Pending"]
        confirmed_apts = [a for a in doctor_apts if a.get("status") == "Confirmed"]

        c_stat1, c_stat2 = st.columns(2)
        with c_stat1:
            st.markdown(
                f"""
                <div class="metric-box" style="border-left: 4px solid #f59e0b;">
                    <div class="metric-value" style="color: #b45309;">{len(pending_apts)}</div>
                    <div class="metric-label">Pending Review Requests</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with c_stat2:
            st.markdown(
                f"""
                <div class="metric-box" style="border-left: 4px solid #16a34a;">
                    <div class="metric-value" style="color: #15803d;">{len(confirmed_apts)}</div>
                    <div class="metric-label">Confirmed Appointments</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("### 📋 Pending Patient Requests Requiring Confirmation")

        if pending_apts:
            for apt in pending_apts:
                st.markdown(render_appointment_card_html(apt, user_role="Doctor"), unsafe_allow_html=True)
                
                target_doc = apt.get("doctor_name") or active_doctor_name

                # Direct Confirmation & Custom Prescription Controls
                act_col1, act_col2 = st.columns([1.1, 1.9])
                with act_col1:
                    if st.button(f"⚡ 1-Click Confirm as {target_doc}", key=f"quick_conf_{apt['appointment_id']}", type="primary", use_container_width=True):
                        ok = db_instance.confirm_appointment(
                            appointment_id=apt["appointment_id"],
                            doctor_name=target_doc,
                            doctor_notes="Confirmed by attending specialist. Please bring previous chest radiographs and report for physical examination.",
                            status="Confirmed"
                        )
                        if ok:
                            st.success(f"🎉 Appointment #{apt['appointment_id']} Confirmed as {target_doc}!")
                            time.sleep(0.4)
                            st.rerun()
                with act_col2:
                    with st.expander(f"📝 Custom Prescription & Clinical Notes"):
                        st.markdown(f"**Appointed Doctor:** {apt.get('doctor_name')} ({apt.get('specialization', 'Specialist')}) | 🏥 {apt.get('hospital')}, {apt.get('city')}")
                        st.markdown(f"**Clinical Indication:** `{apt.get('clinical_indication')}` | 📅 **Slot:** `{apt.get('appointment_slot')}`")
                        
                        doc_notes = st.text_area(
                            "Attending Physician Clinical Notes / Prescription:",
                            value="Confirmed. Please bring previous chest radiographs and report for physical consultation.",
                            key=f"notes_{apt['appointment_id']}"
                        )
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button(f"✅ Save Notes & Confirm", key=f"conf_btn_{apt['appointment_id']}", type="primary", use_container_width=True):
                                ok = db_instance.confirm_appointment(apt["appointment_id"], target_doc, doc_notes, "Confirmed")
                                if ok:
                                    st.success(f"Appointment #{apt['appointment_id']} confirmed with notes!")
                                    time.sleep(0.4)
                                    st.rerun()
                        with btn_col2:
                            if st.button(f"❌ Decline Request", key=f"dec_btn_{apt['appointment_id']}", use_container_width=True):
                                db_instance.confirm_appointment(apt["appointment_id"], target_doc, "Doctor unavailable at this slot.", "Declined")
                                st.warning("Appointment request declined.")
                                time.sleep(0.4)
                                st.rerun()
        else:
            st.success("🎉 All incoming appointment requests are up to date! No pending reviews.")

    # --------------------------------------------------------------------------
    # DOCTOR TAB 2: RADIOGRAPH STUDIO
    # --------------------------------------------------------------------------
    elif doc_menu == "🫁 Clinical Radiograph Diagnostic Studio":
        st.markdown(
            """
            <div class="hospital-header">
                <h1 class="hospital-title">Clinical Radiograph Diagnostic Studio</h1>
                <div class="hospital-subtitle">
                    High-resolution YOLO11 deep-learning triage with anatomical quadrant mapping.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        detector = get_detector()
        up_xray = st.file_uploader("Upload Patient Radiograph", type=["jpg", "png", "jpeg"])
        conf = st.slider("Diagnostic Confidence Threshold", 0.05, 0.70, 0.15, 0.05)

        if up_xray is not None:
            img = Image.open(up_xray).convert("RGB")
            if st.button("Run Diagnostic Triage", type="primary", use_container_width=True):
                with st.spinner("Analyzing radiograph..."):
                    res = detector.predict(img, conf_threshold=conf)
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("#### Input X-ray")
                        st.image(img, use_container_width=True)
                    with c2:
                        st.markdown(f"#### YOLO11 Detections ({res['findings_count']} Findings)")
                        st.image(res["annotated_image_rgb"], use_container_width=True)

                    if res["detections"]:
                        for f in res["detections"]:
                            st.markdown(render_finding_html(f), unsafe_allow_html=True)
                    else:
                        st.success("✅ Normal Radiograph: No focal abnormalities detected.")

                    # Doctor Diagnostic Report Generator
                    st.markdown("---")
                    st.markdown("### 📄 Clinical Diagnostic Certificate & Prescription")
                    doc_pinfo = {
                        "full_name": "Hospital Clinical Patient",
                        "patient_id": f"PAT-RAD-{int(time.time()*1000)%1000000:06d}",
                        "age": 48,
                        "gender": "Clinical Case",
                        "city": user.get("city", "Bangalore"),
                        "timestamp": datetime.now().strftime("%d %b %Y, %I:%M %p")
                    }
                    doc_rep_html = generate_printable_referral_report_html(
                        report_id=f"DOC-RAD-{int(time.time()*1000)%1000000:06d}",
                        patient_info=doc_pinfo,
                        detection_results=res,
                        referred_doctor={
                            "doctor_name": active_doctor_name,
                            "specialization": user.get("specialization", "Pulmonologist"),
                            "hospital": user.get("hospital", "AIIMS"),
                            "city": user.get("city", "Bangalore"),
                            "fees_inr": user.get("fees_inr", 800),
                            "disease_expertise": user.get("disease_expertise", "Specialist Review")
                        },
                        annotated_img_b64=image_to_base64(Image.fromarray(res["annotated_image_rgb"])),
                        doctor_notes="Clinical radiograph reviewed by attending specialist. Recommended follow-up and physiological assessment."
                    )
                    
                    d_col1, d_col2 = st.columns([1.2, 1.8])
                    with d_col1:
                        st.download_button(
                            label="📥 Download Doctor-Signed Clinical Report (HTML / PDF)",
                            data=doc_rep_html,
                            file_name=f"Clinical_Report_{active_doctor_name.replace(' ', '_')}.html",
                            mime="text/html",
                            type="primary",
                            use_container_width=True
                        )
                    with d_col2:
                        with st.expander("👁️ View Full Doctor Diagnostic Certificate"):
                            st.components.v1.html(doc_rep_html, height=650, scrolling=True)

    # --------------------------------------------------------------------------
    # DOCTOR TAB 3: CONFIRMED PATIENTS
    # --------------------------------------------------------------------------
    elif doc_menu == "👥 Confirmed Patient Roster":
        st.markdown(
            """
            <div class="hospital-header">
                <h1 class="hospital-title">Confirmed Patient Consultation Roster</h1>
                <div class="hospital-subtitle">
                    List of all patient appointments approved and confirmed by your department.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        doctor_apts = db_instance.get_doctor_appointments(doctor_name=active_doctor_name)
        confirmed_apts = [a for a in doctor_apts if a.get("status") == "Confirmed"]

        if confirmed_apts:
            for ca in confirmed_apts:
                st.markdown(render_appointment_card_html(ca, user_role="Doctor"), unsafe_allow_html=True)
        else:
            st.info("No confirmed appointments on file yet.")

    # --------------------------------------------------------------------------
    # DOCTOR TAB 4: DOCTOR PROFILE & PRACTICE SETTINGS
    # --------------------------------------------------------------------------
    elif doc_menu == "👤 Doctor Profile & Practice Settings":
        st.markdown(
            """
            <div class="hospital-header">
                <h1 class="hospital-title">Doctor Practice Profile & Clinical Settings</h1>
                <div class="hospital-subtitle">
                    Update your professional profile, medical specialization, hospital network, fees, and patient availability.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        all_cities = doctor_engine.get_cities()
        user_city = user.get("city", "Bangalore")
        city_idx = all_cities.index(user_city) if user_city in all_cities else 0

        all_specs = doctor_engine.get_specializations()
        user_spec = user.get("specialization", "Pulmonologist")
        spec_idx = all_specs.index(user_spec) if user_spec in all_specs else 0

        all_hosps = doctor_engine.get_hospitals()
        user_hosp = user.get("hospital", "AIIMS")
        hosp_idx = all_hosps.index(user_hosp) if user_hosp in all_hosps else 0

        user_avail = user.get("availability", "Available")
        avail_idx = 0 if user_avail == "Available" else 1

        col_doc_form, col_doc_card = st.columns([1.35, 1])

        with col_doc_form:
            st.markdown("#### ✏️ Edit Clinical Practice Information")
            with st.form("doctor_edit_profile_form"):
                c1, c2 = st.columns(2)
                with c1:
                    d_name = st.text_input("Doctor Full Name (with Title) *", value=user.get("full_name", ""))
                    d_email = st.text_input("Official Medical Email *", value=user.get("email", ""))
                    d_spec = st.selectbox("Specialization *", all_specs, index=spec_idx)
                    d_exp = st.number_input("Years of Clinical Experience *", min_value=1, max_value=60, value=int(user.get("experience_years", 15)))
                    d_fee = st.number_input("Consultation Fee (₹) *", min_value=100, max_value=5000, value=int(user.get("fees_inr", 800)), step=50)
                with c2:
                    d_phone = st.text_input("Direct Contact Number *", value=user.get("phone", ""))
                    d_city = st.selectbox("Practice City Location *", all_cities, index=city_idx)
                    d_hosp = st.selectbox("Hospital Network *", all_hosps, index=hosp_idx)
                    d_disease = st.text_input("Sub-specialty / Disease Expertise", value=user.get("disease_expertise", user_spec))
                    d_avail = st.selectbox("Current Availability Status *", ["Available", "Busy"], index=avail_idx)

                with st.expander("🔐 Security & Password Update (Optional)"):
                    st.caption("Leave blank to keep your current password.")
                    new_pw = st.text_input("New Password", type="password", placeholder="Enter new password")
                    confirm_pw = st.text_input("Confirm New Password", type="password", placeholder="Confirm new password")

                doc_save_submit = st.form_submit_button("💾 Save Doctor Practice Profile ➔", type="primary", use_container_width=True)

            if doc_save_submit:
                if not d_name.strip() or not d_email.strip() or not d_phone.strip():
                    st.error("Please fill in all required fields (Name, Email, Phone).")
                elif new_pw and new_pw != confirm_pw:
                    st.error("❌ New password and confirmation do not match.")
                else:
                    clean_dname = d_name.strip()
                    if not clean_dname.startswith("Dr. "):
                        clean_dname = f"Dr. {clean_dname}"

                    updates = {
                        "full_name": clean_dname,
                        "email": d_email.strip(),
                        "phone": d_phone.strip(),
                        "city": d_city,
                        "specialization": d_spec,
                        "hospital": d_hosp,
                        "experience_years": int(d_exp),
                        "fees_inr": int(d_fee),
                        "disease_expertise": d_disease.strip() if d_disease.strip() else d_spec,
                        "availability": d_avail
                    }
                    ok, msg, updated_u = db_instance.update_user_profile(
                        username=user["username"],
                        updates=updates,
                        new_password=new_pw.strip() if new_pw else None
                    )
                    if ok:
                        st.session_state["user_session"] = updated_u
                        st.success("🎉 Your doctor profile and live recommendation credentials have been updated successfully!")
                        time.sleep(0.4)
                        st.rerun()
                    else:
                        st.error(f"Error updating profile: {msg}")

        with col_doc_card:
            st.markdown("#### 🪪 Live Specialist Profile Preview")
            preview_doc = {
                "doctor_name": user.get("full_name", "Dr. Specialist"),
                "specialization": user.get("specialization", "Specialist"),
                "disease_expertise": user.get("disease_expertise", user.get("specialization", "General")),
                "hospital": user.get("hospital", "AIIMS"),
                "city": user.get("city", "Bangalore"),
                "rating": float(user.get("rating", 5.0)),
                "experience_years": int(user.get("experience_years", 15)),
                "fees_inr": int(user.get("fees_inr", 800)),
                "availability": user.get("availability", "Available"),
                "is_registered": True,
                "is_exact_match": True
            }
            st.markdown(render_doctor_card_html(preview_doc), unsafe_allow_html=True)
            
            st.markdown(
                f"""<div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 12px; margin-top: 10px; font-size: 0.84rem; color: #475569;">
<div><strong>User ID:</strong> <code>{user.get('user_id', f"DOC-{user['username'].upper()}")}</code></div>
<div style="margin-top: 4px;"><strong>Username:</strong> <code>@{user.get('username')}</code></div>
<div style="margin-top: 4px;"><strong>Medical Email:</strong> {user.get('email')}</div>
<div style="margin-top: 4px;"><strong>Direct Line:</strong> {user.get('phone')}</div>
</div>""",
                unsafe_allow_html=True
            )


# ==============================================================================
# ROLE 3: 🔬 LABORATORY DIAGNOSTIC PORTAL
# ==============================================================================
elif user["role"] == "Laboratory":
    lab_menu = st.sidebar.radio(
        "Laboratory Services",
        [
            "🧪 Patient Intake & AI X-ray Processing",
            "🩺 Specialist Doctor Referral",
            "📊 Processed Lab Test Registry",
            "👤 Lab Profile & Facility Settings"
        ]
    )

    detector = get_detector()

    # --------------------------------------------------------------------------
    # LAB TAB 1: INTAKE & AI PROCESSING
    # --------------------------------------------------------------------------
    if lab_menu == "🧪 Patient Intake & AI X-ray Processing":
        st.markdown(
            """
            <div class="hospital-header">
                <h1 class="hospital-title">Diagnostic Laboratory Intake & AI Triage</h1>
                <div class="hospital-subtitle">
                    Process patient chest radiographs, execute automated YOLO11 abnormality detection, and generate diagnostic certificates.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        col_pat, col_img = st.columns([1, 1.2])

        with col_pat:
            st.markdown("#### 1. Patient Registration Data")
            l_pname = st.text_input("Patient Full Name *", value="Arthur Pendelton")
            l_pid = st.text_input("Patient MRN / Lab ID *", value="LAB-PAT-8812")
            l_age = st.number_input("Age", 1, 120, 52)
            l_gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            l_city = st.selectbox("Patient City", doctor_engine.get_cities())
            l_ref = st.text_input("Referring Physician / Clinic", value="St. Jude Respiratory Clinic")

        with col_img:
            st.markdown("#### 2. Chest Radiograph Intake")
            lab_upload = st.file_uploader("Upload Patient DICOM/JPEG/PNG Image", type=["jpg", "png", "jpeg"])
            lab_conf = st.slider("AI Sensitivity Threshold", 0.05, 0.60, 0.15, 0.05)

        if lab_upload is not None:
            l_image = Image.open(lab_upload).convert("RGB")
            st.markdown("---")
            if st.button("🔬 Execute YOLO11 Lab Scan & Generate Certificate", type="primary", use_container_width=True):
                with st.spinner("Processing laboratory scan..."):
                    lab_res = detector.predict(l_image, conf_threshold=lab_conf)
                    b64_str = image_to_base64(Image.fromarray(lab_res["annotated_image_rgb"]))
                    
                    # Save to MongoDB
                    scan_id = db_instance.save_scan_record({
                        "username": user["username"],
                        "user_role": "Laboratory",
                        "lab_name": user["full_name"],
                        "patient_name": l_pname,
                        "patient_id": l_pid,
                        "age": l_age,
                        "gender": l_gender,
                        "city": l_city,
                        "findings_count": lab_res["findings_count"],
                        "findings": lab_res["detections"],
                        "image_b64": b64_str
                    })
                    st.session_state["lab_scan_res"] = lab_res
                    st.session_state["lab_patient_info"] = {
                        "full_name": l_pname,
                        "patient_id": l_pid,
                        "age": l_age,
                        "gender": l_gender,
                        "city": l_city,
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    st.session_state["lab_scan_id"] = scan_id

            if "lab_scan_res" in st.session_state:
                lres = st.session_state["lab_scan_res"]
                pinfo = st.session_state["lab_patient_info"]

                st.markdown("### 3. Laboratory Triage Findings")
                c1, c2 = st.columns(2)
                with c1:
                    st.image(l_image, caption="Input Patient Radiograph", use_container_width=True)
                with c2:
                    st.image(lres["annotated_image_rgb"], caption=f"YOLO11 Detections ({lres['findings_count']} Findings)", use_container_width=True)

                if lres["detections"]:
                    for f in lres["detections"]:
                        st.markdown(render_finding_html(f), unsafe_allow_html=True)
                else:
                    st.success("✅ Clear Scan: No abnormal findings detected.")

                # Download certificate
                rep_html = generate_printable_referral_report_html(
                    report_id=st.session_state["lab_scan_id"],
                    patient_info=pinfo,
                    detection_results=lres,
                    annotated_img_b64=image_to_base64(Image.fromarray(lres["annotated_image_rgb"]))
                )
                st.download_button("📥 Download Official Lab Certificate (HTML)", rep_html, f"Lab_Report_{l_pid}.html", "text/html", type="primary")

    # --------------------------------------------------------------------------
    # LAB TAB 2: SPECIALIST REFERRAL
    # --------------------------------------------------------------------------
    elif lab_menu == "🩺 Specialist Doctor Referral":
        st.markdown(
            """
            <div class="hospital-header">
                <h1 class="hospital-title">Route Patient to Specialist Network</h1>
                <div class="hospital-subtitle">
                    Assign patient diagnostic findings directly to verified specialists in the hospital network.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if "lab_scan_res" not in st.session_state:
            st.info("Please process a patient scan in the 'Patient Intake' tab first.")
        else:
            lres = st.session_state["lab_scan_res"]
            pinfo = st.session_state["lab_patient_info"]

            recs = doctor_engine.recommend_doctors(
                detected_findings=lres.get("detections", []),
                city_filter=pinfo.get("city", "Bangalore"),
                top_k=6
            )
            st.markdown(render_specialist_match_summary(recs), unsafe_allow_html=True)

            for d in (recs.get("doctors") or recs.get("recommended_doctors", []))[:4]:
                st.markdown(render_doctor_card_html(d), unsafe_allow_html=True)
                if st.button(f"Route Referral to {d['doctor_name']}", key=f"lab_ref_{d['doctor_name']}"):
                    db_instance.create_appointment({
                        "patient_username": f"pat_{pinfo['patient_id'].lower()}",
                        "patient_name": pinfo["full_name"],
                        "patient_phone": "Lab Referral",
                        "doctor_name": d["doctor_name"],
                        "specialization": d["specialization"],
                        "hospital": d["hospital"],
                        "city": d["city"],
                        "clinical_indication": f"Lab Referral ({', '.join(recs['target_findings'])})",
                        "appointment_slot": "Priority Diagnostic Referral",
                        "status": "Pending"
                    })
                    st.success(f"Referral successfully routed to {d['doctor_name']} at {d['hospital']}!")

    # --------------------------------------------------------------------------
    # LAB TAB 3: REGISTRY
    # --------------------------------------------------------------------------
    elif lab_menu == "📊 Processed Lab Test Registry":
        st.markdown(
            """
            <div class="hospital-header">
                <h1 class="hospital-title">Laboratory Diagnostic Registry</h1>
                <div class="hospital-subtitle">
                    Complete history of processed patient radiographs and AI triage records.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        lab_scans = db_instance.get_user_scans(user["username"])
        if lab_scans:
            st.markdown(f"**Total Processed Tests: {len(lab_scans)}**")
            for ls in lab_scans:
                st.markdown(
                    f"""
                    <div class="hospital-card">
                        <div style="display: flex; justify-content: space-between;">
                            <strong>Patient: {ls.get('patient_name')} ({ls.get('patient_id')})</strong>
                            <span style="font-size: 0.8rem; color: #64748b;">{ls.get('timestamp', 'N/A')}</span>
                        </div>
                        <div style="font-size: 0.88rem; color: #334155; margin-top: 4px;">
                            <strong>Findings Count:</strong> {ls.get('findings_count', 0)} &nbsp;|&nbsp; <strong>City:</strong> {ls.get('city', 'N/A')}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No laboratory scans on record yet.")

    # --------------------------------------------------------------------------
    # LAB TAB 4: LAB PROFILE & FACILITY SETTINGS
    # --------------------------------------------------------------------------
    elif lab_menu == "👤 Lab Profile & Facility Settings":
        st.markdown(
            """
            <div class="hospital-header">
                <h1 class="hospital-title">Laboratory Facility Profile & Accreditation Settings</h1>
                <div class="hospital-subtitle">
                    Manage diagnostic center credentials, license registrations, location coordinates, and facility details.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        all_cities = doctor_engine.get_cities()
        user_city = user.get("city", "Bangalore")
        city_idx = all_cities.index(user_city) if user_city in all_cities else 0

        col_lab_form, col_lab_card = st.columns([1.35, 1])

        with col_lab_form:
            st.markdown("#### ✏️ Edit Diagnostic Facility Information")
            with st.form("lab_edit_profile_form"):
                c1, c2 = st.columns(2)
                with c1:
                    l_name = st.text_input("Diagnostic Lab / Center Name *", value=user.get("full_name", ""))
                    l_email = st.text_input("Official Laboratory Email *", value=user.get("email", ""))
                    l_lic = st.text_input("License / Accreditation Number *", value=user.get("license_no", f"LAB-{user_city[:3].upper()}-2026"))
                with c2:
                    l_phone = st.text_input("Contact Phone Number *", value=user.get("phone", ""))
                    l_city = st.selectbox("Facility City *", all_cities, index=city_idx)
                    l_lead = st.text_input("Lead Radiologist / Lab Director", value=user.get("lead_radiologist", "Dr. Lead Consultant"))

                with st.expander("🔐 Security & Password Update (Optional)"):
                    st.caption("Leave blank to keep your current password.")
                    new_pw = st.text_input("New Password", type="password", placeholder="Enter new password")
                    confirm_pw = st.text_input("Confirm New Password", type="password", placeholder="Confirm new password")

                lab_save_submit = st.form_submit_button("💾 Save Laboratory Profile ➔", type="primary", use_container_width=True)

            if lab_save_submit:
                if not l_name.strip() or not l_email.strip() or not l_phone.strip() or not l_lic.strip():
                    st.error("Please fill in all mandatory fields (Name, Email, Phone, License).")
                elif new_pw and new_pw != confirm_pw:
                    st.error("❌ New password and confirmation do not match.")
                else:
                    updates = {
                        "full_name": l_name.strip(),
                        "email": l_email.strip(),
                        "phone": l_phone.strip(),
                        "city": l_city,
                        "license_no": l_lic.strip(),
                        "lead_radiologist": l_lead.strip()
                    }
                    ok, msg, updated_u = db_instance.update_user_profile(
                        username=user["username"],
                        updates=updates,
                        new_password=new_pw.strip() if new_pw else None
                    )
                    if ok:
                        st.session_state["user_session"] = updated_u
                        st.success("🎉 Laboratory profile and facility credentials updated successfully!")
                        time.sleep(0.4)
                        st.rerun()
                    else:
                        st.error(f"Error updating profile: {msg}")

        with col_lab_card:
            st.markdown("#### 🪪 Laboratory Accreditation Pass")
            st.markdown(render_lab_id_card_html(user), unsafe_allow_html=True)

