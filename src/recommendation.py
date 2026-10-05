"""
CliniScan+ Doctor Recommendation Engine
Matches YOLO11 chest X-ray abnormality detections to verified medical specialists
using the comprehensive 2,000-doctor clinical dataset.
"""

import os
import time
import json
import logging
from typing import List, Dict, Optional, Union, Tuple
import pandas as pd
import numpy as np

from src.database import db_instance
from src.gemini_recommender import gemini_doctor_engine

logger = logging.getLogger(__name__)

# Default locations for doctor dataset
DEFAULT_DATASET_PATHS = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "doctor_2000_realnames.csv"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "recommender", "doctor_2000_realnames.csv"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "doctors.csv"),
]

# Mapping from YOLO11 / Radiographic finding names to dataset Disease names & Primary Specialties
DISETASE_SPECIALTY_MAP = {
    "Atelectasis": {"dataset_disease": "Atelectasis", "specialty": "Pulmonologist", "urgency": "Routine / Subacute Follow-up"},
    "ILD": {"dataset_disease": "ILD", "specialty": "Pulmonologist", "urgency": "Chronic Interstitial Evaluation"},
    "Pulmonary fibrosis": {"dataset_disease": "Pulmonary fibrosis", "specialty": "Pulmonologist", "urgency": "Pulmonary Rehabilitation & Specialist Consult"},
    "Pneumothorax": {"dataset_disease": "Pneumothorax", "specialty": "Pulmonologist", "urgency": "Emergency / Immediate Attention"},
    "Pleural effusion": {"dataset_disease": "Pleural effusion", "specialty": "Pulmonologist", "urgency": "Urgent Thoracentesis / Pulmonology Review"},
    "Pleural thickening": {"dataset_disease": "Pleural thickening", "specialty": "Pulmonologist", "urgency": "Pulmonology Follow-up"},
    "Consolidation": {"dataset_disease": "Consolidation", "specialty": "Pulmonologist", "urgency": "Infectious / Pneumonia Triage"},
    "Lung Opacity": {"dataset_disease": "Lung Opacity", "specialty": "Pulmonologist", "urgency": "Diagnostic Differential Consult"},
    "Nodule/Mass": {"dataset_disease": "Nodule/Mass", "specialty": "Oncologist", "urgency": "Pulmonary Oncology / CT Biopsy Staging"},
    "Infiltration": {"dataset_disease": "Infiltration", "specialty": "Pulmonologist", "urgency": "Respiratory Infection & Antimicrobial Review"},
    "Aortic enlargement": {"dataset_disease": "Aortic enlargement", "specialty": "Cardiologist", "urgency": "Cardiovascular Evaluation & Echocardiogram"},
    "Cardiomegaly": {"dataset_disease": "Cardiomegaly", "specialty": "Cardiologist", "urgency": "Cardiology Heart Failure & ECHO Assessment"},
    "Calcification": {"dataset_disease": "Calcification", "specialty": "Pulmonologist", "urgency": "Routine Follow-up"},
    "Other lesion": {"dataset_disease": "Other lesion", "specialty": "Pulmonologist", "urgency": "Diagnostic Follow-up"},
    "No Finding": {"dataset_disease": "No Finding", "specialty": "General Physician", "urgency": "Annual Preventive Screening"},
}


class DoctorRecommendationEngine:
    """
    Intelligent healthcare recommendation engine matching patient radiographic
    findings with ranked specialists across 26 cities and 10 hospital networks.
    """

    def __init__(self, dataset_path: Optional[str] = None):
        self.df = self._load_dataset(dataset_path)
        self.bookings_log_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "data", "patient_bookings.json"
        )
        self._ensure_bookings_store()

    def _load_dataset(self, dataset_path: Optional[str]) -> pd.DataFrame:
        """Load and validate doctor dataset from CSV and merge registered MongoDB doctors."""
        candidates = [dataset_path] if dataset_path else DEFAULT_DATASET_PATHS
        df = None
        for p in candidates:
            if p and os.path.exists(p):
                try:
                    df = pd.read_csv(p)
                    # Normalize columns and clean strings
                    df.columns = [c.strip() for c in df.columns]
                    df["Doctor_Name"] = df["Doctor_Name"].astype(str).str.strip()
                    df["Disease"] = df["Disease"].astype(str).str.strip()
                    df["Specialization"] = df["Specialization"].astype(str).str.strip()
                    df["Hospital"] = df["Hospital"].astype(str).str.strip()
                    df["City"] = df["City"].astype(str).str.strip()
                    df["Availability"] = df["Availability"].astype(str).str.strip()
                    df["Experience"] = pd.to_numeric(df["Experience"], errors="coerce").fillna(5).astype(int)
                    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce").fillna(4.0).astype(float)
                    df["Fees"] = pd.to_numeric(df["Fees"], errors="coerce").fillna(800).astype(int)
                    df["is_registered"] = False
                    logger.info(f"Loaded {len(df)} doctors from {p}")
                    break
                except Exception as e:
                    logger.error(f"Failed loading {p}: {e}")

        # Fallback dummy dataset if file missing
        if df is None:
            df = pd.DataFrame([
                {
                    "Doctor_Name": "Dr. Yukti Chauhan",
                    "Disease": "Pulmonary fibrosis",
                    "Specialization": "Pulmonologist",
                    "Experience": 20,
                    "Rating": 5.0,
                    "Hospital": "AIIMS",
                    "City": "Bangalore",
                    "Fees": 800,
                    "Availability": "Available",
                    "is_registered": False
                }
            ])

        # Dynamically merge all registered Doctor accounts from MongoDB / backup!
        try:
            import re
            registered_doctors = []
            if hasattr(db_instance, "db") and db_instance.db is not None:
                registered_doctors = list(db_instance.db.users.find({"role": "Doctor"}, {"_id": 0}))

            # If empty, also check local JSON backup directly
            if not registered_doctors:
                backup_p = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "cliniscan_db_backup.json")
                if os.path.exists(backup_p):
                    try:
                        with open(backup_p, "r", encoding="utf-8") as f:
                            b_data = json.load(f)
                        registered_doctors = [u for u in b_data.get("users", []) if u.get("role") == "Doctor"]
                    except Exception:
                        pass

            extra_rows = []
            for rd in registered_doctors:
                raw_name = str(rd.get("full_name", "")).strip()
                clean_n = re.sub(r'^(Dr\.\s*|Dr\s+|Doctor\s+)+', '', raw_name, flags=re.IGNORECASE).strip()
                d_name = f"Dr. {clean_n}"
                
                d_city = str(rd.get("city", "Bangalore")).strip()
                d_spec = str(rd.get("specialization", "General Physician")).strip()
                d_exp = int(rd.get("experience_years", 15))
                d_rating = float(rd.get("rating", 5.0))
                d_hosp = str(rd.get("hospital", "AIIMS")).strip()
                d_fee = int(rd.get("fees_inr", 800))
                d_avail = str(rd.get("availability", "Available")).strip()
                d_disease = str(rd.get("disease_expertise") or d_spec).strip()

                # Check exact match on Doctor_Name AND City
                exact_mask = (
                    (df["Doctor_Name"].str.lower() == d_name.lower()) |
                    (df["Doctor_Name"].str.lower() == clean_n.lower()) |
                    (df["Doctor_Name"].str.lower() == f"dr. {clean_n.lower()}")
                ) & (df["City"].str.lower() == d_city.lower())
                
                if exact_mask.any():
                    df.loc[exact_mask, "Doctor_Name"] = d_name
                    df.loc[exact_mask, "is_registered"] = True
                    df.loc[exact_mask, "Fees"] = d_fee
                    df.loc[exact_mask, "Availability"] = d_avail
                    df.loc[exact_mask, "Hospital"] = d_hosp
                    df.loc[exact_mask, "Specialization"] = d_spec
                else:
                    # Add primary row
                    extra_rows.append({
                        "Doctor_Name": d_name,
                        "Disease": d_disease,
                        "Specialization": d_spec,
                        "Experience": d_exp,
                        "Rating": d_rating,
                        "Hospital": d_hosp,
                        "City": d_city,
                        "Fees": d_fee,
                        "Availability": d_avail,
                        "is_registered": True
                    })
                    # Also associate with related chest pathologies for that specialty
                    spec_diseases = [
                        dis for dis, sinfo in DISETASE_SPECIALTY_MAP.items() 
                        if sinfo.get("specialty", "").lower() == d_spec.lower() and dis != d_disease
                    ]
                    for sdis in spec_diseases:
                        extra_rows.append({
                            "Doctor_Name": d_name,
                            "Disease": sdis,
                            "Specialization": d_spec,
                            "Experience": d_exp,
                            "Rating": d_rating,
                            "Hospital": d_hosp,
                            "City": d_city,
                            "Fees": d_fee,
                            "Availability": d_avail,
                            "is_registered": True
                        })
            if extra_rows:
                extra_df = pd.DataFrame(extra_rows)
                df = pd.concat([extra_df, df], ignore_index=True)
                logger.info(f"Merged {len(extra_rows)} newly registered doctor entries into recommendation database.")
        except Exception as err:
            logger.warning(f"Error merging registered doctors: {err}")

        return df

    def reload(self):
        """Reload the doctor database to include newly registered doctors immediately."""
        self.df = self._load_dataset(None)

    def _ensure_bookings_store(self):
        """Ensure bookings storage directory exists."""
        os.makedirs(os.path.dirname(self.bookings_log_path), exist_ok=True)
        if not os.path.exists(self.bookings_log_path):
            with open(self.bookings_log_path, "w") as f:
                json.dump([], f)

    def get_cities(self) -> List[str]:
        """Get sorted list of all unique cities in the dataset."""
        return sorted(self.df["City"].dropna().unique().tolist())

    def get_hospitals(self) -> List[str]:
        """Get sorted list of all unique hospital networks."""
        return sorted(self.df["Hospital"].dropna().unique().tolist())

    def get_specializations(self) -> List[str]:
        """Get sorted list of medical specializations."""
        return sorted(self.df["Specialization"].dropna().unique().tolist())

    def recommend_doctors(
        self,
        detected_findings: List[Dict],
        city_filter: Optional[str] = None,
        hospital_filter: Optional[str] = None,
        availability_only: bool = True,
        max_fee: Optional[int] = None,
        top_k: int = 4,
        use_gemini_live: bool = True
    ) -> Dict:
        """
        Intelligently recommend top medical specialists tailored to YOLO11 detections.
        Supports real-world live doctor matching via Google Gemini AI.
        """
        # Attempt real-world doctor retrieval via Gemini Live Engine if active
        if use_gemini_live and gemini_doctor_engine.is_available() and (hospital_filter in (None, "All Hospitals")) and (max_fee is None or max_fee >= 2000):
            try:
                target_city = city_filter if (city_filter and city_filter != "All Cities") else "Bangalore"
                gemini_res = gemini_doctor_engine.recommend_real_doctors(
                    findings=detected_findings,
                    city=target_city,
                    top_k=top_k
                )
                if gemini_res and gemini_res.get("doctors"):
                    logger.info("Successfully generated real-world specialist recommendations using Gemini Live Engine.")
                    return gemini_res
            except Exception as e:
                logger.warning(f"Gemini live doctor fetch failed, falling back to internal database: {e}")

        finding_names = []
        if isinstance(detected_findings, list):
            for f in detected_findings:
                cname = f.get("class_name")
                if cname and cname not in finding_names:
                    finding_names.append(cname)

        if not finding_names:
            target_diseases = ["No Finding"]
            primary_specialty = "General Physician"
            clinical_summary = "Normal Chest Radiograph. Routine preventive consultation recommended."
            primary_urgency = "Routine Annual Checkup"
        else:
            target_diseases = finding_names
            # Pick primary specialty from highest severity finding
            primary_finding = finding_names[0]
            spec_info = DISETASE_SPECIALTY_MAP.get(primary_finding, {"specialty": "Pulmonologist", "urgency": "Clinical Correlation"})
            primary_specialty = spec_info["specialty"]
            primary_urgency = spec_info["urgency"]
            clinical_summary = f"Detected {len(finding_names)} pathology indications: {', '.join(finding_names)}. Prioritizing {primary_specialty} consultations."

        # Filter candidate doctors: exact disease match OR primary specialty match OR registered doctors with matching specialty
        is_candidate = (
            self.df["Disease"].isin(target_diseases) |
            (self.df["Specialization"].str.lower() == primary_specialty.lower()) |
            (self.df.get("is_registered", False) & (self.df["Specialization"].str.lower() == primary_specialty.lower()))
        )
        matched_df = self.df[is_candidate].copy().drop_duplicates(subset=["Doctor_Name", "Hospital", "City"])

        # If empty, fallback to entire pool
        if matched_df.empty:
            matched_df = self.df.copy().drop_duplicates(subset=["Doctor_Name", "Hospital", "City"])

        # Apply user filters
        if city_filter and city_filter != "All Cities":
            city_matched = matched_df[matched_df["City"].str.lower() == city_filter.lower()]
            if len(city_matched) > 0:
                matched_df = city_matched.copy()

        if hospital_filter and hospital_filter != "All Hospitals":
            hosp_matched = matched_df[matched_df["Hospital"].str.lower() == hospital_filter.lower()]
            if len(hosp_matched) > 0:
                matched_df = hosp_matched.copy()

        if availability_only:
            avail_matched = matched_df[matched_df["Availability"].str.lower() == "available"]
            if len(avail_matched) > 0:
                matched_df = avail_matched.copy()

        if max_fee is not None and max_fee > 0:
            fee_matched = matched_df[matched_df["Fees"] <= max_fee]
            if len(fee_matched) > 0:
                matched_df = fee_matched.copy()

        if matched_df.empty:
            matched_df = self.df.head(top_k).copy()
        else:
            matched_df = matched_df.copy()

        # Compute intelligent ranking score
        is_exact_disease = (
            matched_df["Disease"].isin(target_diseases) | 
            (matched_df["Specialization"].str.lower() == primary_specialty.lower())
        ).astype(int)
        is_available = (matched_df["Availability"].str.lower() == "available").astype(int)
        is_reg = matched_df.get("is_registered", pd.Series([False]*len(matched_df))).fillna(False).astype(int)

        matched_df["match_score"] = (
            (is_exact_disease * 40.0) +
            (is_reg * 30.0) +
            (matched_df["Rating"] * 12.0) +
            (matched_df["Experience"].clip(upper=30) * 1.2) +
            (is_available * 15.0) -
            (matched_df["Fees"] / 250.0)
        )

        ranked_df = matched_df.sort_values(by=["match_score", "Rating", "Experience"], ascending=[False, False, False]).head(top_k)

        doctors_list = []
        for _, row in ranked_df.iterrows():
            doctors_list.append({
                "doctor_name": row["Doctor_Name"],
                "specialization": row["Specialization"],
                "disease_expertise": row["Disease"],
                "experience_years": int(row["Experience"]),
                "rating": float(row["Rating"]),
                "hospital": row["Hospital"],
                "city": row["City"],
                "fees_inr": int(row["Fees"]),
                "availability": row["Availability"],
                "is_registered": bool(row.get("is_registered", False)),
                "is_exact_match": bool(row["Disease"] in target_diseases or row["Specialization"] == primary_specialty)
            })

        return {
            "primary_specialty": primary_specialty,
            "clinical_urgency": primary_urgency,
            "clinical_summary": clinical_summary,
            "target_findings": target_diseases,
            "recommended_doctors": doctors_list,
            "doctors": doctors_list
        }

    def search_all_doctors(
        self,
        query: Optional[str] = None,
        specialty: Optional[str] = None,
        city: Optional[str] = None,
        hospital: Optional[str] = None,
        min_rating: float = 0.0,
        max_fee: Optional[int] = None,
        available_only: bool = False
    ) -> List[Dict]:
        """Search and filter through all 2,000+ doctors in the directory with relevance scoring."""
        df_filtered = self.df.copy()

        if query:
            q = query.lower().strip()
            df_filtered = df_filtered[
                df_filtered["Doctor_Name"].str.lower().str.contains(q, regex=False) |
                df_filtered["Disease"].str.lower().str.contains(q, regex=False) |
                df_filtered["Specialization"].str.lower().str.contains(q, regex=False) |
                df_filtered["Hospital"].str.lower().str.contains(q, regex=False) |
                df_filtered["City"].str.lower().str.contains(q, regex=False)
            ].copy()

            def compute_search_relevance(row):
                name = str(row["Doctor_Name"]).lower()
                clean_name = name.replace("dr. ", "").strip()
                score = 0
                if name == q or clean_name == q or name == f"dr. {q}":
                    score += 5000
                elif clean_name.startswith(q) or name.startswith(f"dr. {q}"):
                    score += 2000
                elif q in clean_name.split():
                    score += 1000
                elif q in name:
                    score += 500
                
                if row.get("is_registered", False):
                    score += 300
                
                score += float(row.get("Rating", 4.0)) * 10
                score += int(row.get("Experience", 5)) * 0.5
                return score

            df_filtered["search_score"] = df_filtered.apply(compute_search_relevance, axis=1)
            df_filtered = df_filtered.sort_values(by=["search_score", "Rating", "Experience"], ascending=[False, False, False])
        else:
            df_filtered = df_filtered.sort_values(by=["Rating", "Experience"], ascending=[False, False])

        if specialty and specialty != "All Specialties":
            df_filtered = df_filtered[df_filtered["Specialization"].str.lower() == specialty.lower()]

        if city and city != "All Cities":
            df_filtered = df_filtered[df_filtered["City"].str.lower() == city.lower()]

        if hospital and hospital != "All Hospitals":
            df_filtered = df_filtered[df_filtered["Hospital"].str.lower() == hospital.lower()]

        if min_rating > 0.0:
            df_filtered = df_filtered[df_filtered["Rating"] >= min_rating]

        if max_fee and max_fee > 0:
            df_filtered = df_filtered[df_filtered["Fees"] <= max_fee]

        if available_only:
            df_filtered = df_filtered[df_filtered["Availability"].str.lower() == "available"]

        results = []
        for _, row in df_filtered.iterrows():
            results.append({
                "doctor_name": row["Doctor_Name"],
                "specialization": row["Specialization"],
                "disease_expertise": row["Disease"],
                "experience_years": int(row["Experience"]),
                "rating": float(row["Rating"]),
                "hospital": row["Hospital"],
                "city": row["City"],
                "fees_inr": int(row["Fees"]),
                "availability": row["Availability"],
                "is_registered": bool(row.get("is_registered", False))
            })
        return results

    def get_analytics_summary(self) -> Dict:
        """Provide medical network analytics summary for dashboard charts."""
        total_docs = len(self.df)
        registered_count = int(self.df.get("is_registered", False).sum()) if "is_registered" in self.df.columns else 0
        avg_exp = float(self.df["Experience"].mean()) if not self.df.empty else 0.0
        avg_fee = float(self.df["Fees"].mean()) if not self.df.empty else 0.0
        avg_rating = float(self.df["Rating"].mean()) if not self.df.empty else 0.0

        spec_dist = self.df["Specialization"].value_counts().to_dict() if not self.df.empty else {}
        city_dist = self.df["City"].value_counts().to_dict() if not self.df.empty else {}
        hosp_dist = self.df["Hospital"].value_counts().to_dict() if not self.df.empty else {}
        avail_dist = self.df["Availability"].value_counts().to_dict() if not self.df.empty else {}

        return {
            "total_doctors": total_docs,
            "registered_doctors": registered_count,
            "avg_experience": round(avg_exp, 1),
            "avg_fees": int(round(avg_fee)),
            "avg_rating": round(avg_rating, 2),
            "specialization_counts": spec_dist,
            "city_counts": city_dist,
            "hospital_counts": hosp_dist,
            "availability_counts": avail_dist
        }

    def register_doctor_into_system(self, doctor_data: Dict) -> Tuple[bool, str, Dict]:
        """
        Natively register a new specialist into the recommendation engine,
        MongoDB collection, and all persistent dataset backups.
        """
        raw_name = str(doctor_data.get("Doctor_Name") or doctor_data.get("full_name") or "Specialist").strip()
        import re
        clean_n = re.sub(r'^(Dr\.\s*|Dr\s+|Doctor\s+)+', '', raw_name, flags=re.IGNORECASE).strip()
        d_name = f"Dr. {clean_n}"

        hospital = doctor_data.get("Hospital") or doctor_data.get("hospital") or "AIIMS"
        city = doctor_data.get("City") or doctor_data.get("city") or "Bangalore"
        spec = doctor_data.get("Specialization") or doctor_data.get("specialization") or "General Physician"
        disease = doctor_data.get("Disease") or doctor_data.get("disease_expertise") or spec
        exp = int(doctor_data.get("Experience") or doctor_data.get("experience_years") or 15)
        rating = float(doctor_data.get("Rating") or doctor_data.get("rating") or 5.0)
        fees = int(doctor_data.get("Fees") or doctor_data.get("fees_inr") or 800)
        avail = doctor_data.get("Availability") or doctor_data.get("availability") or "Available"

        username = doctor_data.get("username")
        email = doctor_data.get("email")
        password = doctor_data.get("password", "Doctor123!")

        # Auto-generate credentials if not provided
        if not username or not email:
            slug = clean_n.lower().replace(" ", ".")
            h_slug = hospital.lower().replace(" ", "").replace("hospital", "")[:6]
            rand_suffix = f"{int(time.time()*1000)%1000:03d}"
            username = username or f"dr.{slug}.{rand_suffix}"
            email = email or f"{username}@{h_slug}.org"
            user_id = f"DOC-{int(time.time()*1000)%1000000:06d}"
        else:
            user_id = doctor_data.get("user_id", f"DOC-{int(time.time()*1000)%1000000:06d}")

        ok, msg = db_instance.register_user(
            username=username,
            password=password,
            role="Doctor",
            full_name=d_name,
            email=email,
            phone=doctor_data.get("phone", "+91 98111 22334"),
            city=city,
            extra_data={
                "user_id": user_id,
                "specialization": spec,
                "hospital": hospital,
                "experience_years": exp,
                "fees_inr": fees,
                "rating": rating,
                "availability": avail,
                "disease_expertise": disease
            }
        )

        if ok:
            self.reload()
            return True, "Specialist registered and synchronized across all datasets!", {
                "user_id": user_id,
                "doctor_name": d_name,
                "username": username,
                "email": email,
                "password": password,
                "specialization": spec,
                "hospital": hospital,
                "city": city,
                "fees_inr": fees,
                "availability": avail
            }
        return False, msg, {}

    def book_appointment(
        self,
        patient_name: str,
        patient_phone: str,
        doctor_name: str,
        hospital: str,
        city: str,
        finding: str,
        preferred_slot: str = "Tomorrow (10:00 AM - 11:00 AM)",
        patient_username: str = "patient_demo",
        specialization: str = "Pulmonologist",
        scan_id: Optional[str] = None
    ) -> Dict:
        """Simulate an instant appointment booking with MongoDB persistence."""
        appointment_doc = {
            "patient_username": patient_username,
            "patient_name": patient_name,
            "patient_phone": patient_phone,
            "doctor_name": doctor_name,
            "specialization": specialization,
            "hospital": hospital,
            "city": city,
            "clinical_indication": finding,
            "appointment_slot": preferred_slot,
            "scan_id": scan_id,
            "status": "Pending"
        }

        # Save to MongoDB
        apt_id = db_instance.create_appointment(appointment_doc)
        appointment_doc["appointment_id"] = apt_id

        # Also maintain legacy JSON log for inspection
        try:
            with open(self.bookings_log_path, "r") as f:
                bookings = json.load(f)
            clean_doc = {k: str(v) if k == "_id" else v for k, v in appointment_doc.items()}
            bookings.append(clean_doc)
            with open(self.bookings_log_path, "w") as f:
                json.dump(bookings, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed updating bookings JSON log: {e}")

        logger.info(f"Booked appointment {apt_id} for {patient_name} with {doctor_name}")
        return appointment_doc


# Singleton Engine Instance
doctor_engine = DoctorRecommendationEngine()
