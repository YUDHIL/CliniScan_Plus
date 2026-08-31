"""
CliniScan+ Hospital-Grade MongoDB & Audit Persistence Layer
Supports Multi-Role User Authentication (Patient, Doctor, Laboratory),
Diagnostic Scans, Appointments, and Doctor Review Workflows.
"""

import os
import json
import uuid
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Union, Tuple
import pymongo

try:
    import mongomock
    HAS_MONGOMOCK = True
except ImportError:
    HAS_MONGOMOCK = False


def hash_password(password: str) -> str:
    """Hash a plaintext password with SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class CliniScanDatabase:
    """
    Unified MongoDB clinical database interface for CliniScan+ Hospital System.
    """

    def __init__(
        self,
        mongo_uri: str = "mongodb://localhost:27017",
        db_name: str = "cliniscan_hospital_db",
        local_backup_path: Optional[str] = None
    ):
        self.db_name = db_name
        if local_backup_path is None:
            self.local_backup_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data",
                "cliniscan_db_backup.json"
            )
        else:
            self.local_backup_path = local_backup_path
        self.is_connected = False
        self.client = None
        self.db = None

        # Attempt MongoDB connection with 1-second timeout
        try:
            client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=1000)
            client.server_info()  # Trigger check
            self.client = client
            self.db = self.client[db_name]
            self.is_connected = True
            self.storage_mode = "MongoDB (Live Service)"
            print(f"[CliniScanDatabase] Connected to live MongoDB: {mongo_uri}/{db_name}")
        except Exception:
            # Fallback to mongomock
            if HAS_MONGOMOCK:
                self.client = mongomock.MongoClient()
                self.db = self.client[db_name]
                self.storage_mode = "MongoDB Engine (In-Memory Fallback)"
                print("[CliniScanDatabase] MongoDB service offline. Initialized Mongomock engine with local JSON backup.")
            else:
                self.storage_mode = "Local JSON Storage"
                print("[CliniScanDatabase] Initialized Local JSON database storage.")

        # Restore persisted state from local backup if available
        self._load_from_local_backup()
        # Seed baseline users and collections if still empty
        self._seed_default_data()

    def _load_from_local_backup(self):
        """Restore users, appointments, and scans from local JSON backup on startup."""
        if os.path.exists(self.local_backup_path) and self.db is not None:
            try:
                with open(self.local_backup_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if "users" in data and data["users"]:
                    for u in data["users"]:
                        if self.db.users.count_documents({"username": u.get("username")}) == 0:
                            self.db.users.insert_one(u)

                if "appointments" in data and data["appointments"]:
                    for a in data["appointments"]:
                        if self.db.appointments.count_documents({"appointment_id": a.get("appointment_id")}) == 0:
                            self.db.appointments.insert_one(a)

                if "scans" in data and data["scans"]:
                    for s in data["scans"]:
                        if self.db.scans.count_documents({"scan_id": s.get("scan_id")}) == 0:
                            self.db.scans.insert_one(s)

                print(f"[CliniScanDatabase] Restored {self.db.appointments.count_documents({})} appointments and {self.db.users.count_documents({})} users from backup.")
            except Exception as e:
                print(f"[CliniScanDatabase] Backup restore warning: {e}")

        # Also check recommender sample JSON for any newly registered doctors and auto-merge
        try:
            recommender_json = os.path.join(os.path.dirname(os.path.dirname(__file__)), "recommender", "doctors_200_sample.json")
            if os.path.exists(recommender_json) and self.db is not None:
                with open(recommender_json, "r", encoding="utf-8") as f:
                    sample_docs = json.load(f)
                new_imported = 0
                for sd in sample_docs:
                    u_name = sd.get("username")
                    if u_name and self.db.users.count_documents({"username": u_name}) == 0:
                        raw_name = sd.get("Doctor_Name", "Dr. Specialist")
                        clean_n = raw_name.replace("Dr. Dr.", "Dr.").strip()
                        self.db.users.insert_one({
                            "user_id": sd.get("user_id", f"DOC-{u_name.upper()}"),
                            "username": u_name,
                            "password_hash": sd.get("password_hash", hash_password(sd.get("password", "Doctor123!"))),
                            "password": sd.get("password", "Doctor123!"),
                            "role": "Doctor",
                            "full_name": clean_n,
                            "email": sd.get("email", f"{u_name}@hospital.med"),
                            "phone": "+91 98111 22334",
                            "city": sd.get("City", "Bangalore"),
                            "specialization": sd.get("Specialization", "General Physician"),
                            "hospital": sd.get("Hospital", "AIIMS"),
                            "experience_years": int(sd.get("Experience", 15)),
                            "fees_inr": int(sd.get("Fees", 800)),
                            "rating": float(sd.get("Rating", 5.0)),
                            "availability": sd.get("Availability", "Available"),
                            "disease_expertise": sd.get("Disease", "General"),
                            "created_at": sd.get("created_at", datetime.now().isoformat())
                        })
                        new_imported += 1
                if new_imported > 0:
                    self._save_to_local_backup()
                    print(f"[CliniScanDatabase] Auto-imported {new_imported} doctors from recommender directory.")
        except Exception as r_err:
            print(f"[CliniScanDatabase] Recommender sync note: {r_err}")

    def _seed_default_data(self):
        """Seed default demo accounts for Patient, Doctor, and Laboratory if empty."""
        if self.db is not None and self.db.users.count_documents({}) == 0:
            demo_users = [
                {
                    "username": "patient_demo",
                    "password_hash": hash_password("patient123"),
                    "role": "Patient",
                    "full_name": "Eleanor Vance",
                    "email": "eleanor.vance@example.com",
                    "phone": "+91 98765 43210",
                    "city": "Bangalore",
                    "age": 58,
                    "gender": "Female",
                    "created_at": datetime.now().isoformat()
                },
                {
                    "username": "doctor_demo",
                    "password_hash": hash_password("doctor123"),
                    "role": "Doctor",
                    "full_name": "Dr. Yukti Chauhan",
                    "email": "dr.yukti@aiims.org",
                    "phone": "+91 98111 22334",
                    "city": "Bangalore",
                    "specialization": "Pulmonologist",
                    "hospital": "AIIMS",
                    "experience_years": 20,
                    "rating": 5.0,
                    "created_at": datetime.now().isoformat()
                },
                {
                    "username": "lab_demo",
                    "password_hash": hash_password("lab123"),
                    "role": "Laboratory",
                    "full_name": "Apex Diagnostic & Radiology Lab",
                    "email": "contact@apexdiagnostic.com",
                    "phone": "+91 99000 11223",
                    "city": "Bangalore",
                    "license_no": "LAB-BLR-2026-981",
                    "created_at": datetime.now().isoformat()
                }
            ]
            self.db.users.insert_many(demo_users)
            print("[CliniScanDatabase] Seeded demo accounts: patient_demo, doctor_demo, lab_demo")

    # ==========================================================================
    # USER AUTHENTICATION & MANAGEMENT
    # ==========================================================================
    def register_user(
        self,
        username: str,
        password: str,
        role: str,
        full_name: str,
        email: str,
        phone: str,
        city: str,
        extra_data: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """
        Register a new user account (Patient, Doctor, or Laboratory).
        """
        username = username.strip().lower()
        if not username or not password:
            return False, "Username and password cannot be empty."

        if self.db is not None:
            existing = self.db.users.find_one({"username": username})
            if existing:
                return False, f"Username '{username}' already exists. Please choose another."

            user_doc = {
                "user_id": f"USR-{uuid.uuid4().hex[:8].upper()}",
                "username": username,
                "password_hash": hash_password(password),
                "role": role,
                "full_name": full_name.strip(),
                "email": email.strip(),
                "phone": phone.strip(),
                "city": city.strip(),
                "created_at": datetime.now().isoformat()
            }
            if extra_data:
                user_doc.update(extra_data)

            self.db.users.insert_one(user_doc)
            self._save_to_local_backup()

            # If a Doctor is registered, automatically sync to all recommendation datasets & files
            if role == "Doctor":
                try:
                    d_name = full_name.strip()
                    if not d_name.startswith("Dr. "):
                        d_name = f"Dr. {d_name}"
                    d_spec = (extra_data or {}).get("specialization", "General Physician")
                    d_exp = (extra_data or {}).get("experience_years", 15)
                    d_rating = (extra_data or {}).get("rating", 5.0)
                    d_hosp = (extra_data or {}).get("hospital", "AIIMS")
                    d_fee = (extra_data or {}).get("fees_inr", 800)
                    d_avail = (extra_data or {}).get("availability", "Available")
                    d_disease = (extra_data or {}).get("disease_expertise") or d_spec

                    # Try importing recommender sync helper
                    try:
                        from recommender.sample_and_populate_mongodb import add_doctor_to_all_datasets
                        add_doctor_to_all_datasets({
                            "Doctor_Name": d_name,
                            "Specialization": d_spec,
                            "Disease": d_disease,
                            "Hospital": d_hosp,
                            "City": city.strip(),
                            "Experience": d_exp,
                            "Rating": d_rating,
                            "Fees": d_fee,
                            "Availability": d_avail,
                            "username": username,
                            "email": email.strip(),
                            "password": password,
                            "user_id": user_doc["user_id"]
                        })
                    except Exception as sync_err:
                        print(f"[CliniScanDatabase] Recommender package sync fallback: {sync_err}")
                        # Fallback direct append to root CSV
                        csv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "doctor_2000_realnames.csv")
                        if os.path.exists(csv_path):
                            new_line = f"\n{d_name},{d_disease},{d_spec},{d_exp},{d_rating},{d_hosp},{city.strip()},{d_fee},{d_avail}"
                            with open(csv_path, "a", encoding="utf-8") as f:
                                f.write(new_line)

                    # Trigger dynamic recommendation engine reload if loaded
                    try:
                        from src.recommendation import doctor_engine
                        doctor_engine.reload()
                        print(f"[CliniScanDatabase] Reloaded recommendation engine with newly registered doctor: {d_name}")
                    except Exception:
                        pass

                except Exception as err:
                    print(f"[CliniScanDatabase] Doctor CSV sync warning: {err}")

            return True, "Account created successfully! You can now sign in."
        return False, "Database unavailable."

    def authenticate_user(self, username: str, password: str, role: Optional[str] = None) -> Optional[Dict]:
        """
        Authenticate user credentials and role.
        """
        username = username.strip().lower()
        p_hash = hash_password(password)

        if self.db is not None:
            query = {"username": username, "password_hash": p_hash}
            if role:
                query["role"] = role
            user = self.db.users.find_one(query, {"_id": 0, "password_hash": 0})
            return user
        return None

    def get_user(self, username: str) -> Optional[Dict]:
        """Fetch user profile by username."""
        if self.db is not None:
            return self.db.users.find_one({"username": username.strip().lower()}, {"_id": 0, "password_hash": 0})
        return None

    def update_user_profile(
        self,
        username: str,
        updates: Dict,
        new_password: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Update personal info, contact details, role preferences, and credentials for an account holder.
        """
        username = username.strip().lower()
        if not username:
            return False, "Invalid username.", None

        if self.db is not None:
            existing = self.db.users.find_one({"username": username})
            if not existing:
                return False, f"User '{username}' not found.", None

            clean_updates = dict(updates)
            # Handle password update if provided
            if new_password and new_password.strip():
                clean_updates["password_hash"] = hash_password(new_password.strip())
                clean_updates["password"] = new_password.strip()

            clean_updates["updated_at"] = datetime.now().isoformat()

            self.db.users.update_one({"username": username}, {"$set": clean_updates})
            self._save_to_local_backup()

            updated_user = self.get_user(username)

            # If user is a Doctor, propagate changes to recommendation dataset
            if existing.get("role") == "Doctor" or clean_updates.get("role") == "Doctor":
                try:
                    d_name = clean_updates.get("full_name") or existing.get("full_name") or "Dr. Specialist"
                    if not d_name.startswith("Dr. "):
                        d_name = f"Dr. {d_name}"
                    d_spec = clean_updates.get("specialization") or existing.get("specialization") or "General Physician"
                    d_exp = clean_updates.get("experience_years") or existing.get("experience_years") or 15
                    d_hosp = clean_updates.get("hospital") or existing.get("hospital") or "AIIMS"
                    d_city = clean_updates.get("city") or existing.get("city") or "Bangalore"
                    d_fee = clean_updates.get("fees_inr") or existing.get("fees_inr") or 800
                    d_avail = clean_updates.get("availability") or existing.get("availability") or "Available"
                    d_disease = clean_updates.get("disease_expertise") or existing.get("disease_expertise") or d_spec

                    try:
                        from recommender.sample_and_populate_mongodb import add_doctor_to_all_datasets
                        add_doctor_to_all_datasets({
                            "Doctor_Name": d_name,
                            "Specialization": d_spec,
                            "Disease": d_disease,
                            "Hospital": d_hosp,
                            "City": d_city,
                            "Experience": int(d_exp),
                            "Fees": int(d_fee),
                            "Availability": d_avail,
                            "username": username,
                            "email": clean_updates.get("email") or existing.get("email", ""),
                            "password": new_password.strip() if (new_password and new_password.strip()) else existing.get("password", "Doctor123!"),
                            "user_id": existing.get("user_id")
                        })
                    except Exception as s_err:
                        print(f"[CliniScanDatabase] Sync doctor update error: {s_err}")

                    try:
                        from src.recommendation import doctor_engine
                        doctor_engine.reload()
                    except Exception:
                        pass
                except Exception as ex:
                    print(f"[CliniScanDatabase] Doctor update propagation warning: {ex}")

            return True, "Profile updated successfully!", updated_user
        return False, "Database unavailable.", None

    # ==========================================================================
    # APPOINTMENTS & DOCTOR CONFIRMATION WORKFLOW
    # ==========================================================================
    def create_appointment(self, appointment_dict: Dict) -> str:
        """
        Create a new patient appointment request with 'Pending' status.
        """
        if "appointment_id" not in appointment_dict:
            appointment_dict["appointment_id"] = f"APT-{int(datetime.now().timestamp()*1000)%1000000:06d}"
        
        appointment_dict["status"] = appointment_dict.get("status", "Pending")
        appointment_dict["created_at"] = datetime.now().isoformat()
        appointment_dict["doctor_confirmed_at"] = None
        appointment_dict["doctor_notes"] = ""

        if self.db is not None:
            self.db.appointments.insert_one(appointment_dict)
            self._save_to_local_backup()
            return appointment_dict["appointment_id"]
        return ""

    def get_patient_appointments(self, patient_username: str) -> List[Dict]:
        """Fetch all appointments booked by a specific patient."""
        if self.db is not None:
            return list(self.db.appointments.find({"patient_username": patient_username}, {"_id": 0}).sort("created_at", -1))
        return []

    def get_all_appointments(self, limit: int = 100) -> List[Dict]:
        """Fetch all hospital appointments sorted by most recent."""
        if self.db is not None:
            return list(self.db.appointments.find({}, {"_id": 0}).sort("created_at", -1).limit(limit))
        return []

    def get_doctor_appointments(self, doctor_name: Optional[str] = None, specialization: Optional[str] = None) -> List[Dict]:
        """
        Fetch appointment requests routed to a doctor or hospital specialty.
        If doctor_name is None or 'All', returns all hospital appointments.
        """
        if self.db is not None:
            if not doctor_name or doctor_name == "All" or doctor_name == "All Doctors":
                return self.get_all_appointments()
            
            clean_name = doctor_name.replace("Dr. ", "").strip()
            query = {
                "$or": [
                    {"doctor_name": doctor_name},
                    {"doctor_name": {"$regex": clean_name, "$options": "i"}},
                    {"confirming_doctor": doctor_name}
                ]
            }
            if specialization:
                query["$or"].append({"specialization": specialization})

            return list(self.db.appointments.find(query, {"_id": 0}).sort("created_at", -1))
        return []

    def confirm_appointment(self, appointment_id: str, doctor_name: str, doctor_notes: str = "", status: str = "Confirmed") -> bool:
        """
        Doctor confirms or updates an appointment request.
        """
        if self.db is not None:
            res = self.db.appointments.update_one(
                {"appointment_id": appointment_id},
                {
                    "$set": {
                        "status": status,
                        "doctor_confirmed_at": datetime.now().isoformat(),
                        "confirming_doctor": doctor_name,
                        "doctor_notes": doctor_notes
                    }
                }
            )
            self._save_to_local_backup()
            return res.modified_count > 0
        return False

    # ==========================================================================
    # DIAGNOSTIC SCANS & LABORATORY RECORDS
    # ==========================================================================
    def save_scan_record(self, scan_dict: Dict) -> str:
        """
        Save a patient radiograph scan record with AI detections.
        """
        if "scan_id" not in scan_dict:
            scan_dict["scan_id"] = f"SCN-{int(datetime.now().timestamp()*1000)%1000000:06d}"
        scan_dict["timestamp"] = datetime.now().isoformat()

        if self.db is not None:
            self.db.scans.insert_one(scan_dict)
            self._save_to_local_backup()
            return scan_dict["scan_id"]
        return ""

    def get_user_scans(self, username: str, limit: int = 50) -> List[Dict]:
        """Retrieve diagnostic scans for a user (patient or lab)."""
        if self.db is not None:
            return list(self.db.scans.find({"username": username}, {"_id": 0}).sort("timestamp", -1).limit(limit))
        return []

    def get_all_scans(self, limit: int = 100) -> List[Dict]:
        """Retrieve all diagnostic scans across the hospital platform."""
        if self.db is not None:
            return list(self.db.scans.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit))
        return []

    # ==========================================================================
    # PERSISTENCE & LOCAL BACKUP
    # ==========================================================================
    def _save_to_local_backup(self):
        """Persist current state to local JSON file for durability."""
        if self.db is not None:
            try:
                os.makedirs(os.path.dirname(self.local_backup_path), exist_ok=True)
                data = {
                    "users": list(self.db.users.find({}, {"_id": 0})),
                    "appointments": list(self.db.appointments.find({}, {"_id": 0})),
                    "scans": list(self.db.scans.find({}, {"_id": 0}))
                }
                with open(self.local_backup_path, "w") as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                print(f"[CliniScanDatabase] Backup warning: {e}")


# Singleton instance
db_instance = CliniScanDatabase()


if __name__ == "__main__":
    # Self-test database functions
    print("\n--- DATABASE SELF TEST ---")
    print(f"Storage Mode: {db_instance.storage_mode}")
    auth = db_instance.authenticate_user("patient_demo", "patient123")
    print(f"Auth test (patient_demo): {'Success' if auth else 'Failed'}")
    apt_id = db_instance.create_appointment({
        "patient_username": "patient_demo",
        "patient_name": "Eleanor Vance",
        "doctor_name": "Dr. Sarah Johnson",
        "hospital": "AIIMS",
        "city": "Bangalore",
        "finding": "Pulmonary fibrosis",
        "slot": "Tomorrow 10:00 AM"
    })
    print(f"Created Appointment ID: {apt_id}")
    confirmed = db_instance.confirm_appointment(apt_id, "Dr. Sarah Johnson", "Proceed with High-Resolution CT.")
    print(f"Doctor Confirmation: {'Success' if confirmed else 'Failed'}")
