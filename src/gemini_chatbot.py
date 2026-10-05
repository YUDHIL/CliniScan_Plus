"""
CliniScan+ AI Clinical Assistant & Medical Chatbot Engine
Powered by Google Gemini with Clinical Chest Radiology Grounding.
Provides 24/7 intelligent patient triage, finding explanations, specialist navigation,
and diagnostic workflow guidance.
"""

import os
import json
import logging
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are CliniScan AI Clinical Assistant, an intelligent, empathetic, and medically precise medical AI for the CliniScan+ platform.
CliniScan+ is a clinical AI chest radiograph abnormality detection system powered by YOLO11 (trained on VinBigData 100,000+ annotations) and connected to a nationwide network of 2,000+ verified medical specialists across 26 major cities.

Your core clinical responsibilities:
1. Radiograph Finding Interpretation: Explain common thoracic findings clearly (e.g., Cardiomegaly, Atelectasis, Pleural Effusion, Pneumothorax, Consolidation, Infiltration, ILD, Pulmonary Fibrosis, Nodule/Mass, Aortic Enlargement, Calcification).
2. Specialist Guidance: Explain what specialists (Pulmonologists, Cardiologists, Thoracic Surgeons, Radiologists) do and when a patient should consult them.
3. System Navigation: Help users navigate CliniScan+ (how to upload or scan X-rays, adjust confidence thresholds, search the 2,000 doctor directory, book verified appointments, open Google Maps directions to clinics, or download NABL/ISO laboratory reports).
4. Empathy & Precision: Use warm, encouraging, clear language for patients, while maintaining medical rigor.
5. Formatting: Always structure responses with clean Markdown: use **bold** keywords, bullet points, and concise numbered steps where helpful.
6. Safety & Disclaimers: For acute red-flag symptoms (severe crushing chest pain, acute respiratory distress, sudden hemoptysis, severe cyanosis), explicitly advise immediate emergency medical care / ER triage. Always remind users that AI analysis is a supportive tool and clinical evaluation by a licensed physician is essential.

Keep your answers concise, practical, and well-structured.
"""

FALLBACK_RESPONSES = {
    "cardiomegaly": (
        "**Cardiomegaly (Enlarged Heart)** refers to an increased cardiac silhouette on a chest radiograph "
        "(cardiothoracic ratio > 0.50).\n\n"
        "**Key Insights:**\n"
        "- **Common Causes:** Hypertension, cardiomyopathy, coronary artery disease, or heart valve disorders.\n"
        "- **Recommended Specialist:** **Cardiologist / Heart Failure Specialist**.\n"
        "- **Next Diagnostic Step:** Echocardiogram (ECHO) and clinical blood pressure evaluation.\n\n"
        "💡 *You can use the 'Book Specialist' button on your scan result to connect with verified cardiologists in your city.*"
    ),
    "pneumothorax": (
        "⚠️ **Pneumothorax (Collapsed Lung)** is an urgent clinical finding where air enters the pleural cavity between the lung and chest wall.\n\n"
        "- **Clinical Urgency:** **High / Emergency Triage**\n"
        "- **Symptoms to Watch:** Sudden sharp chest pain, shortness of breath, rapid heart rate.\n"
        "- **Recommended Specialist:** **Pulmonologist / Thoracic Surgeon**.\n\n"
        "🚨 *If you are experiencing sudden severe shortness of breath or blue lips, please seek emergency medical care immediately.*"
    ),
    "effusion": (
        "**Pleural Effusion** occurs when excess fluid accumulates in the pleural space surrounding the lungs.\n\n"
        "- **Symptoms:** Breathlessness on exertion, dry cough, or chest tightness.\n"
        "- **Recommended Specialist:** **Pulmonologist / Respiratory Physician**.\n"
        "- **Standard Procedure:** Clinical evaluation, ultrasound confirmation, or diagnostic thoracentesis if indicated."
    ),
    "nodule": (
        "**Pulmonary Nodule / Mass** is a localized round or oval opacity detected within the lung parenchyma.\n\n"
        "- **Recommended Specialist:** **Pulmonary Oncologist / Thoracic Specialist**.\n"
        "- **Standard Follow-Up:** High-resolution contrast CT (HRCT) chest scan and clinical history review.\n"
        "- **Note:** Many small lung nodules are benign (such as prior infection scars or granulomas)."
    ),
    "booking": (
        "**How to Book an Appointment on CliniScan+:**\n\n"
        "1. **After Scanning:** Look at the matched specialists on your scan results card and click **'Book Appointment'**.\n"
        "2. **From Doctor Directory:** Switch to the **2,000 Doctors Directory** tab to filter specialists by city and hospital.\n"
        "3. **Instant Navigation:** Click **'📍 Maps'** on any doctor card to open turn-by-turn Google Maps navigation to their clinic.\n"
        "4. **Direct Confirmation:** You can also call their verified clinic desk or book through their Practo portal."
    ),
    "xray": (
        "**About CliniScan+ YOLO11 AI Scanner:**\n\n"
        "- **Speed:** Sub-250ms real-time inference latency.\n"
        "- **Coverage:** Detects 10 major chest pathologies localized with bounding box heatmaps.\n"
        "- **How to Use:** Go to the **Scanner** tab, upload a standard PA/AP chest radiograph or choose a sample, and click **'Run Live AI Diagnostic Scan'**."
    ),
}


class GeminiClinicalChatbot:
    """
    Intelligent Medical AI Assistant powered by Google Gemini.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "").strip()
        self.client = None
        self._init_client()

    def _init_client(self):
        """Initialize Google GenAI client."""
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not found for chatbot.")
            return

        try:
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.sdk_type = "google-genai"
            logger.info("Chatbot initialized Google GenAI SDK successfully.")
        except Exception as e:
            try:
                import google.generativeai as legacy_genai
                legacy_genai.configure(api_key=self.api_key)
                self.client = legacy_genai
                self.sdk_type = "legacy"
                logger.info("Chatbot initialized legacy google.generativeai SDK.")
            except Exception as ex:
                logger.error(f"Failed initializing chatbot Gemini client: {ex}")
                self.client = None

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10 and self.client is not None)

    def generate_response(
        self,
        message: str,
        history: Optional[List[Dict[str, str]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a conversational clinical AI response given user prompt, history, and active context.
        """
        message_clean = (message or "").strip()
        if not message_clean:
            return "Hello! I am your CliniScan AI Clinical Assistant. How can I assist you with your chest radiograph, symptoms, or finding specialists today?"

        if not self.is_available():
            self._init_client()

        # Build context header if provided
        context_str = ""
        if context:
            user_name = context.get("user_name")
            user_role = context.get("user_role", "Patient")
            user_city = context.get("user_city")
            active_findings = context.get("active_findings")

            ctx_parts = []
            if user_name:
                ctx_parts.append(f"User: {user_name} ({user_role})")
            if user_city:
                ctx_parts.append(f"Location: {user_city}")
            if active_findings:
                ctx_parts.append(f"Current X-ray Findings: {active_findings}")

            if ctx_parts:
                context_str = f"[Active Context: {', '.join(ctx_parts)}]\n\n"

        # If Gemini is available, query the LLM
        if self.is_available():
            try:
                reply = self._call_gemini_chat(message_clean, history or [], context_str)
                if reply and len(reply.strip()) > 5:
                    return reply
            except Exception as err:
                logger.error(f"Gemini chatbot error: {err}")

        # Intelligent Medical Fallback Generator
        return self._generate_fallback(message_clean, context)

    def _call_gemini_chat(
        self,
        message: str,
        history: List[Dict[str, str]],
        context_str: str
    ) -> Optional[str]:
        """Query Gemini using google-genai or legacy SDK."""
        prompt_full = f"{SYSTEM_PROMPT}\n\n{context_str}"

        # Append previous conversation history (up to last 6 turns)
        if history:
            prompt_full += "Conversation History:\n"
            for turn in history[-6:]:
                role_label = "User" if turn.get("role") in ["user", "human"] else "Assistant"
                content = turn.get("content", "").strip()
                if content:
                    prompt_full += f"{role_label}: {content}\n"
            prompt_full += "\n"

        prompt_full += f"User: {message}\nAssistant:"

        if self.sdk_type == "google-genai":
            models_to_try = [
                "gemini-3.5-flash-lite",
                "gemini-3.8-flash",
                "gemini-3.5-flash",
            ]
            for model_id in models_to_try:
                try:
                    response = self.client.models.generate_content(
                        model=model_id,
                        contents=prompt_full,
                    )
                    if response and response.text:
                        return response.text.strip()
                except Exception as ex:
                    logger.debug(f"Chatbot attempt with {model_id} failed: {ex}")
                    continue

        elif self.sdk_type == "legacy":
            for model_id in ["gemini-1.5-flash", "gemini-pro"]:
                try:
                    model = self.client.GenerativeModel(model_id)
                    response = model.generate_content(prompt_full)
                    if response and response.text:
                        return response.text.strip()
                except Exception as ex:
                    logger.debug(f"Legacy chatbot {model_id} failed: {ex}")
                    continue

        return None

    def _generate_fallback(self, message: str, context: Optional[Dict] = None) -> str:
        """Heuristic clinical fallback if live Gemini API is unreachable."""
        m_lower = message.lower()

        for key, text in FALLBACK_RESPONSES.items():
            if key in m_lower:
                return text

        if "hello" in m_lower or "hi" in m_lower or "hey" in m_lower:
            return (
                "👋 **Hello! I'm your CliniScan AI Clinical Assistant.**\n\n"
                "I can assist you with:\n"
                "- 🫁 **Understanding Chest X-ray Findings** (Cardiomegaly, Effusion, Atelectasis, etc.)\n"
                "- 👨‍⚕️ **Finding & Booking Verified Specialists** in your city\n"
                "- 📍 **Google Maps Navigation** to hospitals and clinics\n"
                "- 📑 **Downloading Official NABL/ISO Laboratory Diagnostic Reports**\n\n"
                "How can I help you today?"
            )

        if "doctor" in m_lower or "specialist" in m_lower or "hospital" in m_lower or "clinic" in m_lower:
            return (
                "**Connecting with Verified Specialists:**\n\n"
                "CliniScan+ is integrated with over **2,000 verified doctors** across 10 hospital networks in India.\n\n"
                "- **Search by City & Specialty:** Head over to the **2,000 Doctors Directory** tab.\n"
                "- **Post-Scan Matching:** When you scan an X-ray, our AI automatically matches top specialists tailored to your specific findings.\n"
                "- **Directions & Booking:** Each doctor card includes **'📍 Maps'** for GPS navigation and **'📅 Book Appointment'**."
            )

        if "report" in m_lower or "certificate" in m_lower or "pdf" in m_lower or "download" in m_lower:
            return (
                "**Generating & Downloading Reports:**\n\n"
                "- On any completed scan, click **'Download Official Report'** to generate a complete, printable clinical summary.\n"
                "- The report includes your patient demographics, localized bounding boxes, AI model confidence, triage urgency, and doctor referral notes."
            )

        return (
            "I'm here to support your clinical and diagnostic journey on CliniScan+.\n\n"
            "You can ask me about:\n"
            "- Specific **radiograph findings** (e.g. *'What is Pleural Thickening?'*)\n"
            "- Recommended **specialties & follow-up care**\n"
            "- **Finding top hospitals and doctors** in your area\n"
            "- How to **interpret your AI detection scores**\n\n"
            "Feel free to ask any specific question!"
        )


# Global singleton instance
chatbot_engine = GeminiClinicalChatbot()
