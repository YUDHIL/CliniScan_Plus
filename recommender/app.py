import os
import re
import json
import pandas as pd
import streamlit as st
try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False
from datetime import datetime

# Configure page settings
st.set_page_config(
    page_title="Doctor Portal & Database Manager",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for modern styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    .main-header {
        background: linear-gradient(135deg, #1e1b4b 0%, #0f172a 100%);
        padding: 1.75rem 2rem;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    
    .main-header h1 {
        color: #f8fafc;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 0;
        background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .main-header p {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-top: 0.4rem;
        margin-bottom: 0;
    }

    .metric-container {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        text-align: center;
        backdrop-filter: blur(8px);
    }

    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #38bdf8;
    }

    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .doctor-card {
        background: rgba(30, 41, 59, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
    }

    .doctor-card:hover {
        border-color: #6366f1;
        box-shadow: 0 8px 25px rgba(99, 102, 241, 0.2);
    }

    .badge-pill {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }

    .badge-specialty {
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
    }

    .badge-city {
        background: rgba(129, 140, 248, 0.15);
        color: #a5b4fc;
    }

    .badge-available {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
    }

    .badge-busy {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
    }

    .cred-code {
        font-family: monospace;
        background: rgba(0, 0, 0, 0.35);
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        color: #f1f5f9;
    }
</style>
""", unsafe_allow_html=True)

# Data loader
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_FILE = os.path.join(BASE_DIR, "doctors_200_sample.csv")
JSON_FILE = os.path.join(BASE_DIR, "doctors_200_sample.json")
CREDS_CSV_FILE = os.path.join(BASE_DIR, "doctors_credentials.csv")


def load_data():
    docs = []
    if os.path.exists(JSON_FILE):
        try:
            with open(JSON_FILE, "r", encoding="utf-8") as f:
                docs = json.load(f)
        except Exception:
            docs = []
            
    # Also check cliniscan_db_backup.json for all registered doctors
    backup_file = os.path.abspath(os.path.join(BASE_DIR, "..", "data", "cliniscan_db_backup.json"))
    if os.path.exists(backup_file):
        try:
            with open(backup_file, "r", encoding="utf-8") as f:
                b_data = json.load(f)
            b_docs = [u for u in b_data.get("users", []) if u.get("role") == "Doctor"]
            existing_usernames = {d.get("username") for d in docs if d.get("username")}
            for bd in b_docs:
                u_name = bd.get("username")
                if u_name and u_name not in existing_usernames:
                    raw_name = str(bd.get("full_name", "Dr. Specialist")).strip()
                    clean_n = re.sub(r'^(Dr\.\s*|Dr\s+|Doctor\s+)+', '', raw_name, flags=re.IGNORECASE).strip()
                    clean_name = f"Dr. {clean_n}"
                    docs.insert(0, {
                        "doctor_id": bd.get("user_id", f"DOC-{u_name.upper()}"),
                        "user_id": bd.get("user_id", f"DOC-{u_name.upper()}"),
                        "username": u_name,
                        "email": bd.get("email", f"{u_name}@hospital.med"),
                        "password": bd.get("password", "Doctor123!"),
                        "Doctor_Name": clean_name,
                        "Disease": bd.get("disease_expertise", bd.get("specialization", "General")),
                        "Specialization": bd.get("specialization", "General Physician"),
                        "Experience": int(bd.get("experience_years", 15)),
                        "Rating": float(bd.get("rating", 5.0)),
                        "Hospital": bd.get("hospital", "AIIMS"),
                        "City": bd.get("city", "Bangalore"),
                        "Fees": int(bd.get("fees_inr", 800)),
                        "Availability": bd.get("availability", "Available"),
                        "created_at": bd.get("created_at", "")
                    })
                    existing_usernames.add(u_name)
        except Exception:
            pass

    if docs:
        df_res = pd.DataFrame(docs)
        if "Doctor_Name" in df_res.columns:
            df_res["Doctor_Name"] = df_res["Doctor_Name"].apply(
                lambda x: "Dr. " + re.sub(r'^(Dr\.\s*|Dr\s+|Doctor\s+)+', '', str(x).strip(), flags=re.IGNORECASE).strip()
            )
        return df_res
    elif os.path.exists(CSV_FILE):
        return pd.read_csv(CSV_FILE)
    return pd.DataFrame()


df = load_data()

# Header Banner
st.markdown("""
<div class="main-header">
    <h1>🩺 Doctor Portal & MongoDB Manager</h1>
    <p>Real-time database explorer, credential manager, and doctor authentication dashboard</p>
</div>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/fluency/96/stethoscope.png", width=70)
st.sidebar.title("Navigation")
menu = st.sidebar.radio(
    "Go to",
    [
        "🩺 AI Doctor Recommender",
        "➕ Register New Doctor",
        "🔐 Doctor Login",
        "📋 Doctor Directory & Credentials",
        "📊 Database Analytics",
        "⚙️ Database Actions"
    ]
)

# Top Metrics Row
if not df.empty:
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{len(df)}</div>
            <div class="metric-label">Doctors Sampled</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{df['City'].nunique()} / 26</div>
            <div class="metric-label">Cities Covered</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{df['Specialization'].nunique()}</div>
            <div class="metric-label">Specializations</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">⭐ {df['Rating'].mean():.2f}</div>
            <div class="metric-label">Avg Rating</div>
        </div>
        """, unsafe_allow_html=True)
    with col5:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">₹{df['Fees'].mean():.0f}</div>
            <div class="metric-label">Avg Consultation Fee</div>
        </div>
        """, unsafe_allow_html=True)
    st.write("")

    st.write("")

# -------------------------------------------------------------
# PAGE 0: AI DOCTOR RECOMMENDER
# -------------------------------------------------------------
if menu == "🩺 AI Doctor Recommender":
    st.subheader("🩺 Intelligent Specialist Recommendation Engine")
    st.caption("Match patient radiographic findings, symptoms, or suspected pathologies with ranked verified medical specialists.")

    col_rec1, col_rec2 = st.columns([1.2, 1])

    with col_rec1:
        st.markdown("#### 1. Clinical Pathology & Triage Filters")
        all_diseases = [
            "Pneumothorax", "Pleural effusion", "Pulmonary fibrosis", "ILD",
            "Cardiomegaly", "Aortic enlargement", "Consolidation", "Atelectasis",
            "Lung Opacity", "Infiltration", "Nodule/Mass", "Calcification", "Other lesion", "No Finding"
        ]
        selected_findings = st.multiselect(
            "Select Detected Chest Pathology / Clinical Indication(s):",
            all_diseases,
            default=["Pneumothorax"]
        )
        
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            all_c = ["All Cities"] + sorted(df['City'].unique().tolist())
            filter_city = st.selectbox("Patient City Preference:", all_c)
        with c_f2:
            all_h = ["All Hospitals"] + sorted(df['Hospital'].unique().tolist())
            filter_hosp = st.selectbox("Preferred Hospital Network:", all_h)

        c_f3, c_f4 = st.columns(2)
        with c_f3:
            filter_avail = st.checkbox("Available Specialists Only", value=True)
        with c_f4:
            max_fee_val = st.number_input("Maximum Consultation Fee (₹)", min_value=0, max_value=5000, value=0, step=100, help="0 for no fee limit")

    with col_rec2:
        st.markdown("#### 2. Clinical Mapping Summary")
        if selected_findings:
            primary_finding = selected_findings[0]
            if primary_finding in ["Cardiomegaly", "Aortic enlargement"]:
                target_spec = "Cardiologist"
                urgency = "Cardiovascular Evaluation & ECHO Assessment"
            elif primary_finding == "Nodule/Mass":
                target_spec = "Oncologist"
                urgency = "Pulmonary Oncology / CT Biopsy Staging"
            elif primary_finding == "No Finding":
                target_spec = "General Physician"
                urgency = "Annual Preventive Health Screening"
            else:
                target_spec = "Pulmonologist"
                urgency = "Respiratory & Pulmonology Review"
            
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.8); border: 1.5px solid #38bdf8; border-radius: 12px; padding: 1.25rem;">
                <h4 style="margin: 0 0 0.5rem 0; color: #38bdf8;">🎯 Target Specialty: {target_spec}</h4>
                <div style="font-size: 0.9rem; color: #cbd5e1; margin-bottom: 0.5rem;">
                    <strong>Pathologies:</strong> {', '.join(selected_findings)}
                </div>
                <div style="font-size: 0.85rem; color: #94a3b8;">
                    <strong>Clinical Urgency:</strong> <span style="color: #f59e0b; font-weight: 600;">{urgency}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            target_spec = "General Physician"
            st.info("Select one or more radiographic findings to view recommended specialists.")

    st.markdown("---")
    st.markdown("### 🏆 Top Ranked Specialists Matching Clinical Criteria")

    # Recommendation Filtering & Ranking Algorithm
    candidate_df = df.copy()
    if selected_findings:
        is_disease_match = candidate_df['Disease'].isin(selected_findings)
        is_spec_match = candidate_df['Specialization'].str.lower() == target_spec.lower()
        candidate_df = candidate_df[is_disease_match | is_spec_match].copy()

    if filter_city != "All Cities":
        candidate_df = candidate_df[candidate_df['City'] == filter_city]

    if filter_hosp != "All Hospitals":
        candidate_df = candidate_df[candidate_df['Hospital'] == filter_hosp]

    if filter_avail:
        candidate_df = candidate_df[candidate_df['Availability'] == 'Available']

    if max_fee_val > 0:
        candidate_df = candidate_df[candidate_df['Fees'] <= max_fee_val]

    if candidate_df.empty:
        st.warning(f"No specialists matched all strict filters for {filter_city}. Showing closest specialists across all cities:")
        candidate_df = df[df['Specialization'].str.lower() == target_spec.lower()].head(6).copy()

    # Match score calculation
    is_exact = candidate_df['Disease'].isin(selected_findings).astype(int)
    candidate_df['match_score'] = (
        (is_exact * 40.0) +
        (candidate_df['Rating'] * 12.0) +
        (candidate_df['Experience'].clip(upper=30) * 1.2) +
        ((candidate_df['Availability'] == 'Available').astype(int) * 15.0) -
        (candidate_df['Fees'] / 250.0)
    )

    ranked_doctors = candidate_df.sort_values(by=['match_score', 'Rating', 'Experience'], ascending=[False, False, False]).head(6)

    st.write(f"Displaying **{len(ranked_doctors)}** top ranked specialist matches:")

    rec_cols = st.columns(2)
    for idx, (_, doc) in enumerate(ranked_doctors.iterrows()):
        with rec_cols[idx % 2]:
            st.markdown(f"""
            <div class="doctor-card" style="border-left: 4px solid #38bdf8;">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <h3 style="color: #f8fafc; margin: 0;">🩺 {doc['Doctor_Name']}</h3>
                    <span class="badge-pill {'badge-available' if doc['Availability'] == 'Available' else 'badge-busy'}">
                        {doc['Availability']}
                    </span>
                </div>
                <div style="margin: 0.5rem 0;">
                    <span class="badge-pill badge-specialty">{doc['Specialization']}</span>
                    <span class="badge-pill badge-city">📍 {doc['City']}</span>
                    <span style="font-size: 0.8rem; color: #e2e8f0; background: rgba(56, 189, 248, 0.2); padding: 2px 8px; border-radius: 4px;">
                        Pathology: <strong>{doc['Disease']}</strong>
                    </span>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; font-size: 0.88rem; color: #cbd5e1; margin-top: 0.75rem;">
                    <div>🏥 <strong>{doc['Hospital']}</strong></div>
                    <div>⭐ <strong>{doc['Rating']} / 5.0</strong> Rating</div>
                    <div>🩺 <strong>{doc['Experience']} Years</strong> Exp</div>
                    <div>💰 <strong>₹{doc['Fees']}</strong> Fee</div>
                </div>
                <div style="margin-top: 0.75rem; font-size: 0.8rem; color: #94a3b8; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 0.5rem;">
                    <strong>Login ID:</strong> <span class="cred-code">{doc.get('user_id', 'N/A')}</span> | 
                    <strong>Email:</strong> {doc.get('email', 'N/A')}
                </div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"📅 Book Consultation with {doc['Doctor_Name']}", key=f"rec_book_{idx}", use_container_width=True):
                st.success(f"✅ Consultation request initiated for {doc['Doctor_Name']} at {doc['Hospital']}, {doc['City']}!")


# -------------------------------------------------------------
# PAGE 0.5: REGISTER NEW DOCTOR
# -------------------------------------------------------------
elif menu == "➕ Register New Doctor":
    st.subheader("➕ Register New Specialist Account")
    st.caption("Add a new doctor to MongoDB, sample files, credential sheets, and live recommendation database.")

    with st.form("new_doctor_registration_form"):
        st.markdown("#### Doctor Details & Clinical Profile")
        c_reg1, c_reg2 = st.columns(2)

        with c_reg1:
            new_doc_name = st.text_input("Doctor Full Name *", placeholder="e.g. Dr. Aravind Menon")
            new_spec = st.selectbox(
                "Medical Specialization *",
                ["Pulmonologist", "Cardiologist", "Oncologist", "General Physician", "Radiologist", "Thoracic Surgeon"]
            )
            new_disease = st.text_input("Primary Pathology / Sub-specialty Expertise", placeholder="e.g. Pneumothorax or ILD (Leave empty for default)")
            new_hosp = st.selectbox(
                "Hospital Network *",
                ["AIIMS", "Apollo Hospital", "Columbia Asia", "Fortis Hospital", "KMC Hospital", "Manipal Hospital", "Narayana Health", "Rainbow Hospital", "Sparsh Hospital", "Aster Hospital"]
            )

        with c_reg2:
            all_cities_list = sorted(df['City'].unique().tolist()) if not df.empty else ["Bangalore"]
            new_city = st.selectbox("City Location *", all_cities_list)
            new_exp = st.number_input("Years of Clinical Experience", min_value=1, max_value=60, value=15)
            new_fees = st.number_input("Consultation Fee (₹)", min_value=100, max_value=5000, value=800, step=50)
            new_avail = st.selectbox("Initial Availability Status", ["Available", "Busy"])
            custom_pass = st.text_input("Custom Password (Optional - leave blank for auto-generation)", type="password")

        reg_submit = st.form_submit_button("🚀 Register Doctor & Sync All Datasets", type="primary", use_container_width=True)

    if reg_submit:
        if not new_doc_name.strip():
            st.error("Please provide Doctor Full Name.")
        else:
            with st.spinner("Registering doctor and synchronizing datasets..."):
                from sample_and_populate_mongodb import add_doctor_to_all_datasets
                try:
                    registered_doc = add_doctor_to_all_datasets({
                        "Doctor_Name": new_doc_name.strip(),
                        "Specialization": new_spec,
                        "Disease": new_disease.strip() if new_disease.strip() else new_spec,
                        "Hospital": new_hosp,
                        "City": new_city,
                        "Experience": int(new_exp),
                        "Rating": 5.0,
                        "Fees": int(new_fees),
                        "Availability": new_avail,
                        "password": custom_pass.strip() if custom_pass.strip() else None
                    })
                    
                    st.success(f"🎉 {registered_doc['Doctor_Name']} successfully registered and added to all datasets & live recommender!")

                    st.markdown(f"""
                    <div class="doctor-card" style="border: 2px solid #10b981; margin-top: 1rem;">
                        <h4 style="color: #34d399; margin: 0 0 0.5rem 0;">📋 Generated Doctor Credentials</h4>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; font-size: 0.95rem;">
                            <div><strong>Doctor Name:</strong> {registered_doc['Doctor_Name']}</div>
                            <div><strong>Specialization:</strong> {registered_doc['Specialization']}</div>
                            <div><strong>User ID:</strong> <span class="cred-code">{registered_doc['user_id']}</span></div>
                            <div><strong>Username:</strong> <span class="cred-code">{registered_doc['username']}</span></div>
                            <div><strong>Email:</strong> <span class="cred-code">{registered_doc['email']}</span></div>
                            <div><strong>Password:</strong> <span class="cred-code">{registered_doc['password']}</span></div>
                        </div>
                        <div style="font-size: 0.82rem; color: #94a3b8; margin-top: 0.75rem;">
                            💡 The doctor can immediately log in using their Username or User ID and this password.
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    st.cache_data.clear()
                except Exception as ex:
                    st.error(f"Error registering doctor: {ex}")


# -------------------------------------------------------------
# PAGE 1: DOCTOR LOGIN
# -------------------------------------------------------------
elif menu == "🔐 Doctor Login":
    st.subheader("🔐 Doctor Portal Login")
    st.caption("Doctors can authenticate using their User ID, Username, or Email along with their generated password.")

    left_col, right_col = st.columns([1, 1.2])

    with left_col:
        with st.form("doctor_login_form"):
            login_id = st.text_input("User ID / Username / Email", placeholder="e.g. dr.osha.balasubramanian or DOC_0001")
            password = st.text_input("Password", type="password", placeholder="e.g. DrBalasubramanian#Os0001!")
            submit_btn = st.form_submit_button("Sign In to Portal", use_container_width=True)

        if submit_btn:
            if not login_id or not password:
                st.error("Please enter both login identifier and password.")
            else:
                match = df[
                    (df['user_id'].str.lower() == login_id.strip().lower()) |
                    (df['username'].str.lower() == login_id.strip().lower()) |
                    (df['email'].str.lower() == login_id.strip().lower())
                ]
                if not match.empty:
                    doctor = match.iloc[0]
                    if doctor['password'] == password.strip():
                        st.session_state['logged_doctor'] = doctor.to_dict()
                        st.success(f"✅ Welcome, {doctor['Doctor_Name']}!")
                    else:
                        st.error("❌ Authentication Failed: Invalid password.")
                else:
                    st.error("❌ Authentication Failed: Doctor user ID not found.")

    with right_col:
        if 'logged_doctor' in st.session_state:
            doc = st.session_state['logged_doctor']
            st.markdown(f"""
            <div class="doctor-card" style="border: 2px solid #10b981;">
                <h3 style="color: #38bdf8; margin-bottom: 0.25rem;">🩺 {doc['Doctor_Name']}</h3>
                <p style="color: #94a3b8; font-size: 0.9rem; margin-bottom: 1rem;">
                    <strong>ID:</strong> <span class="cred-code">{doc['user_id']}</span> | 
                    <strong>Email:</strong> {doc['email']}
                </p>
                <div style="margin-bottom: 1rem;">
                    <span class="badge-pill badge-specialty">{doc['Specialization']}</span>
                    <span class="badge-pill badge-city">📍 {doc['City']} ({doc['Hospital']})</span>
                    <span class="badge-pill {'badge-available' if doc['Availability'] == 'Available' else 'badge-busy'}">
                        {doc['Availability']}
                    </span>
                </div>
                <hr style="border-color: rgba(255,255,255,0.08); margin: 1rem 0;">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; font-size: 0.95rem;">
                    <div><strong>Specialty Disease:</strong> {doc['Disease']}</div>
                    <div><strong>Experience:</strong> {doc['Experience']} Years</div>
                    <div><strong>Consultation Fee:</strong> ₹{doc['Fees']}</div>
                    <div><strong>Patient Rating:</strong> ⭐ {doc['Rating']} / 5.0</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                new_status = st.selectbox("Update Availability", ["Available", "Busy"], index=0 if doc['Availability'] == 'Available' else 1)
            with col_b:
                if st.button("Logout", use_container_width=True):
                    del st.session_state['logged_doctor']
                    st.rerun()
        else:
            st.info("💡 **Quick Test Demo Accounts** (Click to inspect credentials):")
            sample_preview = df[['user_id', 'Doctor_Name', 'username', 'password', 'City']].head(3)
            st.dataframe(sample_preview, use_container_width=True, hide_index=True)


# -------------------------------------------------------------
# PAGE 2: DIRECTORY & CREDENTIALS
# -------------------------------------------------------------
elif menu == "📋 Doctor Directory & Credentials":
    st.subheader("📋 Doctor Directory & Credential Manager")
    st.caption("Search, filter, and inspect all 200 doctors and their login credentials.")

    # Search and Filters
    col_search, col_city, col_spec, col_avail = st.columns([1.5, 1, 1, 1])
    
    with col_search:
        search_query = st.text_input("🔍 Search Doctor, Hospital, or Disease", "")
    with col_city:
        all_cities = ["All Cities"] + sorted(df['City'].unique().tolist())
        selected_city = st.selectbox("Filter City", all_cities)
    with col_spec:
        all_specs = ["All Specialties"] + sorted(df['Specialization'].unique().tolist())
        selected_spec = st.selectbox("Filter Specialization", all_specs)
    with col_avail:
        selected_avail = st.selectbox("Filter Availability", ["All Statuses", "Available", "Busy"])

    # Filtering logic
    filtered_df = df.copy()
    if search_query:
        q = search_query.lower()
        filtered_df = filtered_df[
            filtered_df['Doctor_Name'].str.lower().str.contains(q) |
            filtered_df['Hospital'].str.lower().str.contains(q) |
            filtered_df['Disease'].str.lower().str.contains(q) |
            filtered_df['user_id'].str.lower().str.contains(q) |
            filtered_df['username'].str.lower().str.contains(q)
        ]
    if selected_city != "All Cities":
        filtered_df = filtered_df[filtered_df['City'] == selected_city]
    if selected_spec != "All Specialties":
        filtered_df = filtered_df[filtered_df['Specialization'] == selected_spec]
    if selected_avail != "All Statuses":
        filtered_df = filtered_df[filtered_df['Availability'] == selected_avail]

    st.write(f"Showing **{len(filtered_df)}** of **{len(df)}** doctors")

    # Display columns
    cols_to_show = [
        "user_id", "Doctor_Name", "Specialization", "Hospital", "City", 
        "Disease", "Rating", "Fees", "Availability", "username", "password", "email"
    ]
    st.dataframe(
        filtered_df[cols_to_show],
        column_config={
            "user_id": st.column_config.TextColumn("User ID", width="small"),
            "Doctor_Name": st.column_config.TextColumn("Doctor Name", width="medium"),
            "Rating": st.column_config.NumberColumn("Rating", format="⭐ %.1f"),
            "Fees": st.column_config.NumberColumn("Fee", format="₹%d"),
            "password": st.column_config.TextColumn("Password (Plain)"),
            "email": st.column_config.TextColumn("Email Address")
        },
        use_container_width=True,
        hide_index=True
    )

    # Downloads
    st.markdown("### 📥 Download Datasets & Credentials")
    dl1, dl2, dl3 = st.columns(3)
    with dl1:
        if os.path.exists(CREDS_CSV_FILE):
            with open(CREDS_CSV_FILE, "rb") as f:
                st.download_button("📥 Download Credentials (CSV)", f, file_name="doctors_credentials.csv", mime="text/csv", use_container_width=True)
    with dl2:
        if os.path.exists(JSON_FILE):
            with open(JSON_FILE, "rb") as f:
                st.download_button("📥 Download MongoDB Data (JSON)", f, file_name="doctors_200_sample.json", mime="application/json", use_container_width=True)
    with dl3:
        if os.path.exists(CSV_FILE):
            with open(CSV_FILE, "rb") as f:
                st.download_button("📥 Download Sample (CSV)", f, file_name="doctors_200_sample.csv", mime="text/csv", use_container_width=True)


# -------------------------------------------------------------
# PAGE 3: ANALYTICS & INSIGHTS
# -------------------------------------------------------------
elif menu == "📊 Database Analytics":
    st.subheader("📊 MongoDB Dataset Analytics")
    st.caption("Visual distribution of the 200 sampled doctors across Karnataka cities, specialties, and fee metrics.")

    tab1, tab2 = st.tabs(["🏙️ Geographic Coverage", "🩺 Clinical & Financial Insights"])

    with tab1:
        col_c1, col_c2 = st.columns([1.3, 1])
        with col_c1:
            city_counts = df['City'].value_counts().reset_index()
            city_counts.columns = ['City', 'Doctor Count']
            if HAS_PLOTLY:
                fig_city = px.bar(
                    city_counts,
                    x='City',
                    y='Doctor Count',
                    title="Doctors per City (All 26 Cities Represented)",
                    color='Doctor Count',
                    color_continuous_scale='Viridis'
                )
                fig_city.update_layout(xaxis_tickangle=-45, template="plotly_dark", height=420)
                st.plotly_chart(fig_city, use_container_width=True)
            else:
                st.markdown("#### Doctors per City")
                st.bar_chart(city_counts.set_index('City'))

        with col_c2:
            if HAS_PLOTLY:
                fig_pie = px.pie(
                    df,
                    names='Specialization',
                    title="Specialization Share",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                fig_pie.update_layout(template="plotly_dark", height=420)
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.markdown("#### Specialization Distribution")
                st.bar_chart(df['Specialization'].value_counts())

    with tab2:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            if HAS_PLOTLY:
                fig_fees = px.box(
                    df,
                    x='Specialization',
                    y='Fees',
                    color='Specialization',
                    title="Consultation Fee Distribution by Specialty (₹)",
                    points="all"
                )
                fig_fees.update_layout(template="plotly_dark", height=400, showlegend=False)
                st.plotly_chart(fig_fees, use_container_width=True)
            else:
                st.markdown("#### Average Fees by Specialty")
                st.bar_chart(df.groupby('Specialization')['Fees'].mean())

        with col_f2:
            if HAS_PLOTLY:
                fig_exp = px.scatter(
                    df,
                    x='Experience',
                    y='Rating',
                    color='Specialization',
                    size='Fees',
                    hover_data=['Doctor_Name', 'Hospital', 'City'],
                    title="Rating vs. Experience (Bubble Size = Fees)"
                )
                fig_exp.update_layout(template="plotly_dark", height=400)
                st.plotly_chart(fig_exp, use_container_width=True)
            else:
                st.markdown("#### Rating vs Experience")
                st.scatter_chart(df, x='Experience', y='Rating', color='Specialization')


# -------------------------------------------------------------
# PAGE 4: DATABASE ACTIONS
# -------------------------------------------------------------
elif menu == "⚙️ Database Actions":
    st.subheader("⚙️ Database Operations & Pipeline Runner")
    st.caption("Re-sample dataset with a custom seed or push directly to MongoDB instance.")

    with st.form("pipeline_form"):
        st.markdown("#### Sampling & Ingestion Options")
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            seed_val = st.number_input("Random Seed (for reproducibility)", min_value=1, max_value=9999, value=42)
            sample_count = st.number_input("Number of Doctors to Sample", min_value=26, max_value=2000, value=200)
        with col_p2:
            mongo_uri = st.text_input("MongoDB Connection URI", value="mongodb://localhost:27017/")
            db_target = st.text_input("Database Name", value="doctor_db")

        run_btn = st.form_submit_button("🚀 Run Pipeline & Update MongoDB", use_container_width=True)

    if run_btn:
        with st.spinner("Sampling doctors and updating database & credentials..."):
            from sample_and_populate_mongodb import sample_doctors_data, prepare_documents_with_credentials, export_all_files, populate_database, DEFAULT_CSV_PATH
            try:
                new_df = sample_doctors_data(DEFAULT_CSV_PATH, total_samples=int(sample_count), random_seed=int(seed_val))
                db_docs, creds_list = prepare_documents_with_credentials(new_df)
                export_all_files(db_docs, creds_list)
                populate_database(db_docs, mongo_uri=mongo_uri, db_name=db_target, collection_name="doctors")
                st.success("✅ Ingestion & Credential Generation Completed Successfully!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Error during ingestion: {e}")
