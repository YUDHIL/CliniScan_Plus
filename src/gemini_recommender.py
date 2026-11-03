"""
CliniScan+ Gemini Live Specialist Referral & Triage Engine
Powered by Google Gemini with Structured Clinical Grounding.
Discovers medical specialists, accredited hospital departments, and clinic directions
tailored to radiographic chest abnormalities.
"""

import os
import json
import logging
import urllib.parse
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

from src.gemini_service import gemini_service

# Deterministic root .env loading
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(PROJECT_ROOT, ".env")

if os.path.exists(ENV_FILE):
    load_dotenv(dotenv_path=ENV_FILE, override=False)

logger = logging.getLogger(__name__)

# Specialty & Urgency mapping for radiographic findings
SPECIALTY_DISEASE_MAP = {
    "Atelectasis": {"specialty": "Pulmonologist / Chest Physician", "urgency": "Routine / Subacute Follow-up"},
    "ILD": {"specialty": "Pulmonologist & Interstitial Lung Disease Specialist", "urgency": "Specialist Consultation"},
    "Pulmonary fibrosis": {"specialty": "Pulmonologist & Respiratory Specialist", "urgency": "Pulmonary Consult"},
    "Pneumothorax": {"specialty": "Pulmonologist / Thoracic Surgeon", "urgency": "Emergency / Immediate Attention"},
    "Pleural effusion": {"specialty": "Pulmonologist / Thoracic Specialist", "urgency": "Urgent Evaluation & Thoracentesis"},
    "Pleural thickening": {"specialty": "Pulmonologist", "urgency": "Pulmonology Review"},
    "Consolidation": {"specialty": "Pulmonologist / Infectious Disease Physician", "urgency": "Infectious Triage"},
    "Lung Opacity": {"specialty": "Pulmonologist / Respiratory Physician", "urgency": "Diagnostic Evaluation"},
    "Nodule/Mass": {"specialty": "Pulmonary Oncologist / Thoracic Surgeon", "urgency": "Oncology & CT Staging"},
    "Infiltration": {"specialty": "Pulmonologist / General Physician", "urgency": "Respiratory Consult"},
    "Aortic enlargement": {"specialty": "Cardiologist / Vascular Specialist", "urgency": "Cardiovascular Evaluation"},
    "Cardiomegaly": {"specialty": "Cardiologist / Heart Failure Specialist", "urgency": "Cardiology Consultation & ECHO"},
    "Calcification": {"specialty": "Pulmonologist / Radiologist", "urgency": "Routine Follow-up"},
    "Other lesion": {"specialty": "Pulmonologist / Internal Medicine Physician", "urgency": "Diagnostic Follow-up"},
    "No Finding": {"specialty": "General Physician / Preventive Care", "urgency": "Annual Health Checkup"},
}


class GeminiDoctorRecommender:
    """
    Specialist recommendation engine utilizing centralized Gemini AI service
    with clinical triage safeguards, JSON validation, and direct maps/booking navigation.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.service = gemini_service

    def is_available(self) -> bool:
        """Check whether the underlying Gemini service is ready."""
        return self.service.is_available()

    def recommend_real_doctors(
        self,
        findings: List[Dict],
        city: str = "Bangalore",
        top_k: int = 4
    ) -> Optional[Dict[str, Any]]:
        """
        Query Gemini to retrieve recommended medical specialists in `city`
        matching detected chest X-ray findings.
        """
        if not self.is_available():
            logger.warning("[GeminiDoctorRecommender] Gemini service is unavailable.")
            return None

        # Extract detected class names
        finding_names = []
        for f in findings:
            cname = f.get("class_name")
            if cname and cname not in finding_names:
                finding_names.append(cname)

        if not finding_names:
            primary_finding = "No Finding"
            spec_info = SPECIALTY_DISEASE_MAP["No Finding"]
            findings_text = "No focal radiographic abnormalities detected (Normal scan)"
        else:
            primary_finding = finding_names[0]
            spec_info = SPECIALTY_DISEASE_MAP.get(
                primary_finding,
                {"specialty": "Pulmonologist", "urgency": "Clinical Correlation"}
            )
            findings_text = ", ".join(finding_names)

        target_specialty = spec_info["specialty"]
        target_urgency = spec_info["urgency"]
        effective_city = city if city and city.lower() != "all cities" else "Bangalore"

        prompt = f"""You are a clinical triage director in the CliniScan+ Hospital Platform.
A patient has undergone chest radiograph analysis with the following findings:
- Radiographic Finding(s): {findings_text}
- Recommended Specialist Domain: {target_specialty}
- Clinical Urgency Level: {target_urgency}
- Patient Location: {effective_city}

TASK:
Provide a list of up to {top_k} prominent medical specialists or hospital departments in or near {effective_city} specializing in {target_specialty} (e.g. at accredited institutions such as Apollo, Fortis, Max, Manipal, AIIMS, Medanta, Narayana Health, Aster, or established clinical centers).

CRITICAL MEDICAL SAFEGUARDS:
- Do not fabricate doctor personal contact numbers; use official hospital reception numbers or null.
- Do not invent consultation fees; provide estimated standard fees or null.
- Never state that an appointment is pre-booked or confirmed.
- Every entry is an AI-generated clinical referral suggestion for patient navigation.

Return ONLY a valid JSON object with this exact structure:
{{
  "search_location": "{effective_city}",
  "primary_specialty": "{target_specialty}",
  "target_findings": {json.dumps(finding_names or ['Normal Chest Radiograph'])},
  "clinical_summary": "Comprehensive medical summary explaining why {target_specialty} consultation is recommended for {findings_text}.",
  "recommended_urgency": "{target_urgency}",
  "doctors": [
    {{
      "doctor_name": "Dr. Specialist Name",
      "specialization": "{target_specialty}",
      "hospital": "Hospital Name",
      "address": "Locality and area in {effective_city}",
      "city": "{effective_city}",
      "experience_years": 15,
      "rating": 4.8,
      "rating_reviews": "4.8 ⭐",
      "contact_phone": "+91 80 1234 5678",
      "fees_inr": 1000,
      "availability": "Consultation by Appointment",
      "ai_match_reason": "Clinical rationale linking this specialist to {findings_text}.",
      "booking_url": null,
      "maps_query": "Hospital Name {effective_city}"
    }}
  ]
}}
"""

        try:
            raw_json = self.service.generate_json(
                prompt=prompt,
                system_instruction="You are an expert clinical referral assistant. Output only valid JSON strictly matching the requested schema.",
                temperature=0.2
            )

            if not raw_json:
                logger.warning("[GeminiDoctorRecommender] Empty JSON response received from Gemini.")
                return None

            # Validate JSON
            parsed_data = json.loads(raw_json)
            if not isinstance(parsed_data, dict):
                logger.warning("[GeminiDoctorRecommender] Model output is not a JSON object.")
                return None

            raw_doctors = parsed_data.get("doctors", [])
            if not isinstance(raw_doctors, list):
                raw_doctors = []

            sanitized_doctors = []
            for doc in raw_doctors:
                if not isinstance(doc, dict):
                    continue

                doc_name = str(doc.get("doctor_name", "Medical Specialist")).strip()
                hosp = str(doc.get("hospital", "Accredited Hospital")).strip()
                d_city = str(doc.get("city", effective_city)).strip()
                clean_name = doc_name.replace("Dr.", "").replace("Dr", "").strip()

                # Build Google Maps search link
                maps_query = doc.get("maps_query") or f"{doc_name} {hosp} {d_city}"
                encoded_maps = urllib.parse.quote_plus(str(maps_query))
                maps_url = f"https://www.google.com/maps/search/?api=1&query={encoded_maps}"

                # Build Practo & Google appointment search URLs
                practo_q = urllib.parse.quote_plus(f"{clean_name} {d_city}")
                practo_url = f"https://www.practo.com/search/doctors?results_type=doctor&q={practo_q}"

                booking_url = doc.get("booking_url")
                if not booking_url or not str(booking_url).startswith("http") or "example" in str(booking_url):
                    book_q = urllib.parse.quote_plus(f"book appointment {doc_name} {hosp} {d_city}")
                    booking_url = f"https://www.google.com/search?q={book_q}"

                # Medical safeguards: AI suggestions are NEVER marked as verified database doctors
                sanitized_doc = {
                    "doctor_name": doc_name,
                    "specialization": doc.get("specialization") or target_specialty,
                    "hospital": hosp,
                    "address": doc.get("address") or f"{hosp}, {d_city}",
                    "city": d_city,
                    "experience_years": int(doc.get("experience_years", 12)) if str(doc.get("experience_years", "")).isdigit() else 12,
                    "rating": float(doc.get("rating", 4.8)) if isinstance(doc.get("rating"), (int, float)) else 4.8,
                    "rating_reviews": doc.get("rating_reviews") or f"{doc.get('rating', 4.8)} ⭐",
                    "contact_phone": doc.get("contact_phone") or "Hospital Reception / Front Desk",
                    "fees_inr": int(doc.get("fees_inr", 800)) if str(doc.get("fees_inr", "")).isdigit() else 800,
                    "availability": doc.get("availability") or "By Consultation / Prior Booking",
                    "ai_match_reason": doc.get("ai_match_reason") or f"Recommended specialist for {findings_text}.",
                    "maps_url": maps_url,
                    "practo_url": practo_url,
                    "booking_url": booking_url,
                    "disease_expertise": findings_text,
                    # STRICT MEDICAL SAFEGUARDS
                    "is_real_doctor": False,       # Unverified AI suggestion; not an internally verified doctor
                    "is_registered": False,        # Not verified against internal hospital credentials
                    "verification_status": "AI Referral Suggestion (Unverified - Confirm with Clinic)"
                }
                sanitized_doctors.append(sanitized_doc)

            parsed_data["doctors"] = sanitized_doctors
            parsed_data["recommended_doctors"] = sanitized_doctors
            parsed_data["total_matches"] = len(sanitized_doctors)
            parsed_data["source"] = "Gemini AI Clinical Referral Intelligence"
            parsed_data["disclaimer"] = (
                "AI-generated specialist recommendations are provided for informational triage guidance. "
                "Patients should verify credentials, availability, and consultation terms directly with the healthcare facility."
            )

            return parsed_data

        except Exception as err:
            logger.error(f"[GeminiDoctorRecommender] Error generating doctor recommendations: {err}")
            return None


# Global singleton instance
gemini_doctor_engine = GeminiDoctorRecommender()
