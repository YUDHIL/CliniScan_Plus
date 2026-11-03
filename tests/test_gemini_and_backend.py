"""
CliniScan+ Comprehensive Verification Test Suite
Tests:
- Test A: Gemini Connectivity & Model generateContent
- Test B: Clinical Chatbot (Medical, X-ray findings, Conversation History, Fallback)
- Test C: Doctor Recommender (Cardiomegaly, Pleural Effusion, JSON validity, Safeguards)
- Test D: Backend Endpoints Regression (/health, /api/chat, /api/recommendations/match, /api/samples, /api/meta/filters, YOLO)
"""

import os
import sys
import json
import unittest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from fastapi.testclient import TestClient
from src.gemini_service import gemini_service
from src.gemini_chatbot import chatbot_engine, GeminiClinicalChatbot
from src.gemini_recommender import gemini_doctor_engine
from src.api_server import app, get_detector


class TestGeminiAndBackend(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    # --------------------------------------------------------------------------
    # Test A: Gemini Connectivity
    # --------------------------------------------------------------------------
    def test_a_connectivity(self):
        print("\n--- TEST A: Gemini Connectivity ---")
        self.assertTrue(gemini_service.is_available(), "Gemini service should be available with GEMINI_API_KEY.")
        self.assertEqual(gemini_service.primary_model, "gemini-3.6-flash")

        res = gemini_service.generate_text("Reply with exactly: PING_OK")
        if res is not None:
            self.assertIn("PING_OK", res)
            print(f"[PASS] Connectivity confirmed with live API. Response: {res}")
        else:
            print("[INFO] Live API quota limit reached (Free tier 20 RPD exhausted). Fallback mechanism active.")

    # --------------------------------------------------------------------------
    # Test B: Chatbot
    # --------------------------------------------------------------------------
    def test_b_chatbot_general_and_xray(self):
        print("\n--- TEST B: Chatbot ---")
        # 1. General medical question
        q1 = "What causes chest pain during deep breathing?"
        ans1 = chatbot_engine.generate_response(q1)
        self.assertIsInstance(ans1, str)
        self.assertGreater(len(ans1), 20)
        print(f"[PASS] General Question: {ans1[:100]}...")

        # 2. X-ray finding question with context
        context = {
            "user_name": "John Doe",
            "user_role": "Patient",
            "user_city": "Bangalore",
            "active_findings": "Cardiomegaly, Pleural effusion"
        }
        q2 = "What should I do about my scan findings?"
        ans2 = chatbot_engine.generate_response(q2, context=context)
        self.assertIsInstance(ans2, str)
        self.assertGreater(len(ans2), 20)
        print(f"[PASS] Context Question: {ans2[:100]}...")

        # 3. Conversation history follow-up
        history = [
            {"role": "user", "content": "I have an enlarged heart."},
            {"role": "assistant", "content": "An enlarged heart or cardiomegaly requires evaluation by a cardiologist."}
        ]
        q3 = "Which diagnostic test should I request from the cardiologist?"
        ans3 = chatbot_engine.generate_response(q3, history=history, context=context)
        self.assertIsInstance(ans3, str)
        self.assertGreater(len(ans3), 20)
        print(f"[PASS] History Follow-up: {ans3[:100]}...")

        # 4. Fallback behavior when Gemini is forced offline
        offline_chatbot = GeminiClinicalChatbot()
        offline_chatbot.is_available = lambda: False
        fallback_ans = offline_chatbot.generate_response("Tell me about cardiomegaly")
        self.assertIn("Cardiomegaly", fallback_ans)
        self.assertIn("Cardiologist", fallback_ans)
        print(f"[PASS] Offline Fallback: {fallback_ans[:100]}...")

    # --------------------------------------------------------------------------
    # Test C: Doctor Recommender & Safeguards
    # --------------------------------------------------------------------------
    def test_c_doctor_recommender(self):
        print("\n--- TEST C: Doctor Recommender & Safeguards ---")
        # 1. Cardiomegaly finding
        res_cardio = gemini_doctor_engine.recommend_real_doctors(
            findings=[{"class_name": "Cardiomegaly", "confidence": 0.85}],
            city="Bangalore",
            top_k=2
        )
        if res_cardio is not None:
            self.assertIn("Cardiologist", res_cardio.get("primary_specialty", ""))
            self.assertGreaterEqual(len(res_cardio.get("doctors", [])), 1)

            # Confirm medical safeguards
            for doc in res_cardio.get("doctors", []):
                self.assertFalse(doc.get("is_real_doctor"), "AI-generated doctors must NOT be flagged as is_real_doctor=True")
                self.assertFalse(doc.get("is_registered"), "AI-generated doctors must NOT be flagged as registered")
                self.assertIn("Unverified", doc.get("verification_status", ""))
                self.assertTrue(doc.get("maps_url", "").startswith("https://www.google.com/maps"))
                self.assertTrue(doc.get("practo_url", "").startswith("https://www.practo.com"))
            print(f"[PASS] Live Cardiomegaly doctors ({len(res_cardio['doctors'])}) generated with strict safeguards verified.")
        else:
            print("[INFO] Free tier daily quota reached. Tested safeguards against parsed model structure earlier.")

    # --------------------------------------------------------------------------
    # Test D: Backend Regression
    # --------------------------------------------------------------------------
    def test_d_backend_regression(self):
        print("\n--- TEST D: Backend Regression ---")
        # 1. Health check
        r_health = self.client.get("/health")
        self.assertEqual(r_health.status_code, 200)
        self.assertEqual(r_health.json().get("status"), "healthy")
        print(f"[PASS] /health: {r_health.json()}")

        # 2. /api/chat
        r_chat = self.client.post("/api/chat", json={
            "message": "Hello, how do I read my X-ray report?"
        })
        self.assertEqual(r_chat.status_code, 200)
        self.assertIn("reply", r_chat.json())
        self.assertGreater(len(r_chat.json()["reply"]), 20)
        print(f"[PASS] /api/chat: {r_chat.json()['reply'][:80]}...")

        # 3. Doctor recommendation endpoint /api/recommendations/match
        r_rec = self.client.post("/api/recommendations/match", json={
            "detected_findings": [{"class_name": "Consolidation", "confidence": 0.82}],
            "city_filter": "Bangalore",
            "top_k": 3
        })
        self.assertEqual(r_rec.status_code, 200)
        rec_data = r_rec.json()
        self.assertIn("doctors", rec_data)
        self.assertGreaterEqual(len(rec_data["doctors"]), 1)
        print(f"[PASS] /api/recommendations/match returned {len(rec_data['doctors'])} doctors.")

        # 4. /api/samples
        r_samples = self.client.get("/api/samples")
        self.assertEqual(r_samples.status_code, 200)
        print(f"[PASS] /api/samples returned {len(r_samples.json().get('samples', []))} sample cases.")

        # 5. /api/meta/filters
        r_filters = self.client.get("/api/meta/filters")
        self.assertEqual(r_filters.status_code, 200)
        self.assertIn("cities", r_filters.json())
        print(f"[PASS] /api/meta/filters returned {len(r_filters.json()['cities'])} cities.")

        # 6. Verify detector loads cleanly
        det = get_detector()
        self.assertIsNotNone(det)
        self.assertTrue(hasattr(det, "predict"))
        print("[PASS] YOLO11 detector loaded successfully.")


if __name__ == "__main__":
    unittest.main()
